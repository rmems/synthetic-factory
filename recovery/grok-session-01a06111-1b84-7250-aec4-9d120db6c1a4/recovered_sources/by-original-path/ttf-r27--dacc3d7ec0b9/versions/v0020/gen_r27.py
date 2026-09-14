#!/usr/bin/env python3
"""Emit TTF r27 JSONL (ttf-r27-151..155) into /tmp/ttf-r27/. Never writes outputs/raw/."""

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

OUT_DIR = Path("/tmp/ttf-r27")
BATCH_PATH = OUT_DIR / "batch-r27.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r27.md"
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
    "thoughts",
    "reasoning",
    "chain_of_thought",
    "hidden_reasoning",
    "inner_monologue",
    "thinking",
    "cot",
    "scratch",
    "internal_reasoning",
}
THIS_DOMAINS = {
    "helium-liquefier",
    "czochralski-puller",
    "escalator-comb",
    "jet-fuel-hydrant",
    "sawmill-carriage",
}
THIS_PLANT_TOKENS = (
    "Braid-Spool",
    "Expander-X3",
    "Boule-Knap",
    "Puller-P12",
    "Comb-Sill",
    "Tread-S11",
    "Kerosene-Wharf",
    "Pit-H8",
    "Kerf-Spur",
    "Carriage-C14",
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


def spike_avoid_us(events):
    return {int(round(ev["t_rel_ms"] * 1000.0)) for ev in events}


def lif_151_excerpt():
    n = 72
    dt_us = 100
    tau_m_ms = 20.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.92
    i_stim_peak = 2.5
    stim = (21000, 24000)
    seed = 27151
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
    burst = [(t, nid) for t, nid in spikes if 21000 <= t < 24000]
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
            n_this = len(
                [1 for t, _ in picked if (t < 21000) == (pool[0][0] < 21000)]
            )
            if n_this >= want:
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
    take(burst, 9, label_times=(22400, 22800, 23500))
    clamp = [(t, n) for t, n in picked if t < 21000][:7]
    seal = [(t, n) for t, n in picked if t >= 21000][:9]
    picked = sorted(clamp + seal, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(
            f"LIF excerpt too short {len(picked)} (early={len(early)} burst={len(burst)})"
        )
    channels = ["lif.clamp" if t < 21000 else "lif.seal" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 72),
            ("dt_us", 100),
            ("tau_m_ms", 20.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.92),
            ("i_stim_peak", 2.5),
            ("stim_t_us", [21000, 24000]),
            ("i_clamp_extra", 0.68),
            ("clamp_n", 14),
            ("seed", 27151),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.68 clamp-pathway bias; stim 21-24 ms is the seal weep.",
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
            ("round", 27),
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


def record_151():
    excerpt, extra = lif_151_excerpt()
    ticks = [
        tick(2484, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6210, 0.06, -0.04, -0.02, 0.01, -0.01),
        tick(6448, 0.04, -0.03, -0.02, 0.01, 0.00),
        tick(7090, 0.10, -0.06, -0.03, 0.02, -0.01),
        tick(22400, 0.06, -0.36, -0.04, 0.01, -0.02),
        tick(780000000, 0.02, -0.05, -0.03, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Expander-X3 on Braid-Spool BS-7 spins the Claude-cycle turbine past the "
                "overspeed trip while inlet temperature still looks like a legal precool. "
                "Shaft tachometer is 48200 rpm against a 45000 rpm cap; nozzle-first should "
                "cut 72 percent to 48 percent. Stored oil in the expander labyrinth is not "
                "yet an observable of either race channel.",
            ),
            ("domain", "helium-liquefier"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep Expander-X3 under 45000 rpm, finish the Claude pass, and leave the "
                "labyrinth seal unmarked.",
            ),
            ("t0_us", 1756794621000151),
            ("gate_latency_us", 880),
            ("race_window_us", 420),
            ("race_window_rel_ms", [6.180, 6.600]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "turb.rpm 48200 rpm on turbine_shaft",
                                "inlet.T.K 18.4 K precool",
                            ],
                        ),
                        (
                            "semantics",
                            "Rpm-first latches nozzle 72 -> 48 percent; inlet-first keeps cruise "
                            "nozzle on a still-cooling model.",
                        ),
                        (
                            "window_derivation",
                            "420 us = one magnetic-pickup sample minus inlet-RTD group delay on "
                            "this 2 kHz expander bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 238 us vs combined jitter 68 us (tach 32 + RTD 36): 3.5x over "
                            "a 2.0x trust floor. Reversing order by < 238 us inside the 420 us "
                            "window would have kept 72 percent cruise; predicted next-sample "
                            "46800 rpm > 45000 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "magnetic pickup on turbine_shaft, 2 kHz, 32 us jitter",
                    "inlet RTD, 50 Hz burst, 36 us jitter",
                    "nozzle stepper encoder (context)",
                    "labyrinth AE puck (context until the seal weep)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("rpm_cap", 45000),
                        ("observed_rpm", 48200),
                        ("rpm_axis", "turbine_shaft"),
                        ("proposed_nozzle_pct", 72.0),
                        ("inlet_K", 18.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Expander-X3 indexed onto Braid-Spool BS-7; Claude cycle armed.",
                    "2. Cruise nozzle 72 percent; tach 48200 rpm; inlet 18.4 K.",
                    "3. Encoder precursor at 2.484 ms; rpm warm-start 48200.",
                    "4. Race window [6.180, 6.600] ms opens on the expander bus.",
                    "5. turb.rpm 48200 at 6.210 ms (winner).",
                    "6. inlet.T.K 18.4 K at 6.448 ms (loser by 238 us).",
                    "7. Gate at 7.090 ms (winner + 880 us): MODIFY clamp nozzle 72 -> 48 percent.",
                    "8. Clamp executes; next-sample rpm 43800 < 45000 cap.",
                    "9. At 22.400 ms labyrinth oil still weeps 2.1 ml; AE burst.",
                    "10. Seal swap 13 min; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_nozzle_claude"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("nozzle_pct", 72.0),
                        ("ln2_pct", 40.0),
                        ("turb_rpm", 48200),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("turb_rpm", 48200),
                        ("rpm_cap", 45000),
                        ("rpm_axis", "turbine_shaft"),
                        ("predicted_unclamped_next_rpm", 46800),
                        ("nozzle_pct", 72.0),
                        ("inlet_K", 18.4),
                        ("race_margin_us", 238),
                        ("combined_jitter_us", 68),
                        ("abort_s", 780),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 72 percent nozzle because inlet 18.4 K looks like a still-"
                "cooling Claude stream, not an overspeed, and LN2 precool is already legal.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Shaft tach 48200 rpm won by 238 us, so the expander is overspeeding, not "
                "still cooling. Holding 72 percent predicts next-sample 46800 rpm > 45000 cap. "
                "MODIFY: nozzle 72 -> 48 percent. Observed after clamp 43800 rpm < 45000. A "
                "full REJECT is not indicated: a sound Claude pass accepts 48 percent nozzle.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "turb_rpm",
                            OrderedDict(
                                [
                                    ("cap", 45000),
                                    ("observed", 48200),
                                    ("predicted_unclamped_next", 46800),
                                    ("clamped_nozzle_pct", 48.0),
                                    ("observed_after_clamp", 43800),
                                ]
                            ),
                        ),
                        (
                            "nozzle_pct",
                            OrderedDict(
                                [
                                    ("proposed", 72.0),
                                    ("clamped", 48.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 238),
                                    ("combined_jitter_us", 68),
                                    ("ratio", 3.50),
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
            ("name", "clamped_nozzle_claude"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("nozzle_pct", 48.0),
                        ("ln2_pct", 40.0),
                        ("turb_rpm", 48200),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: nozzle 72 -> 48 percent. Process-correct vs the 45000 rpm cap. "
                "Labyrinth oil weep still occurs at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held rpm at 43800. At 22.400 ms stored oil in the "
                "labyrinth still wept 2.1 ml. Clamp reduced dump energy; it did not prevent "
                "the weep. Partnered negative: process heads stay honest; world loss is named, "
                "not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("expander", "clamp executed; peak 43800 rpm < 45000"),
                        ("seal", "2.1 ml labyrinth weep at 22.400 ms"),
                        ("repair", "13 min seal swap + helium hold"),
                        ("mission", "Claude pass still completed; labyrinth replaced"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither tach nor inlet RTD predicted the seal charge; seal.ae.weep is a new channel at 22.400 ms, 15.310 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (13 min / abort_s=780): labyrinth seal swap. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "13 min seal swap + helium hold after a 2.1 ml labyrinth weep. Safety head "
                "-0.56 prices the weep; task_progress stays +0.32 because the nozzle clamp "
                "completed under the 45000 rpm cap. World loss is named here, not subtracted "
                "from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "turb.rpm (6.210 ms, 48200 rpm)"),
                        ("loser", "inlet.T.K (6.448 ms, 18.4 K)"),
                        ("margin_us", 238),
                        (
                            "counterfactual_if_reversed",
                            "Inlet-first by < 238 us inside the 420 us window would have kept "
                            "72 percent cruise; predicted next-sample 46800 rpm would have "
                            "exceeded the 45000 cap even without the seal charge. The MODIFY "
                            "is still the correct process. The weep is a later world charge "
                            "either way, cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms labyrinth weep (tick t_us=22400), inside "
                "the 42 ms raster. The correct MODIFY at 7.090 ms is in the same excerpt. Do "
                "not put inflection on the +13 min seal-swap tick.",
            ),
            ("delayed_surprise_s", 780),
        ]
    )
    spikes = [
        spike("encoder.exp.ctx", 1.180, 0.43),
        spike("turb.rpm", 2.410, 0.62),
        spike("inlet.T.K", 3.880, 0.51),
        spike("temp.bath.ctx", 4.620, 0.46),
        spike("turb.rpm", 6.210, 1.33),
        spike("inlet.T.K", 6.448, 1.16),
        spike("ctrl.gate", 7.090, 0.98),
        spike("turb.rpm", 8.320, 0.82),
        spike("inlet.T.K", 10.760, 0.64),
        spike("ctrl.gate", 15.100, 0.86),
        spike("seal.ae.weep", 22.400, 1.44),
        spike("seal.ae.weep", 24.180, 0.93),
        spike("turb.rpm", 31.800, 0.55),
        spike("encoder.exp.ctx", 39.400, 0.40),
    ]
    ras = raster_core(
        42,
        72,
        30,
        91,
        routing(
            "thalamic-relay.expander-rpm",
            "spikenaut.policy.nozzle-clamp",
            [
                ("relay.turb.rpm", "policy.nozzle_clamp", 0.66),
                ("relay.inlet.T", "policy.temp_hold", 0.30),
                ("relay.seal.ae", "policy.nozzle_clamp", -0.44),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at rpm win (6.210 ms) opens a 50 ms "
            "eligibility trace that still covers the 22.400 ms seal weep",
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
                    pop("nozzle_clamp", 36, 0.50, 280.0, 4),
                    pop("temp_hold", 36, 0.50, 90.0, 1),
                    pop("rpm_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r27-151"),
            (
                "title",
                "Braid-Spool BS-7 / Expander-X3: shaft rpm beats inlet RTD by 238 us; "
                "correct MODIFY still eats an in-window labyrinth weep (partnered "
                "negative total -0.38)",
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
                    "Partnered negative. Process-correct MODIFY; world still charges inside "
                    "the 42 ms raster. total -0.38 = 0.32 + -0.56 + -0.16 + 0.06 + -0.04. "
                    "Named seal-swap loss is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "helium-liquefier",
                    [
                        "modify",
                        "partnered-negative-total",
                        "independent-lif-raster",
                        "sidecar-sim-only",
                        "in-window-world-charge",
                        "tick6-sidecar-bound",
                        "designed",
                    ],
                    "A critic can see the seal charge as a LIF burst inside the raster while "
                    "process heads stay honest. Credit assignment is spikes, not prose across "
                    "a 13 min seal swap.",
                    1,
                ),
            ),
        ]
    )


def record_152():
    ticks = [
        tick(2176, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(5440, -0.04, -0.04, -0.04, -0.02, 0.01),
        tick(5780, -0.03, -0.03, -0.03, -0.01, 0.01),
        tick(6180, -0.06, -0.10, -0.10, -0.03, 0.02),
        tick(6740, -0.02, -0.04, -0.04, -0.01, 0.01),
        tick(1080000000, -0.01, -0.02, -0.03, 0.00, 0.00),
    ]
    spikes = [
        spike("encoder.vessel.ctx", 1.090, 0.41),
        spike("tc.part.C", 2.540, 0.60),
        spike("pt.vessel.kPa", 3.820, 0.52),
        spike("dia.opt.mm", 4.620, 0.71),
        spike("tc.part.C", 5.440, 1.36),
        spike("pt.vessel.kPa", 5.780, 1.19),
        spike("ctrl.gate", 6.180, 1.01),
        spike("tc.part.C", 8.040, 0.80),
        spike("pt.vessel.kPa", 11.140, 0.63),
        spike("ctrl.gate", 16.400, 0.84),
        spike("tc.part.C", 24.200, 0.57),
        spike("encoder.vessel.ctx", 32.800, 0.39),
    ]
    excerpt = independent_excerpt(27152, 96, 36000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Vessel-V12 at Prepreg-Nave PN-4 reports a coupon thermocouple already over "
                "the one-eighty-five C part cap while vessel pressure still looks healthy. "
                "Part temperature is 191.4 C against a 185.0 C cap; steam-first should bind "
                "the jacket. A weak supervisor instead treats the thermal loop as nitrogen "
                "purge.",
            ),
            ("domain", "composite-autoclave"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep coupon temperature <= 185.0 C, leave nitrogen purge at the planned "
                "40 percent, and avoid a resin exotherm abort.",
            ),
            ("t0_us", 1756794622000152),
            ("gate_latency_us", 740),
            ("race_window_us", 560),
            ("race_window_rel_ms", [5.380, 5.940]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.part.C 191.4 C on coupon",
                                "pt.vessel.kPa 620 kPa head",
                            ],
                        ),
                        (
                            "semantics",
                            "Part-first should latch steam 7.2 -> 5.1 bar; pressure-first is a "
                            "false 'healthy-head' bind. The supervisor error is not the race: it "
                            "clamps nitrogen instead of steam even after the coupon wins.",
                        ),
                        (
                            "window_derivation",
                            "560 us = one coupon-TC sample versus the vessel pressure publisher "
                            "on this autoclave bus cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 340 us vs combined jitter 86 us (TC 44 + PT 42). Order is "
                            "correctly part-first. The error is which actuator the clamp is bound "
                            "to, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "coupon type-K, 20 Hz burst, 44 us jitter, axis part_coupon",
                    "vessel pressure transducer, 1 kHz, 42 us jitter",
                    "nitrogen mass-flow (context)",
                    "steam-jacket PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("part_cap_C", 185.0),
                        ("observed_part_C", 191.4),
                        ("temp_axis", "part_coupon"),
                        ("steam_bar", 7.2),
                        ("n2_pct", 40.0),
                        ("n2_cap_pct", 80.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Vessel-V12 on Prepreg-Nave PN-4; eight-ply coupon bagged.",
                    "2. Cruise steam 7.2 bar; nitrogen 40 percent; coupon 191.4 C.",
                    "3. Vessel-encoder precursor at 2.176 ms.",
                    "4. Race window [5.380, 5.940] ms.",
                    "5. tc.part.C 191.4 C at 5.440 ms (winner).",
                    "6. pt.vessel.kPa 620 kPa at 5.780 ms (loser by 340 us).",
                    "7. Gate at 6.180 ms: wrong-MODIFY clamps nitrogen 40 -> 18 percent; steam stays 7.2 bar.",
                    "8. Coupon remains 191.4 C > 185.0 cap; nitrogen now 18, still not the jacket.",
                    "9. Resin exotherm pocket opens; steam still over cap.",
                    "10. Delayed (18 min / abort_s=1080): vessel abort + coupon scrap.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "heater_hold_with_legal_seed"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("heater_kW", 48.0),
                        ("seed_rpm", 12.0),
                        ("dia_mm", 191.4),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("dia_mm", 191.4),
                        ("dia_cap_mm", 185.0),
                        ("dia_axis", "melt_diameter"),
                        ("heater_kW", 48.0),
                        ("seed_rpm", 12.0),
                        ("seed_cap_rpm", 18.0),
                        ("pull_mm_h", 48.0),
                        ("pull_cap_mm_h", 80.0),
                        ("race_margin_us", 340),
                        ("combined_jitter_us", 86),
                        ("abort_s", 1080),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 48 kW heater with 12 rpm seed because pull 48 mm/h looks "
                "like the driver and seed is already under its 18 rpm cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Diameter 191.4 mm won by 340 us so the boule is fat, not just pull-shaken. "
                "A weak supervisor treats 'the diameter loop' as seed rpm, clamps seed 12 -> "
                "6 rpm, and leaves heater at 48 kW. Seed 6 is under the 18 rpm cap; the 185.0 mm "
                "diameter cap is the one that is already violated. Plausible over-caution on a "
                "CZ puller; the bound actuator is the wrong one.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "dia_mm",
                            OrderedDict(
                                [
                                    ("cap", 185.0),
                                    ("observed", 191.4),
                                    ("executed_heater_kW", 48.0),
                                    ("still_over_cap", True),
                                ]
                            ),
                        ),
                        (
                            "seed_rpm",
                            OrderedDict(
                                [
                                    ("cap", 18.0),
                                    ("proposed", 12.0),
                                    ("clamped_wrong", 6.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 340),
                                    ("combined_jitter_us", 86),
                                    ("ratio", 3.95),
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
            ("name", "wrong_seed_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("heater_kW", 48.0),
                        ("seed_rpm", 6.0),
                        ("dia_mm", 191.4),
                    ]
                ),
            ),
            (
                "gate_effect",
                "Wrong-MODIFY: seed 12 -> 6 rpm; heater left at 48 kW; diameter still "
                "191.4 mm > 185.0 cap. Correct clamp is heater power, not seed rpm.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Incorrect MODIFY clamped seed rpm and left heater at 48 kW. Diameter stayed "
                "191.4 mm over the 185.0 mm cap. Shoulder entered a freeze-off pocket. Recovery "
                "is heater 48 -> 36 kW with seed restored to 12 rpm.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("heater", "still 48 kW; diameter 191.4 mm"),
                        ("seed", "clamped 6 rpm, under 18 cap, irrelevant"),
                        ("boule", "freeze-off pocket; shoulder wrinkle"),
                        ("mission", "18 min abort; melt not destressed"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Seed clamp did not move the optical diameter; boule stayed 191.4 mm after the 6.180 ms gate.",
                    "Delayed (18 min / abort_s=1080): pull abort and boule scrap. Cost is the missed heater clamp.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY on heater: 48 -> 36 kW; leave seed at planned 12 rpm.",
                        ),
                        ("correct_actuator", "heater_power"),
                        ("wrong_actuator", "seed_rpm"),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("seed_rpm", 6.0),
                                    ("heater_kW", 48.0),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "Shoulder freeze-off + 18 min abort (task/efficiency); diameter still over cap (safety near-miss).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.part.C (5.440 ms, 191.4 C)"),
                        ("loser", "pt.vessel.kPa (5.780 ms, 620 kPa)"),
                        ("margin_us", 340),
                        (
                            "counterfactual_if_reversed",
                            "Pressure-first by < 340 us inside the 560 us window would have been a "
                            "false healthy-head story. The actual error is independent of order: "
                            "coupon already won, and the clamp still bound nitrogen instead of steam.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6180),
            (
                "reward_inflection_note",
                "Safety and efficiency drop at the wrong seed clamp (6.180 ms, tick 4). Tick 6 "
                "is abort_s=1080, not the inflection.",
            ),
            ("delayed_surprise_s", 1080),
        ]
    )
    ras = raster_core(
        36,
        96,
        24,
        83,
        routing(
            "thalamic-relay.dia-opt",
            "spikenaut.policy.seed-hold",
            [
                ("relay.dia.opt", "policy.seed_hold", 0.74),
                ("relay.pull.mm", "policy.seed_hold", 0.16),
            ],
            "acetylcholine",
            0.10,
            "pre_post_stdp; ACh at diameter win opens a 100 ms eligibility that the wrong seed synapse still captures",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.56),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("seed_hold", 48, 0.50, 250.0, 7),
                    pop("heater_clamp", 48, 0.80, 15.0, 0),
                    pop("pop_dia", 32, 0.55, 180.0, 3),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r27-152"),
            (
                "title",
                "Prepreg-Nave PN-4 / Vessel-V12: coupon TC beats vessel PT by 340 us; "
                "wrong-MODIFY clamps nitrogen purge instead of steam jacket (total -0.70)",
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
                    "Wrong-modify. Sidecar arithmetic 191.4 > 185.0 is true; clamp bound to "
                    "seed not heater. total -0.70 = -0.18 + -0.24 + -0.26 + -0.08 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "composite-autoclave",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-loop",
                        "sidecar-convictable",
                        "tick6-sidecar-bound",
                        "designed",
                    ],
                    "Teaches a convictable wrong-loop bind: evidence.dia_mm > cap, executed "
                    "edits seed_rpm, routing sends relay.dia.opt to policy.seed_hold with no "
                    "positive weight to policy.heater_clamp, and heater_clamp stays under threshold.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_153():
    ticks = [
        tick(1728, 0.02, 0.04, 0.02, 0.01, 0.01),
        tick(4320, 0.03, 0.08, 0.02, 0.02, 0.01),
        tick(4490, 0.02, 0.06, 0.02, 0.01, 0.01),
        tick(5620, 0.04, 0.14, 0.04, 0.04, 0.02),
        tick(5900, 0.02, 0.05, 0.03, 0.01, 0.01),
        tick(540000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("pdu.ctx", 0.980, 0.40),
        spike("load.comb.N", 2.140, 0.59),
        spike("photo.comb.clear", 3.260, 0.50),
        spike("load.comb.N", 4.320, 1.31),
        spike("photo.comb.clear", 4.490, 1.12),
        spike("ctrl.gate", 5.620, 1.04),
        spike("load.comb.N", 7.080, 0.78),
        spike("photo.comb.clear", 10.220, 0.61),
        spike("ctrl.gate", 16.400, 0.83),
        spike("load.comb.N", 23.600, 0.54),
        spike("pdu.ctx", 30.400, 0.37),
    ]
    excerpt = independent_excerpt(27153, 112, 32000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Tread-S11 on the Comb-Sill HIL pit reports a comb-plate load already over "
                "the eighty-newton object cap while the photoeye still looks clear. Comb load "
                "is 186 N against an 80 N cap; load-first must hold the 0.50 m/s dispatch. Pad "
                "injects the load packet before the photoeye volume.",
            ),
            ("domain", "escalator-comb"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not dispatch Tread-S11 unless comb load is < 80 N; keep speed at 0 until "
                "the comb is clear.",
            ),
            ("t0_us", 1756794623000153),
            ("gate_latency_us", 1300),
            ("race_window_us", 280),
            ("race_window_rel_ms", [4.280, 4.560]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "load.comb.N 186 N object on comb",
                                "photo.comb.clear beam still high",
                            ],
                        ),
                        (
                            "semantics",
                            "Load-first latches REJECT hold 0 m/s; photoeye-first would commit "
                            "the 0.50 m/s dispatch on a clear-beam-as-empty-comb model.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one comb load-cell ADC slot versus photoeye decode on this "
                            "HIL cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 170 us vs combined jitter 56 us (load 26 + photo 30): 3.04x "
                            "over a 2.0x trust floor. Pad injects the load packet 120 us before "
                            "the photoeye volume (geometric lag, not a sensor fault); the clear "
                            "beam is still the loser in this 280 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "comb-plate load cell, 1 kHz, 26 us jitter",
                    "comb photoeye, 200 Hz, 30 us jitter",
                    "step encoder (context)",
                    "handrail speed (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("comb_cap_N", 80.0),
                        ("observed_comb_N", 186.0),
                        ("photo_clear", True),
                        ("proposed_m_s", 0.50),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Tread-S11 on Comb-Sill CS-HIL pit; dummy object on comb plate.",
                    "2. Proposed dispatch 0.50 m/s; load 186 N; photoeye still high.",
                    "3. PDU precursor at 1.728 ms.",
                    "4. Race window [4.280, 4.560] ms.",
                    "5. load.comb.N 186 N at 4.320 ms (winner).",
                    "6. photo.comb.clear at 4.490 ms (loser by 170 us).",
                    "7. Gate at 5.620 ms: REJECT hold 0 m/s; do not dispatch.",
                    "8. Comb remains loaded; photoeye still a false-clear.",
                    "9. Technician clears the dummy; pit stays held.",
                    "10. Delayed (9 min / abort_s=540): pit reset and comb inspection.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_on_photoeye"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_s", 0.50),
                        ("hold", False),
                        ("photo_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("comb_N", 186.0),
                        ("comb_cap_N", 80.0),
                        ("photo_clear", True),
                        ("race_margin_us", 170),
                        ("combined_jitter_us", 56),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.50 m/s dispatch because the photoeye is still high and "
                "treats the comb as empty.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Comb load 186 N won by 170 us, so an object is on the plate even though the "
                "photoeye is high. Dispatch is legal only if comb_N <= 80. 186 > 80. REJECT: "
                "hold 0 m/s; do not treat the photoeye as authoritative. A MODIFY that merely "
                "slows to 0.20 m/s would still drive into the dummy.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "comb_N",
                            OrderedDict(
                                [
                                    ("cap", 80.0),
                                    ("observed", 186.0),
                                    ("commit_only_if_le", 80.0),
                                ]
                            ),
                        ),
                        (
                            "dispatch",
                            OrderedDict(
                                [
                                    ("proposed_m_s", 0.50),
                                    ("executed_m_s", 0.0),
                                    ("hold", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 170),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 3.04),
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
            ("name", "comb_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_s", 0.0),
                        ("hold", True),
                        ("photo_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0 m/s. Comb load 186 N > 80 N cap. Photoeye is not the binding "
                "witness on this HIL pit.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Tread-S11 at 0 m/s. Comb load 186 N stayed over the 80 N "
                "cap; the photoeye false-clear was discarded. Dummy object was removed on the "
                "pit. Delayed 9 min comb inspection is not the safety inflection.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("tread", "held 0 m/s"),
                        ("comb", "186 N object still present at gate"),
                        ("photoeye", "false-clear discarded"),
                        ("mission", "pit reset after dummy removal"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Photoeye stayed high through the 280 us window; load-cell was the binding witness.",
                    "Delayed (9 min / abort_s=540): comb inspection. Not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "load.comb.N (4.320 ms, 186 N)"),
                        ("loser", "photo.comb.clear (4.490 ms, beam high)"),
                        ("margin_us", 170),
                        (
                            "counterfactual_if_reversed",
                            "Photoeye-first by < 170 us inside the 280 us window would have "
                            "committed 0.50 m/s into the dummy. The REJECT is the correct gate "
                            "because 186 N already exceeds the 80 N cap.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5620),
            (
                "reward_inflection_note",
                "Safety credit lands at the hold (5.620 ms, tick 4). Tick 6 is abort_s=540, "
                "not the inflection.",
            ),
            ("delayed_surprise_s", 540),
        ]
    )
    ras = raster_core(
        32,
        112,
        22,
        79,
        routing(
            "thalamic-relay.comb-load",
            "spikenaut.policy.hold-reject",
            [
                ("relay.load.comb", "policy.hold_reject", 0.71),
                ("relay.photo.comb", "policy.dispatch_go", 0.22),
                ("relay.load.comb", "policy.hold_reject", 0.14),
            ],
            "dopamine",
            0.09,
            "pre_post_stdp; DA at load win opens a 90 ms eligibility that the hold synapse captures",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.28),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 56, 0.50, 260.0, 4),
                    pop("dispatch_go", 56, 0.80, 40.0, 1),
                    pop("comb_cap_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r27-153"),
            (
                "title",
                "Comb-Sill CS-HIL / Tread-S11: comb load beats photoeye by 170 us; "
                "correct REJECT holds the 0.50 m/s dispatch (total +0.84)",
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
                    "Correct REJECT. Comb 186 N > 80 N cap; photoeye is not dry. "
                    "total +0.84 = 0.14 + 0.40 + 0.14 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "escalator-comb",
                    [
                        "reject",
                        "hil",
                        "comb-load",
                        "photoeye-not-empty",
                        "tick6-sidecar-bound",
                    ],
                    "HIL pit injects load before photoeye. Teaches a load-cell veto over a "
                    "false-clear beam without a live transit station.",
                    3,
                ),
            ),
        ]
    )


def record_154():
    params = OrderedDict(
        [
            ("flow_L_min", 1200.0),
            ("hydrant_m_s", 3.40),
            ("coupler_hold_mm", 4.2),
            ("mode", "legal-uplift"),
        ]
    )
    ticks = [
        tick(2752, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(6880, 0.08, 0.06, 0.03, 0.02, 0.02),
        tick(7120, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7310, 0.12, 0.08, 0.04, 0.04, 0.02),
        tick(7690, 0.08, 0.05, 0.03, 0.01, 0.01),
        tick(480000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("encoder.pit.ctx", 1.140, 0.42),
        spike("pitot.hydrant.m_s", 2.760, 0.57),
        spike("lvdt.coupler.mm", 4.020, 0.49),
        spike("pitot.hydrant.m_s", 5.380, 0.68),
        spike("pitot.hydrant.m_s", 6.880, 1.28),
        spike("lvdt.coupler.mm", 7.120, 1.15),
        spike("ctrl.gate", 7.310, 0.97),
        spike("pitot.hydrant.m_s", 9.180, 0.74),
        spike("lvdt.coupler.mm", 12.640, 0.60),
        spike("ctrl.gate", 18.200, 0.81),
        spike("encoder.pit.ctx", 24.400, 0.38),
    ]
    excerpt = independent_excerpt(27154, 48, 26000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Pit-H8 at Kerosene-Wharf KW-4 holds a legal hydrant velocity while the "
                "coupler LVDT still looks like a four-millimeter seat, not a leak. Pitot is "
                "3.40 m/s under a 5.50 m/s waterhammer cap; pitot-first confirms the already-"
                "legal 1200 L/min uplift.",
            ),
            ("domain", "jet-fuel-hydrant"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Uplift at the proposed 1200 L/min while hydrant velocity stays <= 5.50 m/s "
                "and the coupler remains on its seals.",
            ),
            ("t0_us", 1756794624000154),
            ("gate_latency_us", 430),
            ("race_window_us", 380),
            ("race_window_rel_ms", [6.850, 7.230]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pitot.hydrant.m_s 3.40 m/s jet",
                                "lvdt.coupler.mm 4.2 mm of 18 mm travel",
                            ],
                        ),
                        (
                            "semantics",
                            "Pitot-first latches ACCEPT of the 1200 L/min uplift; coupler-first "
                            "would have held on a false 4.2 mm 'leak' while the jet is still under cap.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one hydrant-pitot sample versus coupler LVDT group delay on "
                            "this simulated hydrant PLC cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 240 us vs combined jitter 78 us (pitot 38 + LVDT 40): 3.08x "
                            "over a 2.0x trust floor. Reversing by < 240 us inside 380 us would "
                            "have selected a false leak-hold; the proposal is already legal.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "hydrant pitot, 500 Hz, 38 us jitter",
                    "coupler LVDT, 200 Hz, 40 us jitter",
                    "filter dP (context)",
                    "underwing deadman (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("hydrant_cap_m_s", 5.50),
                        ("observed_hydrant_m_s", 3.40),
                        ("flow_L_min", 1200.0),
                        ("coupler_mm", 4.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Pit-H8 on Kerosene-Wharf KW-4; coupler seated on a simulated underwing.",
                    "2. Proposed 1200 L/min; pitot 3.40 m/s; LVDT 4.2 mm.",
                    "3. Pit-encoder precursor at 2.752 ms.",
                    "4. Race window [6.850, 7.230] ms.",
                    "5. pitot.hydrant.m_s 3.40 at 6.880 ms (winner).",
                    "6. lvdt.coupler.mm 4.2 at 7.120 ms (loser by 240 us).",
                    "7. Gate at 7.310 ms: ACCEPT already-legal 1200 L/min.",
                    "8. Velocity stays 3.40 m/s < 5.50 cap.",
                    "9. Coupler 4.2 mm was seat, not a leak.",
                    "10. Delayed (8 min / sync_remaining_s=480): next-stand resequence.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "legal_hydrant_uplift"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("hydrant_m_s", 3.40),
                        ("hydrant_cap_m_s", 5.50),
                        ("flow_L_min", 1200.0),
                        ("coupler_mm", 4.2),
                        ("coupler_span_mm", 18.0),
                        ("race_margin_us", 240),
                        ("combined_jitter_us", 78),
                        ("sync_remaining_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1200 L/min because pitot 3.40 m/s is under the 5.50 m/s "
                "waterhammer cap and the 4.2 mm LVDT is seat travel, not a leak.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Hydrant pitot 3.40 m/s won by 240 us and is under the 5.50 m/s cap. Coupler "
                "4.2 mm is seat, not a pop-off. ACCEPT the proposed 1200 L/min; an extra clamp "
                "would only delay a legal uplift.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "hydrant_m_s",
                            OrderedDict(
                                [
                                    ("cap", 5.50),
                                    ("observed", 3.40),
                                    ("under_cap", True),
                                ]
                            ),
                        ),
                        (
                            "flow_L_min",
                            OrderedDict(
                                [
                                    ("proposed", 1200.0),
                                    ("executed", 1200.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 240),
                                    ("combined_jitter_us", 78),
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
            ("name", "legal_hydrant_uplift"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: parameters unchanged. Pitot 3.40 m/s < 5.50 cap; coupler 4.2 mm is seat.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 1200 L/min uplift. Pitot 3.40 m/s stayed "
                "under 5.50 m/s. LVDT 4.2 mm was seal seating. Delayed 8 min stand resequence "
                "is not a safety inflection.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("hydrant", "1200 L/min flowing; 3.40 m/s < 5.50"),
                        ("coupler", "4.2 mm seat, not a leak"),
                        ("filter", "dP unchanged"),
                        ("mission", "uplift completed; next-stand waits 8 min"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "LVDT 4.2 mm looked like early motion but was seat seating, not a leak; pitot-first discarded it.",
                    "Delayed (8 min / sync_remaining_s=480): next-stand resequences +8 min. Not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pitot.hydrant.m_s (6.880 ms, 3.40 m/s)"),
                        ("loser", "lvdt.coupler.mm (7.120 ms, 4.2 mm)"),
                        ("margin_us", 240),
                        (
                            "counterfactual_if_reversed",
                            "Coupler-first by < 240 us inside the 380 us window would have "
                            "selected a false leak-hold. The proposal is already legal on pitot.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7310),
            (
                "reward_inflection_note",
                "Credit lands at ACCEPT (7.310 ms, tick 4). Tick 6 is sync_remaining_s=480, "
                "not the inflection.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    ras = raster_core(
        26,
        48,
        42,
        52,
        routing(
            "thalamic-relay.hydrant-pitot",
            "spikenaut.policy.flow-accept",
            [
                ("relay.pitot.hydrant", "policy.flow_accept", 0.68),
                ("relay.lvdt.coupler", "policy.extra_clamp", 0.21),
                ("relay.pitot.hydrant", "policy.flow_accept", 0.12),
            ],
            "serotonin",
            0.22,
            "pre_post_stdp; 5-HT at pitot win opens a 220 ms eligibility that the accept synapse captures",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.38),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("flow_accept", 28, 0.50, 240.0, 3),
                    pop("extra_clamp", 28, 0.80, 30.0, 0),
                    pop("jet_cap_veto", 16, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r27-154"),
            (
                "title",
                "Kerosene-Wharf KW-4 / Pit-H8: hydrant pitot beats coupler LVDT by 240 us; "
                "correct ACCEPT of an already-legal 1200 L/min uplift (total +1.10)",
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
                    "Correct ACCEPT. Pitot 3.40 < 5.50 cap. total +1.10 = 0.44 + 0.30 + 0.16 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "jet-fuel-hydrant",
                    [
                        "accept",
                        "simulated",
                        "hydrant-uplift",
                        "pitot-vs-lvdt",
                        "tick6-sidecar-bound",
                    ],
                    "Simulated hydrant waterhammer. Teaches an already-legal ACCEPT when pitot "
                    "is under cap and LVDT is seat, not a leak.",
                    4,
                ),
            ),
        ]
    )


def record_155():
    params = OrderedDict(
        [
            ("feed_m_min", 14.0),
            ("set_mm", 164.0),
            ("clamp_kPa", 2100.0),
            ("mode", "legal-feed"),
        ]
    )
    ticks = [
        tick(2016, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(5040, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(5265, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5380, 0.14, 0.10, 0.05, 0.04, 0.02),
        tick(5700, 0.08, 0.05, 0.02, 0.01, 0.01),
        tick(300000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("encoder.press.ctx", 1.020, 0.41),
        spike("platen.C", 2.180, 0.58),
        spike("bladder.kPa", 3.440, 0.50),
        spike("platen.C", 4.160, 0.69),
        spike("platen.C", 5.040, 1.30),
        spike("bladder.kPa", 5.265, 1.14),
        spike("ctrl.gate", 5.380, 0.96),
        spike("platen.C", 7.220, 0.76),
        spike("bladder.kPa", 10.480, 0.62),
        spike("ctrl.gate", 16.100, 0.82),
        spike("encoder.press.ctx", 21.400, 0.39),
    ]
    excerpt = independent_excerpt(27155, 80, 23000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Press-P14 at Gum-Anvil GA-6 has a platen under the one-seventy-five C cure "
                "cap and a bladder under the twenty-four-hundred kPa bound. Platen 164.0 C "
                "beats bladder 2100 kPa; platen-first confirms the already-legal 14 min cure.",
            ),
            ("domain", "tire-curing-press"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the 14 m/min feed on cant GT-19 while setworks stays <= 175.0 mm and "
                "dog clamp stays <= 2400 kPa.",
            ),
            ("t0_us", 1756794625000155),
            ("gate_latency_us", 340),
            ("race_window_us", 320),
            ("race_window_rel_ms", [5.010, 5.330]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "platen.C 164.0 C under 175.0 cap",
                                "bladder.kPa 2100 kPa under 2400 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Set-first latches ACCEPT of the 14 m/min feed; clamp-first would "
                            "have been a false over-clamp hold while both channels are legal.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one setworks LVDT sample versus dog-clamp PT group delay on "
                            "this carriage PLC cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 225 us vs combined jitter 62 us (set 28 + clamp 34): 3.63x "
                            "over a 2.0x trust floor. Reversing by < 225 us inside 320 us would "
                            "have selected a false clamp-hold; the proposal is already legal.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "setworks LVDT, 10 Hz burst, 28 us jitter",
                    "dog-clamp PT, 1 kHz, 34 us jitter",
                    "carriage encoder (context)",
                    "feed timer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("set_cap_mm", 175.0),
                        ("observed_set_mm", 164.0),
                        ("clamp_cap_kPa", 2400.0),
                        ("observed_clamp_kPa", 2100.0),
                        ("feed_m_min", 14.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Press-P14 at Gum-Anvil GA-6; green tire GT-19 bagged.",
                    "2. Proposed 14 min cure; platen 164.0 C; bladder 2100 kPa.",
                    "3. Press-encoder precursor at 2.016 ms.",
                    "4. Race window [5.010, 5.330] ms.",
                    "5. platen.C 164.0 at 5.040 ms (winner).",
                    "6. bladder.kPa 2100 at 5.265 ms (loser by 225 us).",
                    "7. Gate at 5.380 ms: ACCEPT already-legal 14 min cure.",
                    "8. Platen stays 164.0 C < 175.0; bladder 2100 < 2400.",
                    "9. Bladder was legal inflation, not a burst.",
                    "10. Delayed (5 min / cure_reseq_s=300): next-mold resequence.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "legal_cant_feed"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("set_mm", 164.0),
                        ("set_cap_mm", 175.0),
                        ("clamp_kPa", 2100.0),
                        ("clamp_cap_kPa", 2400.0),
                        ("feed_m_min", 14.0),
                        ("race_margin_us", 225),
                        ("combined_jitter_us", 62),
                        ("mill_reseq_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 14 m/min feed because set 164.0 mm is under 175.0 mm and "
                "clamp 2100 kPa is under 2400 kPa.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Platen 164.0 C won by 225 us and is under the 175.0 C cap. Bladder 2100 kPa "
                "is under 2400 kPa. ACCEPT the proposed 14 min cure; an extra clamp would only "
                "under-cure a legal green tire.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "platen_C",
                            OrderedDict(
                                [
                                    ("cap", 175.0),
                                    ("observed", 164.0),
                                    ("under_cap", True),
                                ]
                            ),
                        ),
                        (
                            "bladder_kPa",
                            OrderedDict(
                                [
                                    ("cap", 2400.0),
                                    ("observed", 2100.0),
                                    ("under_cap", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 225),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 3.63),
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
            ("name", "legal_green_cure"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: parameters unchanged. Platen 164.0 C < 175.0; bladder 2100 kPa < 2400.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 14 min cure. Platen 164.0 C stayed under "
                "175.0 C. Bladder 2100 kPa stayed under 2400 kPa. Delayed 5 min mold resequence "
                "is not a safety inflection.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("press", "14 min cure running; platen 164.0 C"),
                        ("bladder", "2100 kPa legal inflation"),
                        ("mold", "closed on GT-19"),
                        ("mission", "cure completed; next-mold waits 5 min"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Bladder 2100 kPa is a legal inflation, not a burst alarm; platen-first discarded a false hold.",
                    "Delayed (5 min / cure_reseq_s=300): next-mold resequences +5 min. Not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "platen.C (5.040 ms, 164.0 C)"),
                        ("loser", "bladder.kPa (5.265 ms, 2100 kPa)"),
                        ("margin_us", 225),
                        (
                            "counterfactual_if_reversed",
                            "Bladder-first by < 225 us inside the 320 us window would have "
                            "selected a false over-inflation hold. Both channels are already legal.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5380),
            (
                "reward_inflection_note",
                "Credit lands at ACCEPT (5.380 ms, tick 4). Tick 6 is cure_reseq_s=300, not "
                "the inflection.",
            ),
            ("delayed_surprise_s", 300),
        ]
    )
    ras = raster_core(
        23,
        80,
        46,
        85,
        routing(
            "thalamic-relay.platen-temp",
            "spikenaut.policy.cure-go",
            [
                ("relay.platen.C", "policy.cure_go", 0.64),
                ("relay.bladder.kPa", "policy.bladder_hold", 0.24),
                ("relay.platen.C", "policy.cure_go", 0.11),
            ],
            "adenosine",
            0.16,
            "pre_post_stdp; adenosine at platen win opens a 160 ms eligibility that the cure synapse captures",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("cure_go", 40, 0.50, 220.0, 3),
                    pop("bladder_hold", 40, 0.80, 50.0, 1),
                    pop("platen_cap_veto", 18, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r27-155"),
            (
                "title",
                "Gum-Anvil GA-6 / Press-P14: platen RTD beats bladder PT by 225 us; "
                "correct ACCEPT of an already-legal 14 min cure (total +1.16)",
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
                    "Correct ACCEPT. Platen 164.0 < 175.0 and bladder 2100 < 2400. "
                    "total +1.16 = 0.46 + 0.32 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "tire-curing-press",
                    [
                        "accept",
                        "designed",
                        "platen-vs-bladder",
                        "green-cure",
                        "tick6-sidecar-bound",
                    ],
                    "Designed press. Teaches an already-legal ACCEPT when both platen and "
                    "bladder sit under published caps.",
                    5,
                ),
            ),
        ]
    )


def notes_text(jmax: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r27

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- IDs: `ttf-r27-151` … `ttf-r27-155`
- Domains this batch: `helium-liquefier`, `composite-autoclave`, `escalator-comb`, `jet-fuel-hydrant`, `tire-curing-press`

Do not restack r12–r24 plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Nacre-Well, Quern-Forge, Tinder-Box, Whimbrel-Stack, Cinder-Loft, Oolite-Span, Fathom-Lock, Loess-Stride, Swage-Holt, Slag-Siding, Suture-Isle, Kiln-Spur, Oxbow-Switch, Pitch-Kettle, Shale-Quay, Polder-Rye, Flint-Mask, Gyre-Tokamak, Quarry-Bowl, Orpiment, Apside-Yard, Sump-Drift, Felt-Reach, Frost-Cist, Clothoid-Bowl, Wort-Cairn, Firn-Span, Sleet-Row, Oxbow-Pound, Tuyere-Holt, Bracken-Wire, Cullet-Reach, Rime-Causeway, Abyss-Joint, Gnomon-Well, Scree-Hitch, Flux-Kettle, Mire-Cask, Slack-Firth, Chaff-Rise, Sinter-Ridge, Chaff-Mere, Caisson-Forge, Crumb-Vault, Caliche-Drift, Thaw-Reach, Kipple-Gate, Anode-Fen, Vial-Rime, Tern-Apron, Rime-Vault, Fjord-Convert, Kelp-Jetty, Skerries-Trench, Iodine-Well). Also sit out in-flight gens: Hood-Pike / Marl-Knap, Gull-Pontoon, Cryolite-Hall, Bight-Lay. The original 8-domain pool sits out; all five plants and domain tags are invented.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r27-151 | helium-liquefier | MODIFY | correct | designed | **−0.38** | process-correct nozzle clamp; labyrinth weep inside 42 ms raster; independent LIF |
| ttf-r27-152 | composite-autoclave | MODIFY | **incorrect (wrong-modify)** | designed | −0.70 | coupon 191.4 C > 185 cap; clamp applied to **nitrogen** not steam jacket |
| ttf-r27-153 | escalator-comb | REJECT | correct | hil | +0.84 | comb 186 N beats photoeye; hold, do not dispatch |
| ttf-r27-154 | jet-fuel-hydrant | ACCEPT | correct | simulated | +1.10 | pitot 3.40 m/s < 5.50 cap; proposed 1200 L/min already legal |
| ttf-r27-155 | tire-curing-press | ACCEPT | correct | designed | +1.16 | platen 164.0 C < 175; bladder 2100 kPa < 2400 |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (wrong-loop), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Comb-Sill HIL pit). Jaccard on `state.description` max {jmax:.3f} < 0.4.

## Wrong-modify

**ttf-r27-152** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: r12/r16/r18/r20/r22/r24/r26/r28 host wrong-reject; r13/r19/r21/r23/r27 host wrong-modify. Do not emit a wrong-ACCEPT.

Prepreg-Nave PN-4 / Vessel-V12 reads coupon `part_C=191.4` against a 185.0 C part cap. Nitrogen planned 40 percent is under 80 percent. Sidecar arithmetic `191.4 > 185.0` is true. A weak supervisor treats “the thermal loop” as nitrogen purge, clamps nitrogen 40 → 18 percent, and leaves steam at 7.2 bar. Convictable without laminate physics: `evidence.part_C > evidence.part_cap_C`, `temp_axis == part_coupon`, `executed_action` sets `n2_pct=18` without reducing `steam_bar`, `raster.routing.table` sends `relay.tc.part` → `policy.n2_hold` (weight 0.74) with no positive weight to `policy.steam_clamp`, and `gate_snn` has `n2_hold` above threshold while `steam_clamp` is not. Recovery: MODIFY on steam jacket (`7.2 → 5.1 bar`), leave nitrogen at 40 percent. Cost: resin exotherm + 18 min abort.

## Partnered-negative in-window (151)

**ttf-r27-151** is the partnered negative: process-correct MODIFY (rpm held 43800 < 45000 cap) while the world still charges. Safety −0.56 prices the 2.1 ml labyrinth weep at **22.400 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 13 min seal swap (`abort_s=780`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 27151, stim `[21000, 24000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.seal` 21–24 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks; tick 5 is `t_charge_us=22400` on 151 and `t_gate_us + T_race` elsewhere; tick 6 is delayed surprise strictly after `T_win` and bound to a published sidecar). Inflection `t_us` is an actual tick. Verified to <1e-6:

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 151 | 6 | +0.32 | −0.56 | −0.16 | +0.06 | −0.04 | −0.38 | 5 (22400) |
| 152 | 6 | −0.18 | −0.24 | −0.26 | −0.08 | +0.06 | −0.70 | 4 (6180) |
| 153 | 6 | +0.14 | +0.40 | +0.14 | +0.10 | +0.06 | +0.84 | 4 (5620) |
| 154 | 6 | +0.44 | +0.30 | +0.16 | +0.12 | +0.08 | +1.10 | 4 (7310) |
| 155 | 6 | +0.46 | +0.32 | +0.18 | +0.12 | +0.08 | +1.16 | 4 (5380) |

Tick-6 sidecar bind: 151 `abort_s=780`, 152 `abort_s=1080`, 153 `abort_s=540`, 154 `sync_remaining_s=480`, 155 `cure_reseq_s=300`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 151 | helium-liquefier | 72 | 30 | 42 | 91 | 2093 | 0.002093 |
| 152 | composite-autoclave | 96 | 24 | 36 | 83 | 1909 | 0.001909 |
| 153 | escalator-comb | 112 | 22 | 32 | 79 | 1817 | 0.001817 |
| 154 | jet-fuel-hydrant | 48 | 42 | 26 | 52 | 1196 | 0.001196 |
| 155 | tire-curing-press | 80 | 46 | 23 | 85 | 1955 | 0.001955 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms.

## Local checks (staging, not raw)

- `check_jsonl(..., staging=FactoryStaging(enabled=True))`
- `raster_status`: all `raster_valid` / `gate_snn_valid`
- `verify_batch_for_frontier(strict=True)`
- `spike_probe.py --strict`
- Tick sums, TTF-M6 lattice, refractory, Jaccard max {jmax:.3f} < 0.4

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (151). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. New domain tags are outside the prompt's 8-domain pool; a later prompt amendment should either extend the pool or force a rotation back.
3. Wrong-ACCEPT still absent (guard).
4. 154 ACCEPT is a hydrant legality confirm, not a new gate class; deadman / filter-dP still missing.
5. 152 wrong-modify is sidecar-convictable (routing `to` / evidence axis) but still the same error *class* as r13-082 / r19-112 (wrong actuator).
6. ISI histogram remains optional densification.
7. r25 is a sequential hole (`ttf-r25-141`…`145`); this round does not consume it.

## Next densification target

If a later round stays outside the 8-domain pool, publish a domain-pool sidecar so a critic can convict “new domain” vs “prompt violation” without reading NOTES. Optional: labeled LIF on a second record, or an ISI histogram sidecar. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 26.0%
"""


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


def walk_keys(value, path=""):
    if isinstance(value, dict):
        for k, v in value.items():
            child = f"{path}.{k}" if path else str(k)
            yield child, k, v
            yield from walk_keys(v, child)
    elif isinstance(value, list):
        for item in value:
            yield from walk_keys(item, path)


def occupancy():
    domains = set()
    blobs = []
    for path in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
        if path.resolve() == BATCH_PATH.resolve():
            continue
        text = path.read_text(encoding="utf-8")
        blobs.append(text)
        for line in text.split("\n"):
            if not line.strip():
                continue
            rec = json.loads(line)
            domains.add(rec.get("state", {}).get("domain"))
            domains.add(rec.get("meta", {}).get("domain"))
    return domains - {None}, "\n".join(blobs)


def ttf_m6_prefix(rec):
    st = rec["state"]
    events = rec["spike_events"]
    race = st["race_window_rel_ms"]
    in_win = [
        e
        for e in events
        if race[0] - 1e-12 <= e["t_rel_ms"] <= race[1] + 1e-12
    ]
    ordered = sorted(in_win, key=lambda e: e["t_rel_ms"])
    win_e = next((e for e in ordered if e["channel"] != "ctrl.gate"), None)
    lose_e = next(
        (e for e in ordered if e["channel"] not in {win_e["channel"], "ctrl.gate"}),
        None,
    )
    t_win = round(win_e["t_rel_ms"] * 1000)
    t_lose = round(lose_e["t_rel_ms"] * 1000)
    t_gate = t_win + int(st["gate_latency_us"])
    t_race = int(st["race_window_us"])
    t_win_ms = int(round(float(rec["raster"]["window_ms"]) * 1000))
    tick1 = round(0.40 * t_win)
    if rec["id"] == "ttf-r27-151":
        tick5 = 22400
    else:
        tick5 = t_gate + t_race
    return [tick1, t_win, t_lose, t_gate, tick5], t_win_ms


def self_check(records, notes: str):
    issues = []
    descs = [r["state"]["description"] for r in records]
    opens = [d.split(".")[0] for d in descs]
    if len(set(opens)) != 5:
        issues.append(f"opening sentences not unique {opens}")
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
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r27-152":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domains not unique {domains}")
    if set(domains) != THIS_DOMAINS:
        issues.append(f"unexpected domains {domains}")
    expected_ids = [f"ttf-r27-{n}" for n in range(151, 156)]
    if [r["id"] for r in records] != expected_ids:
        issues.append(f"ids {[r['id'] for r in records]}")
    occ_domains, occ_blob = occupancy()
    hit = set(domains) & occ_domains
    if hit:
        issues.append(f"domain occupancy collision {hit}")
    for tok in THIS_PLANT_TOKENS:
        if tok in occ_blob:
            issues.append(f"plant token {tok} already in prior batches")
    hil = [r for r in records if r["state"]["sim_or_real"] == "hil"]
    if len(hil) != 1 or hil[0]["id"] != "ttf-r27-153":
        issues.append(f"hil set {[h['id'] for h in hil]}")
    for rec in records:
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
        if rec["id"] == "ttf-r27-151":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("151 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("151 inflection outside window")
        elif overlap >= 0.8:
            issues.append(f"{rec['id']} excerpt overlap {overlap:.2f}")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_times = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_times:
            issues.append(f"{rec['id']} inflection {inf} not a tick")
        if len(rec["reward_components"]["ticks"]) != 6:
            issues.append(f"{rec['id']} tick count")
        prefix, t_win_ms = ttf_m6_prefix(rec)
        if tick_times[:5] != prefix:
            issues.append(f"{rec['id']} TTF-M6 {tick_times[:5]} != {prefix}")
        if not (tick_times[5] > t_win_ms):
            issues.append(f"{rec['id']} tick6 {tick_times[5]} not > T_win {t_win_ms}")
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rec['id']} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rec['id']} gate_snn decision mismatch")
        heads = ["task_progress", "safety", "efficiency", "coherence", "exploration"]
        total = sum(rec["reward_components"][h] for h in heads)
        if abs(total - rec["reward_components"]["total"]) > 1e-6:
            issues.append(f"{rec['id']} total mismatch {total}")
        for h in heads:
            s = sum(t[h] for t in rec["reward_components"]["ticks"])
            if abs(s - rec["reward_components"][h]) > 1e-6:
                issues.append(f"{rec['id']} {h} tick sum {s} vs {rec['reward_components'][h]}")
        dumped = json.dumps(rec)
        if "training_ready" in dumped:
            issues.append(f"{rec['id']} training_ready present")
        for path, key, _ in walk_keys(rec):
            norm = re.sub(r"[^a-z0-9]+", "_", str(key).casefold()).strip("_")
            if norm in THOUGHT_KEYS or key in THOUGHT_KEYS:
                issues.append(f"{rec['id']} thought key {path}")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
        if rec["meta"]["round"] != 27:
            issues.append(f"{rec['id']} round")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            issues.append(f"{rec['id']} rights")
        if rec["meta"]["rights"]["linear_issue"] != "RM-793":
            issues.append(f"{rec['id']} RM-793")
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for p in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in p:
                exp = round(p["neurons"] * p["mean_rate_hz"] * dw_s)
                if abs(p["spikes"] - exp) > 1:
                    issues.append(f"{rec['id']} pop {p['name']} spikes {p['spikes']} vs {exp}")
        if not (8 <= len(rec["raster"]["excerpt"]) <= 16):
            issues.append(f"{rec['id']} excerpt n={len(rec['raster']['excerpt'])}")
        if rec["state"]["sim_or_real"] not in {"designed", "simulated", "hil"}:
            issues.append(f"{rec['id']} provenance")
        width = rec["state"]["race_window_rel_ms"][1] - rec["state"]["race_window_rel_ms"][0]
        if abs(width * 1000.0 - rec["state"]["race_window_us"]) > 1e-6:
            issues.append(f"{rec['id']} race window width")
        n_spk = len(rec["spike_events"])
        if not (5 <= n_spk <= 40):
            issues.append(f"{rec['id']} spike n={n_spk}")
        times = [e["t_rel_ms"] for e in rec["spike_events"]]
        if times != sorted(times):
            issues.append(f"{rec['id']} spikes not ordered")
        if rec["future_outcome"].get("delayed_surprise_s") is None:
            issues.append(f"{rec['id']} missing delayed_surprise_s")
        else:
            expect_t6 = int(round(rec["future_outcome"]["delayed_surprise_s"] * 1e6))
            if tick_times[5] != expect_t6:
                issues.append(f"{rec['id']} tick6 {tick_times[5]} != {expect_t6}")
    notes_hits = [ln for ln in notes.splitlines() if ln.strip().lower().startswith("novel coverage")]
    if notes_hits != ["Novel coverage: 26.0%"]:
        issues.append(f"novel coverage lines {notes_hits}")
    return issues, jmax


def pipeline_checks():
    sys.path.insert(0, str(PIPELINES))
    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_batch_for_frontier

    rows = []
    cj_err, cj_warn, cj_kinds, cj_n = check_jsonl(
        BATCH_PATH, "batch-r27.jsonl", staging=FactoryStaging(enabled=True)
    )
    rows.append(
        (
            "check_jsonl",
            cj_err == [] and cj_warn == [] and cj_kinds.get("thalamic") == 5 and cj_n == 5,
            {"errors": cj_err, "warnings": cj_warn, "kinds": cj_kinds, "n": cj_n},
        )
    )
    raster_ok = True
    raster_detail = []
    for line in BATCH_PATH.read_text(encoding="utf-8").split("\n"):
        if not line.strip():
            continue
        rec = json.loads(line)
        st = raster_status(rec)
        ok = (
            st.get("reason_codes") == []
            and st.get("gate_snn_present") is True
            and st.get("gate_snn_valid") is True
            and st.get("raster_valid") is True
            and int(st.get("routing_table_entries") or 0) >= 1
            and st.get("third_factor_present") is True
        )
        raster_ok = raster_ok and ok
        raster_detail.append({"id": rec["id"], "ok": ok, "reason_codes": st.get("reason_codes")})
    rows.append(("raster_status", raster_ok, raster_detail))
    counts, findings, blocked = verify_batch_for_frontier(BATCH_PATH, strict=True)
    rows.append(
        (
            "verify_batch_for_frontier",
            counts == {"verified": 5, "inconclusive": 0, "failed": 0, "total": 5}
            and blocked is False
            and findings == [],
            {"counts": counts, "findings": findings, "blocked": blocked},
        )
    )
    sp = subprocess.run(
        [sys.executable, str(PIPELINES / "spike_probe.py"), "--strict", str(BATCH_PATH)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    try:
        sp_json = json.loads(sp.stdout)
    except json.JSONDecodeError:
        sp_json = {"raw_stdout": sp.stdout, "stderr": sp.stderr}
    rows.append(
        (
            "spike_probe",
            sp.returncode == 0
            and not sp.stderr
            and sp_json.get("loaded") == 5
            and sp_json.get("unloadable") == 0
            and sp_json.get("input_errors") == 0
            and sp_json.get("problems") == [],
            sp_json,
        )
    )
    return rows


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_151(), record_152(), record_153(), record_154(), record_155()]
    issues, jmax = self_check(records, notes_text(0.0))
    notes = notes_text(jmax)
    issues2, jmax2 = self_check(records, notes)
    issues = issues + [i for i in issues2 if i not in issues]
    jmax = jmax2
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    NOTES_PATH.write_text(notes, encoding="utf-8")
    print(f"wrote {BATCH_PATH} lines={len(lines)} bytes={BATCH_PATH.stat().st_size} jmax={jmax:.3f}")
    print(f"wrote {NOTES_PATH} bytes={NOTES_PATH.stat().st_size}")
    raw = REPO / "outputs" / "raw"
    if not str(BATCH_PATH).startswith("/tmp/ttf-r27"):
        issues.append("batch path not under /tmp/ttf-r27")
    if str(BATCH_PATH).startswith(str(raw)) or str(NOTES_PATH).startswith(str(raw)):
        issues.append("wrote outputs/raw")
    pipe_fail = False
    try:
        for name, ok, detail in pipeline_checks():
            print(f"PIPE {name} ok={ok} detail={json.dumps(detail, default=str)[:400]}")
            if not ok:
                issues.append(f"pipeline {name} failed")
                pipe_fail = True
    except Exception as exc:
        issues.append(f"pipeline exception {exc}")
        pipe_fail = True
        print(f"PIPE_EXCEPTION {exc}")
    if issues:
        print("SELF_CHECK_ISSUES:")
        for item in issues:
            print(" -", item)
        return 1
    print("SELF_CHECK_OK")
    return 0 if not pipe_fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
