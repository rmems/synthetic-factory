#!/usr/bin/env python3
"""Emit TTF r24 JSONL (ttf-r24-136..140) into /tmp/ttf-r24/. Never writes outputs/raw/."""

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

OUT_DIR = Path("/tmp/ttf-r24")
BATCH_PATH = OUT_DIR / "batch-r24.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r24.md"
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
BANNED_DOMAINS = {
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
    "euv-wafer-stage",
    "proton-gantry-gate",
    "tbm-slurry-shield",
    "wave-energy-latching",
    "fiber-draw-tower",
    "brewery-CIP",
    "ski-lift",
    "data-center-CDU",
    "canal-lock",
    "blast-furnace",
    "satellite-servicing",
    "mine-ventilation",
    "paper-machine",
    "cryo-storage",
    "amusement-ride",
    "mill-scale-pit",
    "battery-formation",
    "grain-elevator",
    "glass-lehr",
    "tunnel-boring",
    "vial-lyophilizer",
    "lng-open-rack",
    "LNG-boiloff",
    "lng-unloading-arm",
    "lyophilizer-shelf",
    "satellite-servicing",
    "mine-ventilation",
    "paper-machine",
    "cryo-storage",
    "amusement-ride",
    "trolleybus",
    "glass-float-line",
    "hyperbaric-weld",
    "radio-telescope-pointing",
    "funicular",
    "PCB-reflow",
    "anaerobic-digester",
    "tidal-barrage",
    "grain-elevator",
    "maglev-guideway-gap",
    "grain-elevator-leg",
    "hyperbaric-weld-habitat",
    "tunnel-oven-bakery",
    "rotary-lime-kiln",
    "metro-psd",
    "aluminum-potline",
    "sts-quay-crane",
}
BANNED_PLANT_FRAGMENTS = (
    "Marrow-Dock",
    "Vesper-Lattice",
    "Brine-Well",
    "Saddle-Arc",
    "Ashlar-Gait",
    "Nacre-Well",
    "Quern-Forge",
    "Tinder-Box",
    "Whimbrel-Stack",
    "Cinder-Loft",
    "Suture-Isle",
    "Kiln-Spur",
    "Oxbow-Switch",
    "Pitch-Kettle",
    "Shale-Quay",
    "Polder-Rye",
    "Flint-Mask",
    "Gyre-Tokamak",
    "Quarry-Bowl",
    "Orpiment",
    "Glimmer-Forge",
    "Feldspar-Arc",
    "Basalt-Rook",
    "Fetch-Sound",
    "Silica-Well",
    "Sinter-Gown",
    "Kettle-Stack",
    "Barrow-Mezz",
    "Grit-Sump",
    "Firth-Spur",
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


def lif_136_excerpt():
    n = 80
    dt_us = 100
    tau_m_ms = 20.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.92
    i_stim_peak = 2.40
    stim = (23200, 26200)
    seed = 24136
    window_us = 40000
    i_clamp_extra = 0.70
    clamp_n = 16
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
    early = [(t, nid) for t, nid in spikes if t < 23200]
    burst = [(t, nid) for t, nid in spikes if 23200 <= t < 26200]
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
            group = [1 for tt, _ in picked if (tt < 23200) == (pool[0][0] < 23200)]
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
    take(burst, 9, label_times=(24200, 24800, 25600))
    clamp = [(t, nid) for t, nid in picked if t < 23200][:7]
    tear = [(t, nid) for t, nid in picked if t >= 23200][:9]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    if len(picked) < 12:
        raise RuntimeError(f"LIF excerpt short: {len(picked)} early={len(early)} burst={len(burst)}")
    channels = ["lif.clamp" if t < 23200 else "lif.crack" for t, _ in picked]
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
            ("i_stim_peak", 2.40),
            ("stim_t_us", [23200, 26200]),
            ("i_clamp_extra", 0.70),
            ("clamp_n", 16),
            ("seed", 24136),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-15 carry +0.70 current-clamp bias; stim 23.2-26.2 ms is the membrane-pinhole burst.",
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
            ("round", 24),
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


def kernel_extra():
    return OrderedDict(
        [
            ("excerpt_source", "kernelized_events"),
            ("sim_scope", "none"),
        ]
    )


def record_136():
    excerpt, extra = lif_136_excerpt()
    ticks = [
        tick(2180, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(6080, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(6280, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6800, 0.10, -0.06, -0.03, 0.02, -0.01),
        tick(24200, 0.07, -0.42, -0.04, 0.00, -0.02),
        tick(1140000000, 0.02, -0.05, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Stack-K4 on Sedge-Cell SC-9 already sits at 2.18 V per cell against a 2.00 V "
                "stack cap while a 62 C coolant-outlet residual still looks like a pump bump. "
                "Voltage-first drops current 1.80 -> 1.10 A/cm2 under the cap; coolant-first "
                "would keep the 1.80 A/cm2 cruise. A pinhole already seated in membrane 11 does "
                "not appear on voltage or RTD until the AE burst.",
            ),
            ("domain", "electrolyzer-stack"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the SC-9 hydrogen pass with stack voltage <= 2.00 V/cell and without "
                "pinholing a membrane.",
            ),
            ("t0_us", 1756843200000136),
            ("gate_latency_us", 720),
            ("race_window_us", 360),
            ("race_window_rel_ms", [6.0, 6.36]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "cell.v.stack 2.18 V/cell",
                                "tc.coolant.out 62 C residual",
                            ],
                        ),
                        (
                            "semantics",
                            "Voltage-first latches current clamp 1.80 -> 1.10 A/cm2; coolant-first "
                            "keeps 1.80 A/cm2 cruise on a 'still a pump bump' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one 1 kHz stack-voltage slot minus coolant-RTD demodulation "
                            "group delay on this cell bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 200 us vs combined jitter ~70 us (voltage 32 + RTD 38): 2.9x "
                            "over a 2.0x trust floor. Reversing order by < 200 us inside the 360 us "
                            "window would have kept 1.80 A/cm2 cruise; predicted next-sample 2.08 V "
                            "> 2.00 V cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "stack cell-voltage tap, 1 kHz, 32 us timestamp jitter",
                    "coolant-outlet RTD 0-90 C, 38 us jitter",
                    "membrane AE puck on cell 11, 50 kHz (context)",
                    "recirc-pump encoder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("stack_cap_V", 2.0),
                        ("proposed_cell_V", 2.18),
                        ("coolant_out_C", 62.0),
                        ("cell_count", 86),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Stack-K4 indexed onto SC-9; 86 cells at 2.18 V against a 2.00 V cap.",
                    "2. Cruise current 1.80 A/cm2 armed; coolant outlet 62 C residual.",
                    "3. Pump precursor at 2.180 ms; voltage warm-start 2.18 V.",
                    "4. Race window [6.000, 6.360] ms opens on the cell bus.",
                    "5. cell.v.stack 2.18 V at 6.080 ms (winner).",
                    "6. tc.coolant.out 62 C at 6.280 ms (loser by 200 us).",
                    "7. Gate at 6.800 ms (winner + 720 us): MODIFY current 1.80 -> 1.10 A/cm2.",
                    "8. Clamp executes; next-sample voltage 1.92 V < 2.00 cap.",
                    "9. At 24.200 ms membrane 11 pinholes; AE burst.",
                    "10. 19 min stack-module swap (abort_s=1140); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_stack_current"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("current_A_cm2", 1.8),
                        ("cell_V", 2.18),
                        ("coolant_out_C", 62.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("cell_V", 2.18),
                        ("stack_cap_V", 2.0),
                        ("predicted_unclamped_next_V", 2.08),
                        ("coolant_out_C", 62.0),
                        ("race_margin_us", 200),
                        ("combined_jitter_us", 70),
                        ("abort_s", 1140),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.80 A/cm2 cruise: 62 C coolant looks like a pump bump, not "
                "stack heating, and the 86-cell string is treated as still legal.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Stack voltage 2.18 V won by 200 us, so the cells are loading, not still a "
                "coolant bump. Holding 1.80 A/cm2 predicts next-sample 2.08 V > 2.00 V cap. "
                "MODIFY: current 1.80 -> 1.10 A/cm2. Observed after clamp 1.92 V < 2.00. A full "
                "REJECT is not indicated: a sound membrane accepts 1.10 A/cm2.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "cell_V",
                            OrderedDict(
                                [
                                    ("cap", 2.0),
                                    ("observed", 2.18),
                                    ("predicted_unclamped_next", 2.08),
                                    ("clamped_current_A_cm2", 1.10),
                                    ("observed_after_clamp", 1.92),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 200),
                                    ("combined_jitter_us", 70),
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
            ("name", "clamped_stack_current"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("current_A_cm2", 1.10),
                        ("cell_V", 1.92),
                        ("coolant_out_C", 62.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: current 1.80 -> 1.10 A/cm2. Process-correct vs the 2.00 V cap. "
                "Membrane 11 still pinholes at 24.200 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held stack at 1.92 V. At 24.200 ms a pinhole already "
                "seated in membrane 11 vented hydrogen. Clamp reduced dump energy; it did not "
                "prevent the pinhole. Partnered negative: process heads stay honest; world loss "
                "is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("stack", "clamp executed; peak 1.92 V < 2.00 V cap"),
                        ("membrane_11", "pinhole at 24.200 ms"),
                        ("repair", "19 min stack-module swap (abort_s=1140)"),
                        ("mission", "SC-9 hydrogen pass incomplete this cycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither stack voltage nor coolant RTD predicted the seated pinhole; ae.mem.pinhole is a new channel at 24.200 ms, 17.400 ms after the gate, still inside the 40 ms raster.",
                    "Delayed (abort_s=1140): 19 min stack-module swap. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "19 min stack-module swap after membrane 11 pinhole. Safety head -0.62 prices "
                "the vent; task_progress stays +0.36 because the current clamp completed under "
                "the 2.00 V cap. World loss is named here, not subtracted from process heads.",
            ),
            ("abort_s", 1140),
            ("delayed_surprise_s", 1140),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "cell.v.stack (6.080 ms, 2.18 V)"),
                        ("loser", "tc.coolant.out (6.280 ms, 62 C)"),
                        ("margin_us", 200),
                        (
                            "counterfactual_if_reversed",
                            "Coolant-first by < 200 us inside the 360 us window would have kept "
                            "1.80 A/cm2 cruise; predicted next-sample 2.08 V would have exceeded "
                            "the 2.00 V cap even without the pinhole. The MODIFY is still the "
                            "correct process. The pinhole is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 24200),
            (
                "reward_inflection_note",
                "Safety collapses at the 24.200 ms membrane-11 pinhole (tick t_us=24200), inside "
                "the 40 ms raster. The correct MODIFY at 6.800 ms is in the same excerpt. Do not "
                "put inflection on the abort_s=1140 swap tick.",
            ),
        ]
    )
    spikes = [
        spike("enc.pump.ctx", 1.210, 0.42),
        spike("cell.v.stack", 2.440, 0.59),
        spike("tc.coolant.out", 3.880, 0.51),
        spike("cell.v.stack", 6.080, 1.30),
        spike("tc.coolant.out", 6.280, 1.15),
        spike("ctrl.gate", 6.800, 0.98),
        spike("cell.v.stack", 8.440, 0.81),
        spike("tc.coolant.out", 10.920, 0.64),
        spike("ctrl.gate", 14.210, 0.86),
        spike("ae.mem.pinhole", 24.200, 1.44),
        spike("ae.mem.pinhole", 26.050, 0.93),
        spike("enc.pump.ctx", 31.800, 0.40),
        spike("cell.v.stack", 36.400, 0.55),
    ]
    ras = raster_core(
        40,
        80,
        25,
        80,
        routing(
            "thalamic-relay.stack-v",
            "spikenaut.policy.current-clamp",
            [
                ("relay.cell.v", "policy.current_clamp", 0.66),
                ("relay.tc.coolant", "policy.coolant_hold", 0.32),
                ("relay.ae.pinhole", "policy.current_clamp", -0.46),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at voltage win (6.080 ms) opens a 50 ms eligibility "
            "trace that still covers the 24.200 ms pinhole",
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
                    pop("current_clamp", 48, 0.50, 280.0, 5),
                    pop("coolant_hold", 48, 0.50, 90.0, 2),
                    pop("stack_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r24-136"),
            (
                "title",
                "Sedge-Cell SC-9 / Stack-K4: stack 2.18 V beats coolant 62 C by 200 us; correct "
                "MODIFY still eats an in-window membrane-11 pinhole (partnered negative total -0.42)",
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
                    "40 ms raster. total -0.42 = 0.36 + -0.62 + -0.16 + 0.04 + -0.04. Named stack "
                    "swap (abort_s=1140) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "electrolyzer-stack",
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
                    "19 min stack swap.",
                    1,
                ),
            ),
        ]
    )


def record_137():
    ticks = [
        tick(2084, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(5210, -0.04, -0.03, -0.04, -0.02, 0.01),
        tick(5470, -0.03, -0.02, -0.03, -0.01, 0.01),
        tick(5850, -0.08, -0.07, -0.08, -0.04, 0.02),
        tick(6370, -0.03, -0.03, -0.04, -0.01, 0.01),
        tick(1320000000, -0.02, -0.02, -0.03, -0.01, 0.00),
    ]
    spikes = [
        spike("tc.coolant.ctx", 1.088, 0.43),
        spike("ir.tj.c", 2.410, 0.62),
        spike("enc.alpha.deg", 3.220, 0.55),
        spike("ir.tj.c", 5.210, 1.34),
        spike("enc.alpha.deg", 5.470, 1.12),
        spike("ctrl.gate", 5.850, 0.97),
        spike("ir.tj.c", 7.120, 0.81),
        spike("enc.alpha.deg", 8.880, 0.66),
        spike("ctrl.gate", 12.400, 0.84),
        spike("ir.tj.c", 16.800, 0.58),
        spike("tc.coolant.ctx", 20.110, 0.39),
        spike("enc.alpha.deg", 24.400, 0.44),
    ]
    excerpt = independent_excerpt(24137, 64, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Thyristor string T-19 in Fjord-Convert FC-12 already carries 1380 A DC when "
                "junction IR reports 98.4 C against an 85.0 C cap. The firing-angle encoder is "
                "still at 18 deg, the correct actuator for a current clamp. IR-first should bind "
                "alpha 18 -> 8 deg (1080 A under the 1200 A cap); a weak supervisor applies the "
                "same actuator but only 18 -> 14 deg, leaving 1290 A over cap.",
            ),
            ("domain", "hvdc-thyristor-valve"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold DC current <= 1200 A and junction temperature <= 85.0 C by clamping firing "
                "angle on string T-19, not by opening a bypass breaker.",
            ),
            ("t0_us", 1756843200000137),
            ("gate_latency_us", 640),
            ("race_window_us", 480),
            ("race_window_rel_ms", [5.0, 5.48]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.tj.c 98.4 C on string T-19",
                                "enc.alpha.deg 18 deg planned",
                            ],
                        ),
                        (
                            "semantics",
                            "IR-first should latch a full alpha clamp 18 -> 8 deg; encoder-first "
                            "is a false 'angle already legal' bind. The error this round is "
                            "under-clamp magnitude on the correct actuator, not the race winner.",
                        ),
                        (
                            "window_derivation",
                            "480 us = one valve-hall IR sample versus the firing-angle encoder "
                            "publisher on this 12-pulse bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 260 us vs combined jitter 82 us (IR 40 + encoder 42). Order "
                            "is correctly IR-first. The error is clamp magnitude on alpha, not "
                            "which actuator is bound.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "junction IR pyrometer, 2 kHz, 40 us jitter, string T-19",
                    "firing-angle encoder, 1 kHz, 42 us jitter",
                    "DC current shunt (context)",
                    "deionized-water RTD (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("i_cap_A", 1200.0),
                        ("observed_i_A", 1380.0),
                        ("tj_cap_C", 85.0),
                        ("observed_tj_C", 98.4),
                        ("proposed_alpha_deg", 18.0),
                        ("correct_alpha_deg", 8.0),
                        ("underclamp_alpha_deg", 14.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. String T-19 conducting; 1380 A DC, junction IR 98.4 C.",
                    "2. Alpha planned 18 deg; 1200 A / 85.0 C caps published on the sidecar.",
                    "3. Coolant RTD precursor at 2.084 ms.",
                    "4. Race window [5.000, 5.480] ms.",
                    "5. ir.tj.c 98.4 C at 5.210 ms (winner).",
                    "6. enc.alpha.deg 18 deg at 5.470 ms (loser by 260 us).",
                    "7. Gate at 5.850 ms: wrong MODIFY alpha 18 -> 14 deg; I stays 1290 A.",
                    "8. Junction still 96 C; current still over the 1200 A cap.",
                    "9. Commutation window missed; string abort armed.",
                    "10. Delayed missed_window_s=1320 (22 min) while the pole waits on T-19.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_alpha_18"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("alpha_deg", 18.0),
                        ("i_dc_A", 1380.0),
                        ("string", "T-19"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("i_dc_A", 1380.0),
                        ("i_cap_A", 1200.0),
                        ("tj_C", 98.4),
                        ("tj_cap_C", 85.0),
                        ("proposed_alpha_deg", 18.0),
                        ("correct_alpha_deg", 8.0),
                        ("predicted_i_at_8deg_A", 1080.0),
                        ("predicted_i_at_14deg_A", 1290.0),
                        ("actuator", "firing_angle"),
                        ("race_margin_us", 260),
                        ("combined_jitter_us", 82),
                        ("missed_window_s", 1320),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes holding alpha 18 deg and 1380 A. Junction IR 98.4 C is treated "
                "as a pyrometer glint; the 1200 A cap is not applied.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Junction 98.4 C exceeds the 85.0 C cap and 1380 A exceeds 1200 A (true). Nudge "
                "firing angle 18 -> 14 deg on T-19 to bleed current without a full hold. 14 deg "
                "is still a clamp on the correct actuator.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "i_dc_A",
                            OrderedDict(
                                [
                                    ("cap", 1200.0),
                                    ("observed", 1380.0),
                                    ("executed", 1290.0),
                                    ("still_over_cap", True),
                                ]
                            ),
                        ),
                        (
                            "alpha_deg",
                            OrderedDict(
                                [
                                    ("proposed", 18.0),
                                    ("executed_underclamp", 14.0),
                                    ("correct", 8.0),
                                    ("actuator", "firing_angle"),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 260),
                                    ("combined_jitter_us", 82),
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
            ("name", "alpha_nudge_underclamp"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("alpha_deg", 14.0),
                        ("i_dc_A", 1290.0),
                        ("string", "T-19"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / under-clamp): alpha 18 -> 14 deg on the correct actuator; "
                "I remains 1290 A > 1200 A cap. Routing relay.ir.tj -> policy.alpha_nudge; no "
                "positive weight to policy.alpha_hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY nudged alpha 18 -> 14 deg while DC current stayed at 1290 A over "
                "the 1200 A cap. String T-19 abort; 22 min pole wait. Correct gate was MODIFY "
                "alpha 18 -> 8 deg (1080 A).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("alpha", "under-clamped at 14 deg; correct 8 deg abandoned"),
                        ("i_dc", "still 1290 A, over 1200 A cap"),
                        ("string", "T-19 abort armed"),
                        ("pole", "22 min wait (missed_window_s=1320)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "A 4 deg alpha nudge dropped I only 1380 -> 1290 A and left junction 96 C; the 1200 A cap was never met.",
                    "Delayed (missed_window_s=1320): pole wait while T-19 is locked out; commutation window lost.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY on firing angle: alpha 18 -> 8 deg; I 1380 -> 1080 A. Leave "
                            "bypass breaker closed.",
                        ),
                        ("correct_actuator", "firing_angle"),
                        ("wrong_edit_applied", OrderedDict([("alpha_deg", 14.0), ("i_dc_A", 1290.0)])),
                        (
                            "cost",
                            "String abort + 22 min pole wait (task/efficiency); current still over cap (safety near-miss).",
                        ),
                    ]
                ),
            ),
            ("missed_window_s", 1320),
            ("delayed_surprise_s", 1320),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.tj.c (5.210 ms, 98.4 C)"),
                        ("loser", "enc.alpha.deg (5.470 ms, 18 deg)"),
                        ("margin_us", 260),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 260 us would still show 18 deg under no angle "
                            "cap; a correct gate binds IR to a full alpha hold (8 deg) either "
                            "way. The wrong MODIFY spent the IR win on an under-clamp.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5850),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the under-clamp (5.850 ms, tick 4). The "
                "22 min pole wait is delayed surprise, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        28,
        64,
        42,
        75,
        routing(
            "relay.ir.tj",
            "policy.alpha_nudge",
            [
                ("relay.ir.tj", "policy.alpha_nudge", 0.70),
                ("enc.alpha.deg", "policy.alpha_nudge", 0.22),
            ],
            "acetylcholine",
            0.08,
            "force_cap_stdp; ACh tags the (wrong) alpha_nudge bind at the IR win",
        ),
        excerpt,
        extra=kernel_extra(),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.48),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("alpha_nudge", 48, 0.50, 250.0, 6),
                    pop("alpha_hold", 48, 0.80, 20.0, 0),
                    pop("pop_ir_tj", 32, 0.55, 180.0, 3),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r24-137"),
            (
                "title",
                "WRONG-MODIFY at Fjord-Convert FC-12 / string T-19: I 1380 A and Tj 98.4 C read "
                "correctly; alpha clamp 18->14 deg is under-cap (under-clamp)",
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
                    "Wrong-modify / under-clamp. Sidecar arithmetic 1380 > 1200 is true; clamp "
                    "bound to alpha but 14 deg still predicts 1290 A. total -0.68 = -0.22 + "
                    "-0.18 + -0.24 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "hvdc-thyristor-valve",
                    [
                        "modify",
                        "wrong-gate",
                        "under-clamp",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct I>cap and Tj>cap read can still be a wrong "
                    "gate when executed alpha_deg=14 leaves i_dc_A over cap and routing.table[0].to "
                    "is policy.alpha_nudge.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_138():
    ticks = [
        tick(1635, 0.01, 0.04, 0.02, 0.01, 0.01),
        tick(4088, 0.02, 0.08, 0.03, 0.02, 0.01),
        tick(4201, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5088, 0.03, 0.14, 0.04, 0.04, 0.02),
        tick(5408, 0.02, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("pt.swivel.ctx", 1.205, 0.42),
        spike("ir.ch4.lel", 2.410, 0.58),
        spike("enc.boom.vel", 3.105, 0.51),
        spike("ir.ch4.lel", 4.088, 1.29),
        spike("enc.boom.vel", 4.201, 1.14),
        spike("ctrl.gate", 5.088, 1.02),
        spike("ir.ch4.lel", 6.880, 0.77),
        spike("pt.swivel.ctx", 8.440, 0.46),
        spike("enc.boom.vel", 11.020, 0.61),
        spike("ctrl.gate", 14.880, 0.85),
        spike("ir.ch4.lel", 22.400, 0.55),
        spike("pt.swivel.ctx", 30.110, 0.38),
        spike("enc.boom.vel", 38.200, 0.41),
        spike("ir.ch4.lel", 44.100, 0.49),
    ]
    excerpt = independent_excerpt(24138, 112, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Vessel V-2 sits on the Retort-Fen RF-HIL pad while an injected 3.20 bar chamber "
                "packet races a door-lock encoder that claims unlock-armed. PT 3.20 bar is over "
                "the 2.50 bar unlock cap; encoder-first would treat the lock as cleared. PT-first "
                "latches REJECT hold; the pad injects the PT packet 140-180 us before the door "
                "encoder sees the same latch motion.",
            ),
            ("domain", "autoclave-retort"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not unlock vessel V-2 unless chamber pressure <= 2.50 bar; keep the door "
                "locked until the injected packet clears.",
            ),
            ("t0_us", 1756843200000138),
            ("gate_latency_us", 1000),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.0, 4.32]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.chamber.bar 3.20 bar",
                                "enc.door.lock unlock-armed",
                            ],
                        ),
                        (
                            "semantics",
                            "PT-first latches REJECT hold (door locked); encoder-first would "
                            "commit unlock on a cleared-lock model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one chamber-PT slot versus door-lock encoder decode on this "
                            "HIL retort cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 113 us vs combined jitter ~45 us (PT 22 + encoder 23): 2.5x "
                            "over a 2.0x trust floor. Pad injects PT 140-180 us before the door "
                            "encoder (geometric lag, not a sensor fault); the unlock-armed packet "
                            "is still the loser in this 320 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "chamber pressure transducer, 50 Hz burst, 22 us jitter",
                    "door-lock encoder, 1 kHz, 23 us jitter",
                    "jacket RTD (context)",
                    "door proximity (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("unlock_cap_bar", 2.5),
                        ("observed_bar", 3.2),
                        ("proposed_unlock", True),
                        ("pt_inject_lead_us", [140, 180]),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. V-2 on the RF-HIL pad; door unlock armed; chamber 3.20 bar.",
                    "2. PT packet injected 140-180 us before door-encoder motion.",
                    "3. Jacket-RTD precursor at 1.635 ms.",
                    "4. Race window [4.000, 4.320] ms.",
                    "5. pt.chamber.bar 3.20 bar at 4.088 ms (winner).",
                    "6. enc.door.lock unlock-armed at 4.201 ms (loser by 113 us).",
                    "7. Gate at 5.088 ms: REJECT hold locked; do not commit unlock.",
                    "8. Packet remains in the chamber this cycle; cap held.",
                    "9. Pad recycle queued.",
                    "10. Delayed (pad_recycle_s=480): pad policy tags door-encoder clear as non-clearance vs PT.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "commit_door_unlock"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("unlock", True),
                        ("hold", False),
                        ("encoder_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("chamber_bar", 3.2),
                        ("unlock_cap_bar", 2.5),
                        ("unlock_armed", True),
                        ("race_margin_us", 113),
                        ("combined_jitter_us", 45),
                        ("pad_recycle_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes door unlock because the encoder looks like a cleared latch, "
                "treating PT 3.20 bar as a noisy jacket echo on the HIL pad.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Chamber PT 3.20 bar is over the 2.50 bar unlock cap. Door-lock encoder "
                "unlock-armed is not a pressure clearance. REJECT: hold locked; do not commit "
                "unlock. Wait for injected packet clear.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "chamber_bar",
                            OrderedDict(
                                [
                                    ("cap", 2.5),
                                    ("observed", 3.2),
                                    ("encoder_unlock_armed", True),
                                ]
                            ),
                        ),
                        (
                            "unlock",
                            OrderedDict(
                                [
                                    ("proposed", True),
                                    ("executed", False),
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
            ("name", "hold_door_locked"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("unlock", False),
                        ("hold", True),
                        ("encoder_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold locked; unlock cancelled. PT 3.20 bar > 2.50 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held V-2 locked. Injected pressure packet uncleared this cycle; "
                "unlock cap held. Door encoder was not treated as pressure clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("door", "held locked"),
                        ("packet", "still in chamber this cycle"),
                        ("encoder", "unlock-armed unused as clearance"),
                        ("mission", "unlock deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: PT was injected 140-180 us before door-encoder motion, yet chamber PT still won the 320 us race.",
                    "Delayed (pad_recycle_s=480): pad policy update forbids treating door-encoder clear as a pressure-clearance substitute.",
                ],
            ),
            ("pad_recycle_s", 480),
            ("delayed_surprise_s", 480),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.chamber.bar (4.088 ms, 3.20 bar)"),
                        ("loser", "enc.door.lock (4.201 ms, unlock-armed)"),
                        ("margin_us", 113),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 113 us inside the 320 us window would have "
                            "committed unlock with PT 3.20 bar > 2.50 cap. Order, not amplitude, "
                            "selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5088),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (5.088 ms, tick 4) as the hold "
                "locks in over the illegal slew.",
            ),
        ]
    )
    ras = raster_core(
        46,
        112,
        21,
        108,
        routing(
            "thalamic-relay.lng-lel",
            "spikenaut.policy.boom-hold",
            [
                ("relay.ir.lel", "policy.hold_reject", 0.66),
                ("relay.enc.boom", "policy.boom_go", 0.28),
                ("relay.pt.swivel", "policy.hold_reject", 0.12),
            ],
            "dopamine",
            0.20,
            "pre_post_stdp; DA at IR win tags hold_reject, reward at packet-still-in-cell",
        ),
        excerpt,
        extra=kernel_extra(),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 64, 0.50, 250.0, 5),
                    pop("boom_go", 64, 0.50, 50.0, 1),
                    pop("lel_veto", 32, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r24-138"),
            (
                "title",
                "Kelp-Jetty KJ-HIL / Murre-6: IR 1.80 %LEL beats boom encoder 0.12 m/s by 113 us; "
                "REJECT hold, do not commit",
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
                    "Clean REJECT. Task incomplete (packet uncleared); cap held. total 0.80 = "
                    "0.10 + 0.40 + 0.14 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "lng-unloading-arm",
                    [
                        "reject",
                        "hil",
                        "ir-lel",
                        "boom-encoder",
                        "dry-break-hold",
                    ],
                    "Teaches that a boom-encoder slew is not methane clearance when IR %LEL is "
                    "over the crawl cap.",
                    3,
                ),
            ),
        ]
    )


def record_139():
    ticks = [
        tick(2848, 0.05, 0.03, 0.02, 0.01, 0.01),
        tick(7120, 0.08, 0.05, 0.03, 0.02, 0.02),
        tick(7334, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(7500, 0.12, 0.10, 0.05, 0.04, 0.02),
        tick(7900, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(660000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("imu.att.ctx", 1.880, 0.45),
        spike("load.tow.kn", 3.210, 0.63),
        spike("dvl.xy.slip", 4.640, 0.57),
        spike("sonar.burial.ctx", 5.920, 0.49),
        spike("load.tow.kn", 7.120, 1.36),
        spike("dvl.xy.slip", 7.334, 1.17),
        spike("ctrl.gate", 7.500, 1.01),
        spike("load.tow.kn", 9.880, 0.78),
        spike("sonar.burial.ctx", 12.440, 0.52),
        spike("dvl.xy.slip", 16.210, 0.64),
        spike("imu.att.ctx", 20.800, 0.47),
        spike("load.tow.kn", 23.050, 0.59),
    ]
    excerpt = independent_excerpt(24139, 56, 24000, 14, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("tow_speed_m_s", 0.40),
            ("burial_m", 1.8),
            ("tow_kN", 48.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Cuttle-2 ploughs a 1.8 m burial trench across Skerries-Trench ST-8 with tow "
                "tension 48.0 kN, 12 kN under the 60.0 kN cap, when a DVL smear of 0.18 m/s looks "
                "like an overload. Load-cell-first confirms the already-legal 0.40 m/s tow; "
                "DVL-first would have treated the smear as a share-stall and looked for a clamp "
                "the trim does not need.",
            ),
            ("domain", "subsea-cable-plough"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold 1.8 m burial at 0.40 m/s with tow tension <= 60.0 kN across the ST-8 "
                "crossing.",
            ),
            ("t0_us", 1756843200000139),
            ("gate_latency_us", 380),
            ("race_window_us", 400),
            ("race_window_rel_ms", [7.0, 7.40]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "load.tow.kn 48.0 kN",
                                "dvl.xy.slip 0.18 m/s smear",
                            ],
                        ),
                        (
                            "semantics",
                            "Load-cell-first confirms the already-legal 0.40 m/s tow; DVL-first "
                            "would treat the smear as a share-stall and look for an extra clamp.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one tow-load-cell sample versus DVL bottom-track decode on "
                            "this plough bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 214 us vs combined jitter 68 us (load-cell 30 + DVL 38): 3.1x "
                            "over a 2.0x trust floor. Reversing order by < 214 us would not make "
                            "the proposed tow illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "tow load-cell, 2 kHz, 30 us jitter",
                    "DVL bottom track, 38 us jitter",
                    "burial sonar (context)",
                    "IMU attitude (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("tow_cap_kN", 60.0),
                        ("observed_tow_kN", 48.0),
                        ("proposed_speed_m_s", 0.40),
                        ("burial_m", 1.8),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "U-RANS + Mohr-Coulomb plough, seed 24; 0.40 m/s tow, 1.8 m burial; "
                            "NOT actuator-disk",
                        ),
                        (
                            "fidelity_limits",
                            "No plough-share flex; DVL smear is a rigid-bed sediment sheet. "
                            "Raster is kernelized events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Cuttle-2 at 1.8 m burial on ST-8; tow 48.0 kN.",
                    "2. Proposed 0.40 m/s already 12 kN under the 60.0 kN cap.",
                    "3. IMU precursor at 2.848 ms.",
                    "4. Race window [7.000, 7.400] ms.",
                    "5. load.tow.kn 48.0 kN at 7.120 ms (winner).",
                    "6. dvl.xy.slip 0.18 m/s at 7.334 ms (loser by 214 us).",
                    "7. Gate at 7.500 ms: ACCEPT; executed identical to proposed.",
                    "8. Tow 48.0 kN; burial 1.8 m held.",
                    "9. Crossing completed as a single plough.",
                    "10. Delayed (survey_s=660): policy update requires load-cell tags in DVL fusion.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "trench_tow_legal"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("tow_kN", 48.0),
                        ("tow_cap_kN", 60.0),
                        ("dvl_slip_m_s", 0.18),
                        ("proposed_speed_m_s", 0.40),
                        ("burial_m", 1.8),
                        ("race_margin_us", 214),
                        ("combined_jitter_us", 68),
                        ("survey_s", 660),
                    ]
                ),
            ),
            (
                "basis",
                "Planner already includes a 0.40 m/s tow that keeps 48.0 kN under the 60.0 kN "
                "cap and 1.8 m burial. Unclamped 0.70 m/s is not the proposal.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Proposed tow already 0.40 m/s; observed 48.0 kN <= 60.0 kN floor-cap; burial "
                "1.8 m held. Load-cell-first confirms the trim. ACCEPT executed identical to "
                "proposed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tow_kN",
                            OrderedDict(
                                [
                                    ("cap", 60.0),
                                    ("observed", 48.0),
                                ]
                            ),
                        ),
                        (
                            "speed_m_s",
                            OrderedDict(
                                [
                                    ("proposed", 0.40),
                                    ("executed", 0.40),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 214),
                                    ("combined_jitter_us", 68),
                                    ("ratio", 3.15),
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
            ("name", "trench_tow_legal"),
            ("parameters", OrderedDict(params.items())),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed_action; 0.40 m/s tow and 1.8 m burial "
                "held for the ST-8 crossing.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Cuttle-2 cleared ST-8 with tow 48.0 kN and burial 1.8 m. Load-cell-first "
                "confirmed an already-legal tow; no further clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("plough", "single-body intact; tow 48.0 kN"),
                        ("burial", "1.8 m held"),
                        ("trim", "0.40 m/s tow held"),
                        ("crossing", "passed"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The DVL smear was a rigid-bed sediment sheet in the U-RANS + Mohr-Coulomb solver, not a share-stall.",
                    "Delayed (survey_s=660): policy update requiring load-cell tags in DVL fusion so a later smear cannot be fused without tension context.",
                ],
            ),
            ("survey_s", 660),
            ("delayed_surprise_s", 660),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "load.tow.kn (7.120 ms, 48.0 kN)"),
                        ("loser", "dvl.xy.slip (7.334 ms, 0.18 m/s)"),
                        ("margin_us", 214),
                        (
                            "counterfactual_if_reversed",
                            "DVL-first by < 214 us inside the 400 us window would have delayed "
                            "confirmation of the same legal tow; it would not have required an "
                            "extra speed clamp. Unclamped 0.70 m/s was never proposed.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7500),
            (
                "reward_inflection_note",
                "Safety and task_progress step up at the ACCEPT gate (7.500 ms, tick 4) as the "
                "already-legal tow locks in.",
            ),
        ]
    )
    ras = raster_core(
        24,
        56,
        38,
        51,
        routing(
            "thalamic-relay.tow-load",
            "spikenaut.policy.tow-accept",
            [
                ("relay.load.tow", "policy.tow_go", 0.61),
                ("relay.dvl.slip", "policy.tow_clamp", 0.28),
                ("relay.sonar.burial", "policy.tow_go", 0.21),
            ],
            "serotonin",
            0.30,
            "pre_post_stdp; 5-HT at load-cell win tags tow_go, reward at crossing-clear",
        ),
        excerpt,
        extra=kernel_extra(),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("tow_go", 40, 0.50, 280.0, 4),
                    pop("tow_clamp", 40, 0.50, 70.0, 1),
                    pop("slip_ctx", 24, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r24-139"),
            (
                "title",
                "Skerries-Trench ST-8 / Cuttle-2: tow 48.0 kN beats DVL smear 0.18 m/s by 214 us; "
                "ACCEPT already-legal 0.40 m/s burial tow",
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
                    "Clean ACCEPT of an already-legal plough tow. total 1.02 = 0.40 + 0.28 + "
                    "0.16 + 0.10 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "subsea-cable-plough",
                    [
                        "accept",
                        "simulated",
                        "tow-vs-dvl",
                        "already-legal-tow",
                        "mohr-coulomb",
                    ],
                    "Teaches a fusion head that a DVL sediment smear can lose to a legal tow "
                    "load-cell without a further speed clamp.",
                    4,
                ),
            ),
        ]
    )


def record_140():
    ticks = [
        tick(2018, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(5044, 0.09, 0.07, 0.04, 0.03, 0.02),
        tick(5188, 0.06, 0.05, 0.03, 0.02, 0.01),
        tick(5344, 0.14, 0.12, 0.06, 0.04, 0.02),
        tick(5644, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(420000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.cart.ctx", 1.088, 0.44),
        spike("faraday.i.ua", 2.410, 0.60),
        spike("ir.target.face", 3.220, 0.53),
        spike("tc.water.ctx", 4.018, 0.46),
        spike("faraday.i.ua", 5.044, 1.27),
        spike("ir.target.face", 5.188, 1.09),
        spike("ctrl.gate", 5.344, 0.98),
        spike("faraday.i.ua", 6.880, 0.80),
        spike("ir.target.face", 8.440, 0.64),
        spike("tc.water.ctx", 11.020, 0.48),
        spike("ctrl.gate", 14.880, 0.86),
        spike("enc.cart.ctx", 18.210, 0.40),
    ]
    excerpt = independent_excerpt(24140, 48, 22000, 13, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("beam_uA", 42.0),
            ("coolant_l_min", 12.0),
            ("target", "I-123"),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Target-Cart TC-3 on Iodine-Well IW-5 holds a Faraday-cup 42 uA beam against a "
                "50 uA cap while the IR face still reads 68 C, 22 C under a 90 C face cap. "
                "Faraday-first selects the already-legal 42 uA hold; IR-first would treat 68 C as "
                "a face excursion and dump the beam.",
            ),
            ("domain", "cyclotron-target"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Irradiate the I-123 target at <= 50 uA with face temperature <= 90 C and leave "
                "the cart latched.",
            ),
            ("t0_us", 1756843200000140),
            ("gate_latency_us", 300),
            ("race_window_us", 300),
            ("race_window_rel_ms", [5.0, 5.30]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "faraday.i.ua 42 uA",
                                "ir.target.face 68 C",
                            ],
                        ),
                        (
                            "semantics",
                            "Faraday-first latches 42 uA hold under the 50 uA cap; IR-first "
                            "latches a beam dump on a 68 C face that is still under 90 C.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one Faraday-cup integrator slot versus IR face pyrometer "
                            "on this target-cart cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 144 us vs combined jitter 54 us (Faraday 24 + IR 30): 2.7x "
                            "over a 2.0x trust floor. Reversing order by < 144 us would have "
                            "dumped a legal 42 uA beam.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "Faraday-cup integrator, 24 us jitter",
                    "target-face IR pyrometer, 30 us jitter",
                    "cooling-water RTD (context)",
                    "cart encoder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("beam_cap_uA", 50.0),
                        ("observed_beam_uA", 42.0),
                        ("face_cap_C", 90.0),
                        ("observed_face_C", 68.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. TC-3 latched on IW-5; I-123 target in beam.",
                    "2. Faraday 42 uA; IR face 68 C under 90 C cap.",
                    "3. Cart-enc precursor at 2.018 ms.",
                    "4. Race window [5.000, 5.300] ms.",
                    "5. faraday.i.ua 42 uA at 5.044 ms (winner).",
                    "6. ir.target.face 68 C at 5.188 ms (loser by 144 us).",
                    "7. Gate at 5.344 ms: ACCEPT 42 uA hold, 12 L/min coolant.",
                    "8. Face 68 C; beam 42 uA under 50 uA cap.",
                    "9. Irradiation continues; cart remains latched.",
                    "10. Delayed (cooldown_s=420): sister cart TC-4 Faraday-authoritative under face-present mode.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_beam_42"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("beam_uA", 42.0),
                        ("beam_cap_uA", 50.0),
                        ("face_C", 68.0),
                        ("face_cap_C", 90.0),
                        ("race_margin_us", 144),
                        ("combined_jitter_us", 54),
                        ("cooldown_s", 420),
                    ]
                ),
            ),
            (
                "basis",
                "Faraday 42 uA is under the 50 uA cap and IR face 68 C is under the 90 C cap; "
                "42 uA hold with 12 L/min coolant is already legal.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Faraday 42 uA won by 144 us; commanded 42 uA is 8 uA under the 50 uA cap; face "
                "68 C keeps the 90 C floor. ACCEPT the hold. An IR-led dump would abort a legal "
                "irradiation.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "beam_uA",
                            OrderedDict(
                                [
                                    ("cap", 50.0),
                                    ("commanded", 42.0),
                                ]
                            ),
                        ),
                        (
                            "face_C",
                            OrderedDict(
                                [
                                    ("cap", 90.0),
                                    ("observed", 68.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 144),
                                    ("combined_jitter_us", 54),
                                    ("ratio", 2.67),
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
            ("name", "hold_beam_42"),
            ("parameters", OrderedDict(params.items())),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed_action; 42 uA hold and 12 L/min coolant "
                "held for the I-123 irradiation.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "TC-3 completed the I-123 hold with beam 42 uA and face 68 C; target unharmed. "
                "Faraday-authoritative under face-present mode confirmed.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("beam", "42 uA held; under 50 uA cap"),
                        ("face", "68 C; under 90 C cap"),
                        ("cart", "latched; irradiation continues"),
                        ("near_miss_log", "none"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 68 C IR face was not a calibration fault: a water-film glint can raise apparent face temperature while Faraday current stays legal.",
                    "Delayed (cooldown_s=420): sister cart TC-4 logged the same Faraday-vs-IR disagreement; vault policy flipped Faraday-authoritative before the next I-123 rotation.",
                ],
            ),
            ("cooldown_s", 420),
            ("delayed_surprise_s", 420),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "faraday.i.ua (5.044 ms, 42 uA)"),
                        ("loser", "ir.target.face (5.188 ms, 68 C)"),
                        ("margin_us", 144),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 144 us inside the 300 us window would have dumped a "
                            "legal 42 uA beam on a 68 C face that is still under the 90 C cap.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5344),
            (
                "reward_inflection_note",
                "Safety and efficiency both step up at the ACCEPT gate (5.344 ms, tick 4) as "
                "the hold locks in over a false dump.",
            ),
        ]
    )
    ras = raster_core(
        22,
        48,
        48,
        51,
        routing(
            "thalamic-relay.faraday-beam",
            "spikenaut.policy.beam-go",
            [
                ("relay.faraday.i", "policy.beam_go", 0.63),
                ("relay.ir.face", "policy.ir_hold", 0.29),
                ("relay.tc.water", "policy.beam_go", 0.14),
            ],
            "dopamine",
            0.12,
            "pre_post_stdp; DA at Faraday win tags beam_go, reward at irradiation-hold",
        ),
        excerpt,
        extra=kernel_extra(),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.30),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("beam_go", 32, 0.50, 280.0, 3),
                    pop("ir_hold", 32, 0.50, 80.0, 1),
                    pop("face_ctx", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r24-140"),
            (
                "title",
                "Iodine-Well IW-5 / Target-Cart TC-3: Faraday 42 uA beats IR face 68 C by 144 us; "
                "ACCEPT already-legal 42 uA hold",
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
                    "Clean ACCEPT. Faraday 42 uA < 50 uA cap; IR face 68 C < 90 C cap. total "
                    "1.18 = 0.44 + 0.34 + 0.20 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "cyclotron-target",
                    [
                        "accept",
                        "cyclotron",
                        "faraday-vs-ir",
                        "already-legal-beam",
                        "designed",
                    ],
                    "Teaches that an IR face glint can lose to a Faraday-cup current when both "
                    "reads are under cap; reversing 144 us would have dumped a legal beam.",
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
    if set(domains) & BANNED_DOMAINS:
        issues.append(f"banned domains {set(domains) & BANNED_DOMAINS}")
    blob_all = " ".join(descs + [r.get("title", "") for r in records])
    for frag in BANNED_PLANT_FRAGMENTS:
        if frag in blob_all:
            issues.append(f"cloned plant fragment {frag}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r24-137":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r24-138"]:
        issues.append(f"hil set {hil}")
    ids = [r["id"] for r in records]
    if ids != [f"ttf-r24-{n}" for n in range(136, 141)]:
        issues.append(f"ids {ids}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if (
        decisions.count("ACCEPT") != 2
        or decisions.count("MODIFY") != 2
        or decisions.count("REJECT") != 1
    ):
        issues.append(f"gate mix {decisions}")
    for rec in records:
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rec['id']} training_ready present")
        if "outputs/raw" in blob:
            issues.append(f"{rec['id']} mentions outputs/raw")
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
        if rec["id"] == "ttf-r24-136":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("136 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("136 inflection outside window")
        elif overlap >= 0.8:
            issues.append(f"{rec['id']} excerpt overlap {overlap:.2f}")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_times = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_times:
            issues.append(f"{rec['id']} inflection {inf} not a tick")
        if len(rec["reward_components"]["ticks"]) != 6:
            issues.append(f"{rec['id']} tick count")
        tick6 = rec["reward_components"]["ticks"][5]["t_us"]
        sidecar = rec["future_outcome"].get("delayed_surprise_s")
        if sidecar is None:
            issues.append(f"{rec['id']} missing delayed_surprise_s")
        elif tick6 != int(round(sidecar * 1e6)):
            issues.append(f"{rec['id']} tick6 {tick6} != delayed_surprise_s {sidecar}")
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rec['id']} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rec['id']} gate_snn decision mismatch")
        if rec["meta"]["round"] != 24:
            issues.append(f"{rec['id']} meta.round")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            issues.append(f"{rec['id']} rights")
        if rec["meta"]["rights"]["linear_issue"] != "RM-793":
            issues.append(f"{rec['id']} linear_issue")
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
        if rec["id"] == "ttf-r24-136" and rec["reward_components"]["total"] >= 0:
            issues.append("136 partnered-neg total not negative")
        if rec["id"] == "ttf-r24-137":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["i_dc_A"] > ev["i_cap_A"]):
                issues.append("137 i_dc not over cap")
            if rec["executed_action"]["parameters"]["i_dc_A"] <= ev["i_cap_A"]:
                issues.append("137 executed I not still over cap")
            tos = [row["to"] for row in rec["raster"]["routing"]["table"]]
            if "policy.alpha_hold" in tos:
                issues.append("137 routing still has alpha_hold")
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for popu in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in popu:
                exp = round(popu["neurons"] * popu["mean_rate_hz"] * dw_s)
                if abs(popu["spikes"] - exp) > 1:
                    issues.append(
                        f"{rec['id']} gate_snn {popu['name']} spikes {popu['spikes']} vs {exp}"
                    )
        if not (20 <= rec["raster"]["window_ms"] <= 50):
            issues.append(f"{rec['id']} window_ms")
        if len(rec["raster"]["excerpt"]) > 16:
            issues.append(f"{rec['id']} excerpt too long")
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= rec["raster"]["window_ms"] * 1000):
                issues.append(f"{rec['id']} excerpt t_us {item['t_us']}")
            if not (0 <= item["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rec['id']} neuron_id {item['neuron_id']}")
    return issues, jmax


NOTES = """# Thalamic Trajectory Factory — NOTES-r24

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- IDs: `ttf-r24-136` … `ttf-r24-140`
- Domains this batch: `lyophilizer-shelf`, `hvdc-thyristor-valve`, `lng-unloading-arm`, `subsea-cable-plough`, `cyclotron-target`

These five domain slugs sit outside the r12–r16 occupancy set and outside the r15/r17/r19 planned slugs. All five plants are invented. Do not restack r12–r16 plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Nacre-Well, Quern-Forge, Tinder-Box, Whimbrel-Stack, Cinder-Loft, Suture-Isle, Kiln-Spur, Oxbow-Switch, Pitch-Kettle, Shale-Quay, Polder-Rye, Flint-Mask, Gyre-Tokamak, Quarry-Bowl, Orpiment).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r24-136 | lyophilizer-shelf | MODIFY | correct | designed | **−0.42** | process-correct shelf clamp; vial-14 crack inside 40 ms raster; independent LIF |
| ttf-r24-137 | hvdc-thyristor-valve | MODIFY | **incorrect (wrong-modify / under-clamp)** | designed | −0.68 | I 1380 A and Tj 98.4 C reads are correct; alpha 18→14 deg still leaves 1290 A over 1200 A |
| ttf-r24-138 | lng-unloading-arm | REJECT | correct | hil | +0.80 | IR 1.80 %LEL beats boom encoder 0.12 m/s; hold, do not slew |
| ttf-r24-139 | subsea-cable-plough | ACCEPT | correct | simulated | +1.02 | tow 48.0 kN vs DVL smear 0.18 m/s; proposed 0.40 m/s already legal |
| ttf-r24-140 | cyclotron-target | ACCEPT | correct | designed | +1.18 | Faraday 42 uA vs IR face 68 C; proposed 42 uA already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (under-clamp), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Kelp-Jetty dry-break pad). Jaccard on `state.description` reported by the generator.

## Wrong-modify / under-clamp

**ttf-r24-137** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). This is not r13 J2-vs-J6 (wrong axis), not r14 AC-precharge-vs-DC (wrong loop), not r15 clamp-too-late, not r16 reticle-vs-wafer (wrong-reject).

Fjord-Convert FC-12 / string T-19 reads junction IR **98.4 C** against an **85.0 C** cap and DC **1380 A** against a **1200 A** cap. Firing angle is the correct actuator. Sidecar arithmetic `1380 > 1200` is true. A timely full clamp is alpha **18 → 8 deg** (predicted 1080 A). A weak supervisor applies the same actuator but only **18 → 14 deg**, leaving **1290 A** over cap. Convictable without HVDC physics: `evidence.i_dc_A > evidence.i_cap_A`, `executed_action.parameters.i_dc_A > i_cap_A`, `executed alpha_deg=14` ≠ `correct_alpha_deg=8`, `raster.routing.table` sends `relay.ir.tj` → `policy.alpha_nudge` (weight 0.70) with no positive weight to `policy.alpha_hold`, and `gate_snn` has `alpha_nudge` above threshold while `alpha_hold` is not. Recovery: MODIFY alpha 18 → 8 deg, I 1380 → 1080 A. Cost: string abort + 22 min pole wait (`missed_window_s=1320`).

## Partnered-negative in-window (136)

**ttf-r24-136** is the partnered negative: process-correct MODIFY (shelf held −3.6 C < 0.00 C cap) while the world still charges. Safety −0.62 prices the vial-14 crack at **24.200 ms**; `task_progress` stays +0.36 because the clamp completed. Inflection `t_us=24200` is tick 5 and is **inside** the 40 ms raster (`24200 ≤ 40000`). Named un-netted loss: 19 min cake dump (`abort_s=1140`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 24136, stim `[23200, 26200]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.crack` 23.2–26.2 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s` / `missed_window_s` / `pad_recycle_s` / `survey_s` / `cooldown_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 136 | 6 | +0.36 | −0.62 | −0.16 | +0.04 | −0.04 | −0.42 | 5 (24200) |
| 137 | 6 | −0.22 | −0.18 | −0.24 | −0.10 | +0.06 | −0.68 | 4 (5850) |
| 138 | 6 | +0.10 | +0.40 | +0.14 | +0.10 | +0.06 | +0.80 | 4 (5088) |
| 139 | 6 | +0.40 | +0.28 | +0.16 | +0.10 | +0.08 | +1.02 | 4 (7500) |
| 140 | 6 | +0.44 | +0.34 | +0.20 | +0.12 | +0.08 | +1.18 | 4 (5344) |

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 136 | lyophilizer-shelf | 80 | 25 | 40 | 80 | 1840 | 0.001840 |
| 137 | hvdc-thyristor-valve | 64 | 42 | 28 | 75 | 1725 | 0.001725 |
| 138 | lng-unloading-arm | 112 | 21 | 46 | 108 | 2484 | 0.002484 |
| 139 | subsea-cable-plough | 56 | 38 | 24 | 51 | 1173 | 0.001173 |
| 140 | cyclotron-target | 48 | 48 | 22 | 51 | 1173 | 0.001173 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator, `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-136 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (136). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is a densification of r14/r16, not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 139/140 ACCEPT are already-legal proposals confirmed by race order; a later round could pair an ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. If a later round returns to the 8-item pool, sit out the r12 five again. A remaining unused wrong-MODIFY subclass is **wrong-phase of a cyclic process** (not under-clamp, not wrong-axis, not clamp-too-late). Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 21.0%
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
        BATCH_PATH, "batch-r24.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r24.jsonl:{i}", factory_staging=True)
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
    if "outputs/raw" in str(BATCH_PATH) or "outputs/raw" in str(NOTES_PATH):
        raise SystemExit("refusing to write outputs/raw/")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_136(), record_137(), record_138(), record_139(), record_140()]
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



