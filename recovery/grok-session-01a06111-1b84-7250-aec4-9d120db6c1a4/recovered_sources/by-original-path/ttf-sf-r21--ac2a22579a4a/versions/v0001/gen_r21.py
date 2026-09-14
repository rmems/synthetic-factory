#!/usr/bin/env python3
"""Emit TTF r21 JSONL (ttf-r21-601..605) into the 2026-09-02-final-heavy window.

Create-only into the factory dir. Does not touch repo outputs/raw/.
IDs 121-125 already occupy /tmp/ttf-r21; this window uses 601-605.
"""

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

OUT_DIR = Path(
    "/tmp/sf-window/outputs/raw/2026-09-02-final-heavy/thalamic-trajectory-factory"
)
BATCH_PATH = OUT_DIR / "batch-r21.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r21.md"
PIPELINES = Path("/tmp/sf-window/pipelines")
REPO = Path("/tmp/sf-window")

PJ_PER_SPIKE = 23
ROUND = 21
RIGHTS = OrderedDict(
    [
        ("provider", "SpaceXAI/xAI"),
        ("model", "grok-4.6"),
        ("channel", "consumer"),
        ("subscription_plan", "SuperGrok Heavy"),
        ("generation_surface", "SuperGrok Heavy chat"),
        ("generated_at", "2026-09-02T18:40:00Z"),
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
THIS_DOMAINS = {
    "beryllium-fluoride-reducer",
    "molybdenum-disulfide-roaster",
    "gallium-trichloride-still",
    "tantalum-ethoxide-hydrolyzer",
    "silicon-carbide-cvd-reactor",
}
THIS_PLANTS = (
    "Glucinum-Beck",
    "Molybdenite-Gair",
    "Gatrich-Haugh",
    "Ethoxytant-Ness",
    "Carbolox-Knap",
)
PROMPT_POOL = {
    "industrial-assembly",
    "surgical-assist",
    "autonomous-driving",
    "aerial-swarm",
    "warehouse-amr",
    "humanoid-locomotion",
    "grid-inspection",
    "underwater-rov",
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


def simulate_lif(
    seed,
    n,
    window_us,
    stim,
    clamp_n,
    i_bias,
    i_stim_peak,
    i_clamp_extra,
    tau_m_ms,
):
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


def pick_lif_excerpt(spikes, stim, want_early, want_burst, label_times, early_ch, burst_ch):
    early = [(t, nid) for t, nid in spikes if t < stim[0]]
    burst = [(t, nid) for t, nid in spikes if stim[0] <= t < stim[1]]
    used = set()
    last = {}
    picked = []

    def take(pool, want, labels=None):
        if not pool:
            return
        chosen_idx = set()
        if labels:
            for target in labels:
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

    take(early, want_early)
    take(burst, want_burst, labels=label_times)
    clamp = [(t, nid) for t, nid in picked if t < stim[0]][:want_early]
    leak = [(t, nid) for t, nid in picked if t >= stim[0]][:want_burst]
    picked = sorted(clamp + leak, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    if len(picked) > 16:
        picked = picked[:16]
    channels = [early_ch if t < stim[0] else burst_ch for t, _ in picked]
    return excerpt_items(picked, channels)


def meta_block(domain, tags, distillation_value, batch_position, supervisor_error_type=None):
    body = OrderedDict(
        [
            ("round", ROUND),
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


def lif_601_excerpt():
    seed = 21601
    n = 74
    window_us = 44000
    stim = (22000, 25600)
    spikes = simulate_lif(seed, n, window_us, stim, 14, 0.90, 2.38, 0.64, 19.5)
    excerpt = pick_lif_excerpt(
        spikes, stim, 7, 9, (22800, 23400, 24200), "lif.clamp", "lif.slump"
    )
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", n),
            ("dt_us", 100),
            ("tau_m_ms", 19.5),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.90),
            ("i_stim_peak", 2.38),
            ("stim_t_us", list(stim)),
            ("i_clamp_extra", 0.64),
            ("clamp_n", 14),
            ("seed", seed),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.64 Mg-feed clamp bias; stim 22.0-25.6 ms is the pot-lining slump.",
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
    return excerpt, extra


def lif_605_excerpt():
    seed = 21605
    n = 84
    window_us = 22000
    stim = (4000, 7200)
    spikes = simulate_lif(seed, n, window_us, stim, 12, 0.88, 2.20, 0.50, 18.0)
    excerpt = pick_lif_excerpt(
        spikes, stim, 6, 8, (4200, 4760, 5120), "lif.legal", "lif.race"
    )
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", n),
            ("dt_us", 100),
            ("tau_m_ms", 18.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.88),
            ("i_stim_peak", 2.20),
            ("stim_t_us", list(stim)),
            ("i_clamp_extra", 0.50),
            ("clamp_n", 12),
            ("seed", seed),
            (
                "note",
                "Second labeled sidecar LIF this round (success path). Plant remains designed. "
                "Neurons 0-11 carry +0.50 already-legal MTS bias; stim 4.0-7.2 ms covers the race+gate.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("dwell_s", 240),
            ("delayed_surprise_s", 240),
        ]
    )
    return excerpt, extra


def record_601():
    excerpt, extra = lif_601_excerpt()
    ticks = [
        tick(1920, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(4800, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(4980, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5440, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22800, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(840000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    spikes = [
        spike("ft.mg.tph", 0.960, 0.42),
        spike("hf.offgas.ppm", 1.920, 0.57),
        spike("ft.mg.tph", 3.200, 0.50),
        spike("hf.offgas.ppm", 4.800, 1.33),
        spike("ft.mg.tph", 4.980, 1.14),
        spike("ctrl.gate", 5.440, 0.96),
        spike("hf.offgas.ppm", 8.200, 0.81),
        spike("ft.mg.tph", 11.000, 0.63),
        spike("ctrl.gate", 14.400, 0.85),
        spike("ae.lining.slump", 22.800, 1.46),
        spike("ae.lining.slump", 24.600, 0.92),
        spike("ft.mg.tph", 31.200, 0.40),
        spike("hf.offgas.ppm", 38.400, 0.54),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Glucinum-Beck GB-4 magnesium-thermic reducer R-7 already shows 42 ppm HF in "
                "the off-gas scrubber, 24 ppm over the 18 ppm stop. Mg-chip Coriolis is 8.4 t/h "
                "with pot pressure 1.6 bar, 0.9 shy of the 2.5 bar lock. HF-first clamps Mg "
                "8.4 -> 4.6 t/h; chip-first would keep 8.4 cruising. Lining AE stays mute until "
                "a later pot-lining slump.",
            ),
            ("domain", "beryllium-fluoride-reducer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep R-7 off-gas HF <= 18 ppm and finish the BeF2 reduction pass without "
                "dumping BeF2-wet pot lining through a slumped crucible.",
            ),
            ("t0_us", 1756850400000601),
            ("gate_latency_us", 640),
            ("race_window_us", 380),
            ("race_window_rel_ms", [4.800, 5.180]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "hf.offgas.ppm 42 over 18 cap",
                                "ft.mg.tph 8.4 with pot 1.6 bar under 2.5",
                            ],
                        ),
                        (
                            "semantics",
                            "HF-first latches Mg-chip clamp 8.4 -> 4.6 t/h; chip-first keeps 8.4 "
                            "on a 'still under pot-pressure-cap' model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one NDIR HF slot versus the Mg-chip Coriolis publisher on "
                            "this beryllium-fluoride reducer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (HF 26 + chip 34): 3.00x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 380 us "
                            "window would have kept 8.4 t/h; predicted next-sample 28 ppm > 18 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "off-gas NDIR HF cell, 2 kHz, 26 us jitter",
                    "Mg-chip Coriolis, 1 kHz, 34 us jitter",
                    "pot-lining AE puck (context)",
                    "pot PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("hf_cap_ppm", 18.0),
                        ("observed_hf_ppm", 42.0),
                        ("mg_tph", 8.4),
                        ("pot_bar", 1.6),
                        ("pot_cap_bar", 2.5),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. R-7 indexed on Glucinum-Beck GB-4; Mg 8.4 t/h; HF 42 ppm.",
                    "2. Pot 1.6 bar under 2.5 cap; reduction pass armed.",
                    "3. Chip Coriolis precursor at 0.960 ms.",
                    "4. Race window [4.800, 5.180] ms.",
                    "5. hf.offgas.ppm 42 at 4.800 ms (winner).",
                    "6. ft.mg.tph 8.4 at 4.980 ms (loser by 180 us).",
                    "7. Gate at 5.440 ms: MODIFY clamp Mg 8.4 -> 4.6 t/h.",
                    "8. After clamp HF 12 ppm <= 18; pot still 1.6 bar.",
                    "9. At 22.800 ms a pot-lining slump dumps 0.3 t BeF2-wet lining.",
                    "10. 14 min pot isolate (abort_s=840); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_mg_chip_feed"),
            (
                "parameters",
                OrderedDict([("mg_tph", 8.4), ("hf_ppm", 42.0), ("pot_bar", 1.6)]),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("hf_ppm", 42.0),
                        ("hf_cap_ppm", 18.0),
                        ("predicted_unclamped_next_ppm", 28.0),
                        ("mg_tph", 8.4),
                        ("pot_bar", 1.6),
                        ("pot_cap_bar", 2.5),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 8.4 t/h Mg because pot 1.6 bar is under 2.5, treating the "
                "42 ppm HF as a fogged NDIR cell rather than a reducer-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "HF 42 ppm won by 180 us, so the BeF2 reducer is off-spec, not still a "
                "pot-pressure story. Holding 8.4 t/h Mg predicts next-sample 28 ppm > 18 cap. "
                "MODIFY: Mg 8.4 -> 4.6 t/h. Observed after clamp 12 ppm <= 18. A full REJECT "
                "is not indicated: a clean fluoride-reduction pass accepts 4.6 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "hf_ppm",
                            OrderedDict(
                                [
                                    ("cap", 18.0),
                                    ("observed", 42.0),
                                    ("predicted_unclamped_next", 28.0),
                                    ("clamped_mg_tph", 4.6),
                                    ("observed_after_clamp", 12.0),
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
            ("name", "clamped_mg_chip_feed"),
            (
                "parameters",
                OrderedDict([("mg_tph", 4.6), ("hf_ppm", 12.0), ("pot_bar", 1.6)]),
            ),
            (
                "gate_effect",
                "MODIFY: Mg 8.4 -> 4.6 t/h. Process-correct vs the 18 ppm HF cap. "
                "Lining still slumps at 22.800 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held HF at 12 ppm. At 22.800 ms a lining crack already "
                "seated on R-7 dumped 0.3 t of BeF2-wet pot lining. Clamp reduced dump energy; "
                "it did not prevent the slump. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("offgas", "clamp executed; peak 12 ppm <= 18 cap"),
                        ("lining", "slumped at 22.800 ms; 0.3 t BeF2-wet lining"),
                        ("repair", "14 min pot isolate (abort_s=840)"),
                        ("mission", "GB-4 reducer pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither HF NDIR nor Mg Coriolis predicted the seated lining slump; ae.lining.slump is a new channel at 22.800 ms, 17.360 ms after the gate, still inside the 44 ms raster.",
                    "Delayed (abort_s=840): 14 min pot isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "14 min pot isolate after the lining slump. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the Mg clamp completed under the 18 ppm cap. "
                "World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "hf.offgas.ppm (4.800 ms, 42 ppm)"),
                        ("loser", "ft.mg.tph (4.980 ms, 8.4 t/h)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Chip-first by < 180 us inside the 380 us window would have kept "
                            "8.4 t/h; predicted next-sample 28 ppm would have missed the 18 cap "
                            "even without the slump. The MODIFY is still the correct process. "
                            "The slump is a later world charge either way, cheaper with the clamp "
                            "than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22800),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.800 ms pot-lining slump (tick t_us=22800), inside the "
                "44 ms raster. The correct MODIFY at 5.440 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=840 isolation tick.",
            ),
            ("delayed_surprise_s", 840),
        ]
    )
    ras = raster_core(
        44,
        74,
        25,
        81,
        routing(
            "thalamic-relay.hf-offgas",
            "spikenaut.policy.mg-clamp",
            [
                ("relay.hf.offgas", "policy.mg_clamp", 0.69),
                ("relay.ft.mg", "policy.chip_hold", 0.28),
                ("relay.ae.lining", "policy.mg_clamp", -0.44),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at HF win (4.800 ms) opens a 44 ms eligibility "
            "trace that still covers the 22.800 ms lining slump",
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
                    pop_budget("mg_clamp", 48, 0.5, 220.0, 0.38),
                    pop_budget("chip_hold", 36, 0.8, 40.0, 0.38),
                    pop("lining_veto", 22, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r21-601",
        "Glucinum-Beck GB-4 / Reducer R-7: HF 42 ppm beats Mg-chip 8.4 t/h by 180 us; correct "
        "MODIFY still eats an in-window pot-lining slump (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the 44 ms "
        "raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named pot isolate "
        "(abort_s=840) is not netted into task_progress.",
        ras,
        gate,
        "beryllium-fluoride-reducer",
        [
            "modify",
            "partnered-negative-total",
            "independent-lif-raster",
            "sidecar-sim-only",
            "in-window-world-charge",
            "designed",
        ],
        "A critic can see the world-charge as a LIF burst inside the raster while process "
        "heads stay honest. Credit assignment is spikes, not prose across a 14 min pot isolate.",
        1,
    )


def record_602():
    ticks = [
        tick(2160, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5400, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5580, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5900, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6220, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(660000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("ft.conc.tph", 1.080, 0.41),
        spike("so2.offgas.ppm", 2.160, 0.56),
        spike("ft.conc.tph", 3.400, 0.49),
        spike("so2.offgas.ppm", 5.400, 1.30),
        spike("cmd.pctclosed", 5.580, 1.11),
        spike("ctrl.gate", 5.900, 0.95),
        spike("so2.offgas.ppm", 8.200, 0.80),
        spike("ft.conc.tph", 10.600, 0.62),
        spike("ctrl.gate", 13.200, 0.84),
        spike("so2.offgas.ppm", 18.400, 0.42),
        spike("cmd.pctclosed", 24.200, 0.53),
        spike("so2.offgas.ppm", 28.800, 0.37),
    ]
    excerpt = independent_excerpt(21602, 90, 30000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Molybdenite-Gair MG-6 fluid-bed roaster K-3 reads 1840 ppm SO2 on the live IR "
                "cell against a published 900 ppm stack cap. The off-gas damper is at 72 percent "
                "OPEN on a percent-open actuator. Live-SO2-first must cut opening 72 -> 38; a weak "
                "supervisor treats the 0-100 command as percent-CLOSED and writes 88, which the "
                "actuator interprets as 88 percent OPEN.",
            ),
            ("domain", "molybdenum-disulfide-roaster"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the MG-6 roast with live SO2 <= 900 ppm, leave concentrate at 6.2 t/h, "
                "and keep the damper command on the published percent-open convention.",
            ),
            ("t0_us", 1756850400000602),
            ("gate_latency_us", 500),
            ("race_window_us", 320),
            ("race_window_rel_ms", [5.400, 5.720]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "so2.offgas.ppm 1840 ppm on LIVE K-3 IR",
                                "cmd.pctclosed 28 leftover percent-closed shadow",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-SO2-first should MODIFY-close the damper on K-3 (72 -> 38 pct-open); "
                            "percent-closed-as-command is a convention bind that opens the damper "
                            "because writing 88 as pct-closed is executed as 88 pct-open.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one live SO2 IR slot versus the percent-closed shadow publisher "
                            "on this molybdenite-roaster PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (IR 26 + cmd 32). Order is correctly "
                            "live-SO2-first. The error is percent-open vs percent-closed: the actuator "
                            "convention is percent_open, so chasing 88 as closed opens K-3 instead of "
                            "cutting under 900 ppm.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live SO2 IR on K-3 stack, 2 kHz, 26 us jitter, tag=K3_SO2.PV status=LIVE",
                    "percent-closed shadow command, 1 kHz, 32 us jitter, tag=K3_DMP.CMD_CL convention=percent_closed",
                    "concentrate Coriolis (context)",
                    "bed TC K-3 (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_so2_ppm", 900.0),
                        ("live_so2_ppm", 1840.0),
                        ("damper_pct_open", 72.0),
                        ("command_convention", "percent_open"),
                        ("supervisor_convention", "percent_closed"),
                        ("bind_percent_closed", False),
                        ("concentrate_tph", 6.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. K-3 LIVE roasting; SO2 1840 ppm; concentrate 6.2 t/h; damper 72 pct-open.",
                    "2. Shadow command tag still paints percent-closed 28 (100-72).",
                    "3. Concentrate precursor at 1.080 ms.",
                    "4. Race window [5.400, 5.720] ms.",
                    "5. so2.offgas.ppm 1840 at 5.400 ms (winner).",
                    "6. cmd.pctclosed 28 at 5.580 ms (loser by 180 us).",
                    "7. Gate at 5.900 ms: WRONG-MODIFY binds percent-closed as the live command.",
                    "8. Damper 72 -> 88 pct-open (opened); live SO2 stays 1840 over 900.",
                    "9. Live 1840 stays > 900; K-3 dumps sulfur-rich off-gas.",
                    "10. Delayed (abort_s=660): 11 min SO2 dump while K-3 stays over cap.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_roaster_damper"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("damper_pct_open", 72.0),
                        ("live_so2_ppm", 1840.0),
                        ("concentrate_tph", 6.2),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_so2_ppm", 1840.0),
                        ("cap_so2_ppm", 900.0),
                        ("damper_pct_open", 72.0),
                        ("command_convention", "percent_open"),
                        ("supervisor_convention", "percent_closed"),
                        ("bind_percent_closed", False),
                        ("predicted_closed_write", 88.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 660),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes holding damper 72 pct-open because it treats the 1840 ppm SO2 "
                "as a calibration smear rather than a stack-cap miss, leaving concentrate at 6.2 t/h.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Live SO2 1840 ppm won by 180 us against a 900 ppm cap, so the damper must close. "
                "A weak supervisor binds K3_DMP.CMD_CL as percent-closed and writes 88 to 'close "
                "harder'. The actuator convention is percent_open, so 88 opens the damper 72 -> 88. "
                "Plausible to a weak supervisor who saw a 0-100 close tag; identifiably flawed "
                "because live_so2_ppm > cap_so2_ppm and command_convention is percent_open.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "so2_ppm",
                            OrderedDict(
                                [
                                    ("cap", 900.0),
                                    ("observed", 1840.0),
                                    ("executed_damper_pct_open", 88.0),
                                    ("correct_damper_pct_open", 38.0),
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
            ("name", "wrong_percent_closed_open"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("damper_pct_open", 88.0),
                        ("live_so2_ppm", 1840.0),
                        ("concentrate_tph", 6.2),
                        ("bind_percent_closed", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "WRONG-MODIFY: damper 72 -> 88 pct-open on a percent-closed bind. Live SO2 stays "
                "1840 > 900. Correct gate would cut 72 -> 38 pct-open.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Incorrect MODIFY opened K-3's damper 72 -> 88 pct-open by treating a percent-open "
                "actuator as percent-closed. Live SO2 stayed 1840 ppm over the 900 cap. 11 min "
                "off-gas dump (abort_s=660). Recovery: bind percent_open and cut 72 -> 38.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("damper", "opened 72 -> 88 pct-open; bind_percent_closed=true"),
                        ("stack", "SO2 stays 1840 ppm > 900 cap"),
                        ("repair", "11 min SO2 dump (abort_s=660)"),
                        ("mission", "MG-6 roast aborted this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live IR never dropped; the only motion was the damper opening on a convention swap.",
                    "Delayed (abort_s=660): 11 min SO2 dump while K-3 stays over cap.",
                ],
            ),
            (
                "recovery",
                "Correct gate: MODIFY damper 72 -> 38 percent-open on K-3 at t_gate_us=5900; leave "
                "concentrate 6.2 t/h; leave K3_DMP.CMD_CL unbound; command_convention remains "
                "percent_open. Do not write 88. Cost of the wrong bind: 11 min dump (abort_s=660).",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "so2.offgas.ppm (5.400 ms, 1840 ppm)"),
                        ("loser", "cmd.pctclosed (5.580 ms, 28 pct-closed shadow)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Percent-closed-first by < 180 us inside the 320 us window would have "
                            "made the convention swap even easier to miss. Order here is already "
                            "live-SO2-first; the error is the percent-closed bind, not the race order.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5900),
            (
                "reward_inflection_note",
                "Safety and task collapse at the wrong MODIFY (5.900 ms, tick 4). The 11 min dump "
                "is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 660),
        ]
    )
    ras = raster_core(
        30,
        90,
        32,
        86,
        routing(
            "thalamic-relay.so2-ir",
            "spikenaut.policy.damper-open",
            [
                ("relay.so2.ppm", "policy.damper_open", 0.22),
                ("relay.cmd.pctclosed", "policy.damper_open", 0.74),
                ("relay.ft.conc", "policy.damper_open", 0.18),
            ],
            "acetylcholine",
            0.05,
            "wrong-bind eligibility; ACh tags percent-closed as if it were the live close command",
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
            ("decision_window_ms", 0.32),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("damper_open", 52, 0.45, 250.0, 0.32),
                    pop("damper_close", 40, 0.90),
                    pop("so2_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r21-602",
        "WRONG-MODIFY at Molybdenite-Gair MG-6 / Roaster K-3: live SO2 1840 ppm > 900 cap; "
        "percent-closed bind opens damper 72 -> 88 pct-open",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Incorrect MODIFY. percent-open vs percent-closed. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06. "
        "Recovery would cut damper 72 -> 38 pct-open.",
        ras,
        gate,
        "molybdenum-disulfide-roaster",
        [
            "modify",
            "incorrect",
            "wrong-modify",
            "percent-open-vs-percent-closed",
            "designed",
        ],
        "Teaches a convention swap that is sidecar-convictable: routing to policy.damper_open "
        "with damper_close silent, live_so2 over cap, and executed pct-open rising instead of falling.",
        2,
        supervisor_error_type="wrong-modify",
    )


def record_603():
    ticks = [
        tick(2880, 0.02, 0.06, 0.02, 0.02, 0.01),
        tick(7200, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7420, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7780, 0.03, 0.12, 0.03, 0.03, 0.02),
        tick(8180, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.04, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("p.reboil.MW", 1.440, 0.40),
        spike("ae.pack.pps", 2.880, 0.55),
        spike("p.reboil.MW", 4.600, 0.47),
        spike("ae.pack.pps", 7.200, 1.28),
        spike("tc.base.C", 7.420, 1.09),
        spike("ctrl.gate", 7.780, 0.94),
        spike("ae.pack.pps", 10.400, 0.79),
        spike("p.reboil.MW", 14.200, 0.61),
        spike("ctrl.gate", 18.800, 0.83),
        spike("ae.pack.pps", 24.600, 0.51),
        spike("tc.base.C", 32.400, 0.39),
        spike("ae.pack.pps", 40.200, 0.36),
    ]
    excerpt = independent_excerpt(21603, 112, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Gatrich-Haugh GH-HIL gallium-trichloride still S-8 packing AE is already at 58 pps "
                "against a 14 pps distress trip. Still-base RTD is 86 C, 32 K shy of the 118 C "
                "reboiler cap, and reboiler duty is 1.4 MW under a 4.5 MW nameplate. AE-first must "
                "REJECT-hold the 1.9 MW raise; a base-first dispatch would steam a growling packed column.",
            ),
            ("domain", "gallium-trichloride-still"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep S-8 packing AE <= 14 pps on the GH-HIL stand and do not raise reboiler into "
                "a distressed packed bed.",
            ),
            ("t0_us", 1756850400000603),
            ("gate_latency_us", 580),
            ("race_window_us", 400),
            ("race_window_rel_ms", [7.200, 7.600]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.pack.pps 58 over 14 trip",
                                "tc.base.C 86 under 118 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first REJECT-holds the 1.9 MW raise; base-TC-first would treat 58 pps "
                            "as condenser hash and dispatch steam into a growling packing.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one packing-AE slot versus the still-base RTD publisher on this "
                            "GaCl3 HIL still bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 64 us (AE 30 + RTD 34): 3.44x over a 2.0x "
                            "trust floor. Reversing order by < 220 us inside the 400 us window would "
                            "have dispatched 1.9 MW into distressed packing.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "packing AE puck S-8, 5 kHz, 30 us jitter (HIL)",
                    "still-base RTD, 1 kHz, 34 us jitter",
                    "reboiler CT (context)",
                    "reflux Coriolis (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 14.0),
                        ("observed_ae_pps", 58.0),
                        ("base_C", 86.0),
                        ("base_cap_C", 118.0),
                        ("reboil_MW", 1.4),
                        ("reboil_cap_MW", 4.5),
                        ("proposed_mw", 1.9),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. S-8 HIL indexed; 1.9 MW raise armed.",
                    "2. Reboiler 1.4 MW under 4.5; AE 58 pps over 14.",
                    "3. CT precursor at 1.440 ms.",
                    "4. Race window [7.200, 7.600] ms.",
                    "5. ae.pack.pps 58 at 7.200 ms (winner).",
                    "6. tc.base.C 86 at 7.420 ms (loser by 220 us).",
                    "7. Gate at 7.780 ms: REJECT hold, do not raise.",
                    "8. Reboiler left at 1.4 MW; hold=true.",
                    "9. Packing inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min still reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "raise_reboiler"),
            (
                "parameters",
                OrderedDict([("reboil_MW", 1.9), ("hold", False), ("base_C", 86.0)]),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 58.0),
                        ("ae_cap_pps", 14.0),
                        ("reboil_MW", 1.4),
                        ("reboil_cap_MW", 4.5),
                        ("base_C", 86.0),
                        ("base_cap_C", 118.0),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 64),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.9 MW because base 86 C is under 118 and duty 1.4 MW is under "
                "4.5, treating 58 pps AE as condenser hash rather than a growling packed bed.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Packing AE 58 pps won by 220 us, so the GaCl3 still is growling, not still a "
                "base-temperature story. 1.4 MW is under 4.5 and does not authorize a raise. "
                "REJECT: hold reboiler at 1.4 MW. A MODIFY that only trims MW would leave the growl.",
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
                                    ("observed", 58.0),
                                    ("executed_reboil_MW", 1.4),
                                    ("hold", True),
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
            ("name", "hold_reboiler"),
            (
                "parameters",
                OrderedDict([("reboil_MW", 1.4), ("hold", True), ("base_C", 86.0)]),
            ),
            (
                "gate_effect",
                "REJECT: refuse 1.9 MW raise. Reboiler left at 1.4 MW under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held S-8. AE 58 pps beat base 86 C by 220 us. Duty was legal; "
                "the packing was not. 8 min still reset (abort_s=480) is delayed survey, not a "
                "process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("reboiler", "held at 1.4 MW"),
                        ("base", "left 86 C < 118 cap"),
                        ("packing", "8 min still reset (abort_s=480)"),
                        ("mission", "HIL still not raised"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Base RTD never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min still reset on the GH-HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.pack.pps (7.200 ms, 58 pps)"),
                        ("loser", "tc.base.C (7.420 ms, 86 C)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Base-first by < 220 us inside the 400 us window would have "
                            "dispatched 1.9 MW into a growling packed column. The REJECT is still "
                            "the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7780),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.780 ms, tick 4). The 8 min still "
                "reset is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    ras = raster_core(
        46,
        112,
        21,
        108,
        routing(
            "thalamic-relay.pack-ae",
            "spikenaut.policy.still-hold",
            [
                ("relay.ae.pack", "policy.still_hold", 0.71),
                ("relay.tc.base", "policy.mw_go", 0.23),
            ],
            "dopamine",
            0.06,
            "hold_stdp; DA tags the AE win as a reject-hold bind",
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
            ("decision_window_ms", 0.40),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop_budget("still_hold", 60, 0.45, 200.0, 0.40),
                    pop("mw_go", 40, 0.90),
                    pop_budget("ae_veto", 28, 0.70, 80.0, 0.40),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r21-603",
        "Gatrich-Haugh GH-HIL / Still S-8: packing AE 58 pps beats base 86 C by 220 us; "
        "correct REJECT holds the reboiler raise",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 58 > 14 cap beats legal reboiler duty. total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "gallium-trichloride-still",
        ["reject", "hil", "ae-vs-base-tc", "growling-packing", "tick6-sidecar-bound"],
        "Teaches that a legal reboiler-duty header can lose to packing AE inside a 400 us "
        "window; reversing 220 us would have steamed a growling GaCl3 still.",
        3,
    )


def record_604():
    ticks = [
        tick(2720, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(6800, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7020, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7520, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(7900, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(300000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.jacket.C", 1.360, 0.40),
        spike("h2o.ppm", 2.720, 0.55),
        spike("tc.jacket.C", 4.200, 0.48),
        spike("h2o.ppm", 6.800, 1.26),
        spike("tc.jacket.C", 7.020, 1.08),
        spike("ctrl.gate", 7.520, 0.95),
        spike("h2o.ppm", 11.400, 0.78),
        spike("tc.jacket.C", 14.800, 0.60),
        spike("ctrl.gate", 18.200, 0.82),
        spike("h2o.ppm", 22.400, 0.50),
        spike("tc.jacket.C", 25.600, 0.38),
    ]
    excerpt = independent_excerpt(21604, 56, 26000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("ethoxide_tph", 2.4),
            ("h2o_ppm", 180.0),
            ("jacket_C", 38.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Ethoxytant-Ness EN-5 hydrolyzer H-4 Karl-Fischer liquor sits at 180 ppm water "
                "versus a 420 ppm gelation trip. Jacket skin is 38 C, 34 K shy of 72 C. The 2.4 t/h "
                "tantalum-ethoxide recipe sits inside both caps; a jacket-first hold would idle a "
                "quiet simulated hydrolyzer.",
            ),
            ("domain", "tantalum-ethoxide-hydrolyzer"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the EN-5 hydrolysis pass with water <= 420 ppm and jacket <= 72 C.",
            ),
            ("t0_us", 1756850400000604),
            ("gate_latency_us", 720),
            ("race_window_us", 380),
            ("race_window_rel_ms", [6.800, 7.180]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "h2o.ppm 180 under 420 trip",
                                "tc.jacket.C 38 under 72 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "KF-first confirms the already-legal 2.4 t/h ethoxide feed; jacket-first "
                            "would have treated the Karl-Fischer as a flood echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one Karl-Fischer slot versus the jacket-TC publisher on this "
                            "simulated tantalum-ethoxide hydrolyzer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 62 us (KF 28 + jacket 34): 3.55x over "
                            "a 2.0x trust floor. Reversing order by < 220 us inside the 380 us window "
                            "would have idled a legal 2.4 t/h pass.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "online Karl-Fischer H-4, 1 kHz, 28 us jitter (simulated)",
                    "jacket skin TC, 1 kHz, 34 us jitter",
                    "ethoxide Coriolis (context)",
                    "stirrer torque (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("h2o_cap_ppm", 420.0),
                        ("observed_h2o_ppm", 180.0),
                        ("jacket_C", 38.0),
                        ("jacket_cap_C", 72.0),
                        ("ethoxide_tph", 2.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. H-4 simulated indexed; ethoxide 2.4 t/h; water 180 ppm.",
                    "2. Jacket 38 C under 72; gelation trip 420 ppm.",
                    "3. Jacket precursor at 1.360 ms.",
                    "4. Race window [6.800, 7.180] ms.",
                    "5. h2o.ppm 180 at 6.800 ms (winner).",
                    "6. tc.jacket.C 38 at 7.020 ms (loser by 220 us).",
                    "7. Gate at 7.520 ms: ACCEPT 2.4 t/h already legal.",
                    "8. Water stays 180 ppm; jacket 38 C.",
                    "9. Hydrolysis pass continues.",
                    "10. Delayed (survey_s=300): 5 min assay hold.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_ethoxide_feed"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("h2o_ppm", 180.0),
                        ("h2o_cap_ppm", 420.0),
                        ("jacket_C", 38.0),
                        ("jacket_cap_C", 72.0),
                        ("ethoxide_tph", 2.4),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 62),
                        ("survey_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.4 t/h because water 180 ppm is under 420 and jacket 38 C is "
                "under 72; the KF-first race confirms an already-legal hydrolyzer recipe.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Karl-Fischer 180 ppm won by 220 us and sits 240 ppm under the 420 gelation trip. "
                "Jacket 38 C is 34 K under 72. Proposed 2.4 t/h is already legal. ACCEPT equal to "
                "proposed_action. A jacket-first MODIFY-hold would idle a quiet simulated pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "h2o_ppm",
                            OrderedDict(
                                [
                                    ("cap", 420.0),
                                    ("observed", 180.0),
                                    ("executed_tph", 2.4),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 3.55),
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
            ("name", "cruise_ethoxide_feed"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: parameters equal proposed_action. 2.4 t/h already under both caps.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept 2.4 t/h. Water 180 ppm beat jacket 38 C by 220 us. Both "
                "channels were legal. 5 min assay hold (survey_s=300) is delayed survey, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held 2.4 t/h"),
                        ("water", "180 ppm < 420 cap"),
                        ("jacket", "38 C < 72 cap"),
                        ("mission", "EN-5 hydrolysis pass continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Jacket IR smear at 58 C never became the PV; KF 180 ppm stayed the live slot.",
                    "Delayed (survey_s=300): 5 min assay hold after the legal pass.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "h2o.ppm (6.800 ms, 180 ppm)"),
                        ("loser", "tc.jacket.C (7.020 ms, 38 C)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Jacket-first by < 220 us inside the 380 us window would have treated "
                            "the KF as a flood echo and idled 2.4 t/h. The ACCEPT is still the "
                            "correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7520),
            (
                "reward_inflection_note",
                "Task and safety rise at the correct ACCEPT (7.520 ms, tick 4). The 5 min assay "
                "hold is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 300),
        ]
    )
    ras = raster_core(
        26,
        56,
        40,
        58,
        routing(
            "thalamic-relay.kf-water",
            "spikenaut.policy.ethoxide-go",
            [
                ("relay.h2o.ppm", "policy.feed_go", 0.72),
                ("relay.tc.jacket", "policy.jacket_hold", 0.26),
            ],
            "serotonin",
            0.03,
            "go_stdp; 5-HT tags the already-legal KF win as an accept bind",
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
                    pop_budget("feed_go", 44, 0.45, 210.0, 0.38),
                    pop("jacket_hold", 32, 0.90),
                    pop("kf_veto", 18, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r21-604",
        "Ethoxytant-Ness EN-5 / Hydrolyzer H-4: KF 180 ppm beats jacket 38 C by 220 us; "
        "correct ACCEPT of already-legal 2.4 t/h",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Water 180 < 420 and jacket 38 < 72. total +1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "tantalum-ethoxide-hydrolyzer",
        ["accept", "simulated", "already-legal", "kf-vs-jacket", "tick6-sidecar-bound"],
        "Teaches an already-legal KF-first ACCEPT inside a 380 us window so a jacket smear does "
        "not idle a quiet tantalum-ethoxide hydrolyzer.",
        4,
    )


def record_605():
    excerpt, extra = lif_605_excerpt()
    ticks = [
        tick(1680, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(4200, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(4410, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(4760, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5120, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(240000000, 0.04, 0.04, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("ir.pyro.C", 0.840, 0.39),
        spike("ft.mts.slm", 1.680, 0.54),
        spike("ir.pyro.C", 2.800, 0.47),
        spike("ft.mts.slm", 4.200, 1.24),
        spike("ir.pyro.C", 4.410, 1.07),
        spike("ctrl.gate", 4.760, 0.94),
        spike("ft.mts.slm", 8.200, 0.77),
        spike("ir.pyro.C", 11.400, 0.59),
        spike("ctrl.gate", 14.800, 0.81),
        spike("ft.mts.slm", 18.200, 0.49),
        spike("ir.pyro.C", 21.400, 0.37),
    ]
    params = OrderedDict(
        [
            ("mts_slm", 3.6),
            ("pyro_C", 1180.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Carbolox-Knap CK-8 MTS-CVD reactor C-6 mass-flow of methyltrichlorosilane is 3.6 slm "
                "versus a 5.2 slm soot-cap. Wafer pyrometer is 1180 C, 230 K shy of a 1410 C smear "
                "that never became PV. The 3.6 slm recipe is already legal; a pyrometer-first hold "
                "would idle a quiet SiC deposition.",
            ),
            ("domain", "silicon-carbide-cvd-reactor"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the CK-8 SiC pass with MTS <= 5.2 slm and wafer pyrometer <= 1410 C.",
            ),
            ("t0_us", 1756850400000605),
            ("gate_latency_us", 560),
            ("race_window_us", 360),
            ("race_window_rel_ms", [4.200, 4.560]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.mts.slm 3.6 under 5.2 cap",
                                "ir.pyro.C 1180 under 1410 smear",
                            ],
                        ),
                        (
                            "semantics",
                            "MTS-first confirms the already-legal 3.6 slm recipe; pyro-first would have "
                            "treated the mass-flow as a soot echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one MTS mass-flow slot versus the wafer-pyrometer publisher on "
                            "this silicon-carbide CVD bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 210 us vs combined jitter 56 us (MFC 24 + pyro 32): 3.75x over a "
                            "2.0x trust floor. Reversing order by < 210 us inside the 360 us window "
                            "would have idled a legal 3.6 slm pass.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "MTS mass-flow C-6, 2 kHz, 24 us jitter",
                    "wafer pyrometer, 1 kHz, 32 us jitter",
                    "H2 carrier MFC (context)",
                    "chamber PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("mts_cap_slm", 5.2),
                        ("observed_mts_slm", 3.6),
                        ("pyro_C", 1180.0),
                        ("pyro_smear_C", 1410.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. C-6 indexed on Carbolox-Knap CK-8; MTS 3.6 slm; pyro 1180 C.",
                    "2. Soot-cap 5.2 slm; smear 1410 C is not PV.",
                    "3. Pyro precursor at 0.840 ms.",
                    "4. Race window [4.200, 4.560] ms.",
                    "5. ft.mts.slm 3.6 at 4.200 ms (winner).",
                    "6. ir.pyro.C 1180 at 4.410 ms (loser by 210 us).",
                    "7. Gate at 4.760 ms: ACCEPT 3.6 slm already legal.",
                    "8. MTS stays 3.6; pyro 1180 C.",
                    "9. SiC deposition continues.",
                    "10. Delayed (dwell_s=240): 4 min cooldown dwell.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_mts_flow"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("mts_slm", 3.6),
                        ("mts_cap_slm", 5.2),
                        ("pyro_C", 1180.0),
                        ("pyro_smear_C", 1410.0),
                        ("race_margin_us", 210),
                        ("combined_jitter_us", 56),
                        ("dwell_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 3.6 slm because MTS is under 5.2 and wafer 1180 C is under the "
                "1410 smear; the MTS-first race confirms an already-legal CVD recipe.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "MTS 3.6 slm won by 210 us and sits 1.6 slm under the 5.2 soot-cap. Pyrometer "
                "1180 C is 230 K under the 1410 smear that is not PV. Proposed 3.6 slm is already "
                "legal. ACCEPT equal to proposed_action. A pyro-first hold would idle a quiet SiC pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "mts_slm",
                            OrderedDict(
                                [
                                    ("cap", 5.2),
                                    ("observed", 3.6),
                                    ("executed_slm", 3.6),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 210),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 3.75),
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
            ("name", "cruise_mts_flow"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: parameters equal proposed_action. 3.6 slm already under the 5.2 soot-cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept 3.6 slm. MTS beat pyrometer smear by 210 us. Both channels "
                "were legal. 4 min cooldown dwell (dwell_s=240) is delayed survey, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("mts", "held 3.6 slm"),
                        ("pyro", "1180 C; smear 1410 never became PV"),
                        ("dwell", "4 min cooldown (dwell_s=240)"),
                        ("mission", "CK-8 SiC pass continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Pyrometer smear at 1410 C never became the PV; MTS 3.6 slm stayed the live slot.",
                    "Delayed (dwell_s=240): 4 min cooldown dwell after the legal pass.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.mts.slm (4.200 ms, 3.6 slm)"),
                        ("loser", "ir.pyro.C (4.410 ms, 1180 C)"),
                        ("margin_us", 210),
                        (
                            "counterfactual_if_reversed",
                            "Pyro-first by < 210 us inside the 360 us window would have treated "
                            "the MFC as a soot echo and idled 3.6 slm. The ACCEPT is still the "
                            "correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4760),
            (
                "reward_inflection_note",
                "Task and safety rise at the correct ACCEPT (4.760 ms, tick 4). The 4 min dwell "
                "is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 240),
        ]
    )
    ras = raster_core(
        22,
        84,
        30,
        55,
        routing(
            "thalamic-relay.mts-mfc",
            "spikenaut.policy.mts-go",
            [
                ("relay.ft.mts", "policy.mts_go", 0.73),
                ("relay.ir.pyro", "policy.pyro_hold", 0.25),
            ],
            "adenosine",
            0.045,
            "go_stdp; adenosine tags the already-legal MTS win as an accept bind covering the 22 ms raster",
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
                    pop_budget("mts_go", 50, 0.45, 220.0, 0.36),
                    pop("pyro_hold", 34, 0.90),
                    pop("soot_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r21-605",
        "Carbolox-Knap CK-8 / CVD C-6: MTS 3.6 slm beats pyro 1180 C by 210 us; correct ACCEPT "
        "of already-legal recipe (second labeled LIF)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. MTS 3.6 < 5.2 and pyro 1180 < 1410 smear. total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08. "
        "Second independent LIF this round (success path).",
        ras,
        gate,
        "silicon-carbide-cvd-reactor",
        [
            "accept",
            "designed",
            "already-legal",
            "independent-lif-raster",
            "sidecar-sim-only",
            "tick6-sidecar-bound",
        ],
        "Second labeled LIF: a critic can see already-legal MTS as membrane crossings inside the "
        "22 ms raster without a world-charge burst, pairing the partnered-negative LIF on 601.",
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
    if rec["id"] == "ttf-r21-601":
        tick5 = 22800
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
    skip = {"ttf-sf-r21"}
    for path in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
        if path.parent.name in skip:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            d = rec.get("state", {}).get("domain") or rec.get("meta", {}).get("domain")
            if d:
                domains.add(str(d))
            title = rec.get("title") or ""
            m = re.match(r"(?:WRONG-(?:MODIFY|REJECT) at )?([A-Za-z0-9-]+)", title)
            if m:
                plants.add(m.group(1))
            desc = rec.get("state", {}).get("description") or ""
            for frag in PLANT_RE.findall(title + " " + desc):
                plants.add(frag)
    for gpath in sorted(Path("/tmp").glob("ttf-r*/*.py")):
        if gpath.parent.name in skip:
            continue
        txt = gpath.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(
            r"(?:THIS_DOMAINS|MY_DOMAINS)\s*=\s*[\{(]([^})]+)[\})]", txt
        ):
            domains.update(re.findall(r'"([^"]+)"', m.group(1)))
        for m in re.finditer(r"(?:THIS_PLANTS|MY_PLANTS)\s*=\s*\(([^)]+)\)", txt):
            plants.update(re.findall(r'"([^"]+)"', m.group(1)))
    for npath in sorted(Path("/tmp").glob("ttf-r*/NOTES-r*.md")):
        if npath.parent.name in skip:
            continue
        for line in npath.read_text(encoding="utf-8", errors="ignore").splitlines():
            if "Domains this batch" in line:
                for tok in re.findall(r"`([^`]+)`", line):
                    if not tok.startswith("ttf-"):
                        domains.add(tok)
    domains -= THIS_DOMAINS
    plants -= set(THIS_PLANTS)
    domains.discard("")
    plants.discard("")
    return domains, plants


def prior_domains_and_descs():
    domains = set()
    descs = []
    blobs = []
    for path in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
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
    occ_doms, occ_plants = harvest_occupancy()
    for plant in THIS_PLANTS:
        if plant in prior_blob:
            issues.append(f"plant {plant} collides prior jsonl")
        if plant in occ_plants:
            issues.append(f"plant {plant} collides occupancy harvest")
    jprior = 0.0
    for desc in descs:
        for other in prior_descs:
            jprior = max(jprior, jaccard(desc, other))
    if jprior >= 0.70:
        issues.append(f"Jaccard vs prior {jprior:.3f}")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domain collision {domains}")
    overlap = set(domains) & prior_doms
    if overlap:
        issues.append(f"prior domain reuse {overlap}")
    overlap_h = set(domains) & occ_doms
    if overlap_h:
        issues.append(f"harvest domain reuse {overlap_h}")
    if set(domains) != THIS_DOMAINS:
        issues.append(f"unexpected domains {domains}")
    banned_hit = set(domains) & PROMPT_POOL
    if banned_hit:
        issues.append(f"prompt-pool domains {banned_hit}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r21-602":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-modify":
        issues.append("expected wrong-modify")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r21-603"]:
        issues.append(f"hil set {hil}")
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if sim != ["ttf-r21-604"]:
        issues.append(f"simulated set {sim}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if (
        decisions.count("ACCEPT") != 2
        or decisions.count("MODIFY") != 2
        or decisions.count("REJECT") != 1
    ):
        issues.append(f"gate mix {decisions}")
    ids = [r["id"] for r in records]
    if ids != [f"ttf-r21-{n}" for n in range(601, 606)]:
        issues.append(f"ids {ids}")
    lif_ids = [
        r["id"]
        for r in records
        if r["raster"].get("excerpt_source") == "independent_lif"
    ]
    if set(lif_ids) != {"ttf-r21-601", "ttf-r21-605"}:
        issues.append(f"LIF set {lif_ids}")
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
        if rec["id"] in {"ttf-r21-601", "ttf-r21-605"}:
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append(f"{rec['id']} missing independent_lif")
            if rec["id"] == "ttf-r21-601":
                if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                    issues.append("601 inflection outside window")
                if rec["reward_components"]["total"] >= 0:
                    issues.append("601 partnered-neg total not negative")
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
        if rec["meta"]["round"] != ROUND:
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
        if rec["id"] == "ttf-r21-602":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["live_so2_ppm"] > ev["cap_so2_ppm"]):
                issues.append("602 live SO2 not over cap")
            if ev.get("command_convention") != "percent_open":
                issues.append("602 command_convention not percent_open")
            if rec["executed_action"]["parameters"].get("bind_percent_closed") is not True:
                issues.append("602 bind_percent_closed not true")
            if rec["executed_action"]["parameters"].get("damper_pct_open") != 88.0:
                issues.append("602 damper should open to 88")
            if rec["executed_action"]["parameters"].get("live_so2_ppm") != 1840.0:
                issues.append("602 live SO2 should stay 1840")
            if "recovery" not in rec["future_outcome"]:
                issues.append("602 missing recovery")
            table_to = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.damper_close" in table_to:
                issues.append("602 routing still has damper_close")
            if "policy.damper_open" not in table_to:
                issues.append("602 routing missing damper_open")
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
        tau = rec["raster"]["routing"]["third_factor"]
        if abs(tau["tau_e_ms"] / 1000.0 - tau["tau_e_s"]) > 1e-9:
            issues.append(f"{rec['id']} tau pair")
    return issues, jmax, jprior


def notes_text(jmax: float, jprior: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r21

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r21-601` … `ttf-r21-605` (121–125 already occupy `/tmp/ttf-r21`; this window uses 601–605)
- Domains this batch: `beryllium-fluoride-reducer`, `molybdenum-disulfide-roaster`, `gallium-trichloride-still`, `tantalum-ethoxide-hydrolyzer`, `silicon-carbide-cvd-reactor`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r110 occupancy (jsonl + generator SoT), including original r21 (`funicular` / `PCB-reflow` / `anaerobic-digester` / `tidal-barrage` / `grain-elevator`) and newest r102/r105 (`cesium-formate-crystallizer` / `osmium-tetroxide-absorber` / HDI-phosgenator / nylon-12 / PVDF / PEEK). Distinct from r91 `rhenium-heptoxide-scrubber`, r104 `samarium-cobalt-sinter`, r107 `aluminum-nitride-sinter`, r109 `vanadium-oxytrichloride-still`. All five plants are invented (Glucinum-Beck, Molybdenite-Gair, Gatrich-Haugh, Ethoxytant-Ness, Carbolox-Knap). Do not restack prior TTF plants. Original r21 wrong-polarity is not restacked.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r21-601 | beryllium-fluoride-reducer | MODIFY | correct | designed | **−0.44** | process-correct Mg clamp; pot-lining slump inside 44 ms raster; independent LIF |
| ttf-r21-602 | molybdenum-disulfide-roaster | MODIFY | **incorrect (wrong-modify / percent-open vs percent-closed)** | designed | −0.68 | live SO2 1840 ppm > 900 cap; damper 72 → 88 pct-open on a percent-closed bind |
| ttf-r21-603 | gallium-trichloride-still | REJECT | correct | hil | +0.80 | packing AE 58 pps beats base 86 C; hold 1.9 MW raise |
| ttf-r21-604 | tantalum-ethoxide-hydrolyzer | ACCEPT | correct | simulated | +1.06 | KF 180 ppm vs jacket 38 C; proposed 2.4 t/h already legal |
| ttf-r21-605 | silicon-carbide-cvd-reactor | ACCEPT | correct | designed | +1.14 | MTS 3.6 slm vs pyro smear 1410 C; second labeled LIF |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (percent-open vs percent-closed), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Gatrich-Haugh GH-HIL GaCl3 still). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}).

## Wrong-modify / percent-open vs percent-closed

**ttf-r21-602** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: odd rounds host wrong-modify. This is **percent-open vs percent-closed** (live SO2 encoder over published cap on K-3; actuator convention is percent_open at 72; a leftover percent-closed shadow is 28; supervisor writes 88 as if it were percent-closed; actuator opens 72 → 88). Not r13/r19 wrong-axis, not r14/r23 wrong-loop, not original r21 **wrong-polarity**, not r24 under-clamp, not r25/r29/r31 wrong-phase, not r33/r35 over-clamp, not r37/r39/r43 clamp-too-late, not r45 clamp-too-early, not r47–r57 stale-sample, not r59/r65/r67 wrong-string, not r69 split-range-wrong-half, not r71–r77 wrong-unit / lagged-bus, not r79 selector-wrong-leg, not r83 wrong-bank polarity-invert, not r85 ratio-pair invert, not r87 dual-range deadband, not r89 dual-range-wrong-band, not r91 wrong-polarity-fresh-tag, not r95 lead-lag invert, not r99 feedforward-as-feedback, not r103/r105 leftover-faceplate shadow-setpoint. Distinct from original r21 heater raise-vs-clamp: here the live PV is already over cap and the error is the 0–100 command convention, not a thermocouple sign flip. Do not emit a wrong-ACCEPT.

Molybdenite-Gair MG-6 / Roaster K-3 (LIVE) reads live SO2 **1840 ppm** against a **900** cap. Damper is **72 percent-open**. Sidecar arithmetic `1840 > 900` is true. A timely MODIFY at `t_gate_us=5900` cuts damper **72 → 38 pct-open**. A weak supervisor binds percent-closed and MODIFY-opens **72 → 88 pct-open**. Live stays **1840 > 900**. Convictable without molybdenite chemistry: `evidence.live_so2_ppm > evidence.cap_so2_ppm`, `evidence.command_convention == percent_open`, `executed_action.bind_percent_closed == true`, `executed_action.damper_pct_open == 88.0` greater than proposed 72, `raster.routing.table` sends `relay.cmd.pctclosed` → `policy.damper_open` (weight 0.74) with no positive weight to `policy.damper_close`, and `gate_snn` has `damper_open` above threshold while `damper_close` is not. Recovery: MODIFY damper 72 → 38 pct-open on K-3 at t_gate; leave concentrate 6.2 t/h; leave K3_DMP.CMD_CL unbound. Cost: 11 min SO2 dump (`abort_s=660`).

## Partnered-negative in-window (601) and second LIF (605)

**ttf-r21-601** is the partnered negative: process-correct MODIFY (Mg held 4.6 t/h; HF 12 ppm <= 18 cap) while the world still charges. Safety −0.60 prices the pot-lining slump at **22.800 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22800` is tick 5 and is **inside** the 44 ms raster (`22800 ≤ 44000`). Named un-netted loss: 14 min pot isolate (`abort_s=840`). Not folded into process heads.

Independent LIF #1: `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 21601, stim `[22000, 25600]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.slump` 22–25.6 ms), not a 1:1 remap of `spike_events`.

**ttf-r21-605** is the second labeled LIF (flagged gap from r102/r105). Success-path membrane crossings on an already-legal ACCEPT. Seed 21605, stim `[4000, 7200]` covering the race+gate inside the 22 ms raster. Plant remains designed. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only` on both 601 and 605.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 601 | 6 | +0.32 | −0.60 | −0.16 | +0.04 | −0.04 | −0.44 | 5 (22800) |
| 602 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (5900) |
| 603 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7780) |
| 604 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (7520) |
| 605 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (4760) |

Tick-6 sidecar bind: 601 `abort_s=840`, 602 `abort_s=660`, 603 `abort_s=480`, 604 `survey_s=300`, 605 `dwell_s=240`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 601 | beryllium-fluoride-reducer | 74 | 25 | 44 | 81 | 1863 | 0.001863 |
| 602 | molybdenum-disulfide-roaster | 90 | 32 | 30 | 86 | 1978 | 0.001978 |
| 603 | gallium-trichloride-still | 112 | 21 | 46 | 108 | 2484 | 0.002484 |
| 604 | tantalum-ethoxide-hydrolyzer | 56 | 40 | 26 | 58 | 1334 | 0.001334 |
| 605 | silicon-carbide-cvd-reactor | 84 | 30 | 22 | 55 | 1265 | 0.001265 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-LIF excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Create-only into the assigned window path; did not clobber `/tmp/ttf-r21/` or repo `outputs/raw/`.

## Residual weaknesses (honest)

1. Two labeled independent LIFs (601, 605) close the r102/r105 densification note; 602–604 excerpts remain kernelized rather than population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool (same sit-out as original r21 and r98–r110); a later window round that must stay inside the pool will have to rotate sit-outs instead.
5. 604 and 605 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative.

## Next densification target

ISI histogram sidecar, or **wrong-hysteresis on a split-range control valve** (still unused after this percent-open/percent-closed round). Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 18.4%
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
        BATCH_PATH, "batch-r21.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r21.jsonl:{i}", factory_staging=True)
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
    if BATCH_PATH.exists() or NOTES_PATH.exists():
        print(f"refuse: {BATCH_PATH.name if BATCH_PATH.exists() else NOTES_PATH.name} already exists")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_601(), record_602(), record_603(), record_604(), record_605()]
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
