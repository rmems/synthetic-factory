#!/usr/bin/env python3
"""Emit TTF r20 JSONL (ttf-r20-116..120) into /tmp/ttf-r20/. Never writes outputs/raw/."""

from __future__ import annotations

import json
import math
import random
import re
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

OUT_DIR = Path("/tmp/ttf-r20")
BATCH_PATH = OUT_DIR / "batch-r20.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r20.md"

PJ_PER_SPIKE = 23
RIGHTS = OrderedDict(
    [
        ("provider", "SpaceXAI/xAI"),
        ("model", "grok-4.6"),
        ("channel", "consumer"),
        ("subscription_plan", "SuperGrok Heavy"),
        ("generation_surface", "SuperGrok Heavy chat"),
        ("generated_at", "2026-09-02T21:50:00Z"),
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
HEADS = ["task_progress", "safety", "efficiency", "coherence", "exploration"]


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


def lif_117_excerpt():
    """Independent CUBA LIF (seed 20117). Plant remains designed."""

    n = 88
    dt_us = 100
    tau_m_ms = 20.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.90
    i_stim_peak = 2.2
    stim = (25000, 28000)
    seed = 20117
    window_us = 34000
    i_clamp_extra = 0.68
    clamp_n = 18
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
    early = [(t, nid) for t, nid in spikes if t < 25000]
    burst = [(t, nid) for t, nid in spikes if 25000 <= t < 28000]
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
            if len([1 for t, _ in picked if (t < 25000) == (pool[0][0] < 25000)]) >= want:
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
    take(burst, 9, label_times=(26400, 26800, 27400))
    clamp = [(t, n) for t, n in picked if t < 25000][:7]
    oxygen = [(t, n) for t, n in picked if t >= 25000][:9]
    picked = sorted(clamp + oxygen, key=lambda item: (item[0], item[1]))
    channels = ["lif.clamp" if t < 25000 else "lif.oxygen" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", n),
            ("dt_us", dt_us),
            ("tau_m_ms", tau_m_ms),
            ("v_rest", 0.0),
            ("v_reset", v_reset),
            ("v_th", v_th),
            ("r_m", 1.0),
            ("refractory_us", refractory_us),
            ("i_bias", i_bias),
            ("i_stim_peak", i_stim_peak),
            ("stim_t_us", [stim[0], stim[1]]),
            ("i_clamp_extra", i_clamp_extra),
            ("clamp_n", clamp_n),
            ("seed", seed),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-17 carry +0.68 clamp-pathway bias; stim 25-28 ms is the O2 burst.",
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
    return excerpt_items(picked, channels), extra, spikes


def meta_block(
    domain,
    tags,
    distillation_value,
    batch_position,
    supervisor_error_type=None,
) -> OrderedDict:
    body = OrderedDict(
        [
            ("round", 20),
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
    sums = {h: Decimal("0") for h in HEADS}
    for item in ticks:
        for h in HEADS:
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
        window_s = None
    return body


def record_116():
    ticks = [
        tick(1880, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(5140, 0.08, 0.06, 0.03, 0.02, 0.02),
        tick(5338, 0.05, 0.04, 0.02, 0.02, 0.01),
        tick(5620, 0.12, 0.10, 0.06, 0.04, 0.02),
        tick(6100, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(360000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    excerpt = excerpt_items(
        [
            (800, 4),
            (2100, 19),
            (3900, 33),
            (5700, 8),
            (7900, 41),
            (10200, 12),
            (12800, 27),
            (15500, 50),
            (18300, 3),
            (21100, 22),
            (23900, 45),
            (25500, 15),
        ]
    )
    params = OrderedDict(
        [
            ("speed_m_s", 8.0),
            ("panto_force_N", 38.0),
            ("cat_voltage_V", 680.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Magpie-5 already has both poles on the Bracken-Wire BW-2 750 V DC depot loop "
                "while the pantograph load cell still reports 38.0 N. A 680 V sag packet races "
                "the force pulse. Force-first confirms the already-legal 8.0 m/s creep; "
                "voltage-first would treat the sag as an imminent lift-off.",
            ),
            ("domain", "trolleybus"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Creep the depot loop at 8.0 m/s, keep pantograph force <= 55 N, and keep "
                "catenary voltage >= 550 V DC.",
            ),
            ("t0_us", 1756794621000116),
            ("gate_latency_us", 480),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.0, 5.36]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "panto.contact.n 38.0 N on the carbon shoe",
                                "cat.voltage.dc 680 V sag packet",
                            ],
                        ),
                        (
                            "semantics",
                            "Force-first confirms the already-legal 8.0 m/s creep; voltage-first "
                            "would treat a 680 V sag as lift-off and look for a hold the proposal "
                            "does not need.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one pantograph load-cell sample minus catenary PT group delay "
                            "on this 750 V depot bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 198 us vs combined jitter 64 us (panto 30 + PT 34): 3.1x over a "
                            "2.0x trust floor. Reversing order by < 198 us inside the 360 us window "
                            "would not make 8.0 m/s illegal; it would only delay confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "pantograph load cell, 2 kHz, 30 us jitter",
                    "catenary DC PT, 1 kHz, 34 us jitter",
                    "wheel encoder, 100 Hz (context)",
                    "shoe temperature (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("panto_spark_lift_N", 55.0),
                        ("observed_panto_N", 38.0),
                        ("cat_voltage_floor_V", 550.0),
                        ("observed_cat_V", 680.0),
                        ("proposed_speed_m_s", 8.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Magpie-5 poles on BW-2; carbon shoe seated on the 750 V loop.",
                    "2. Proposed 8.0 m/s creep; panto 38.0 N; catenary 680 V.",
                    "3. Wheel-encoder precursor at 1.880 ms.",
                    "4. Race window [5.000, 5.360] ms.",
                    "5. Pantograph force 38.0 N at 5.140 ms (winner).",
                    "6. Catenary 680 V at 5.338 ms (loser by 198 us).",
                    "7. Gate at 5.620 ms: ACCEPT; executed identical to proposed.",
                    "8. Spark-lift margin 17 N; voltage 130 V over floor.",
                    "9. Depot loop completed this cycle.",
                    "10. Delayed (6 min): sister bus Magpie-6 logs the same sag-as-lift false story.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "depot_loop_creep"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("panto_force_N", 38.0),
                        ("panto_spark_lift_N", 55.0),
                        ("cat_voltage_V", 680.0),
                        ("cat_voltage_floor_V", 550.0),
                        ("speed_m_s", 8.0),
                        ("race_margin_us", 198),
                        ("combined_jitter_us", 64),
                        ("delayed_surprise_s", 360.0),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 8.0 m/s creep: 38.0 N is under the 55 N spark-lift cap and "
                "680 V is over the 550 V floor, so the sag is not a lift-off.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Pantograph 38.0 N won by 198 us and sits 17 N under the 55 N spark-lift cap. "
                "Catenary 680 V is 130 V over the 550 V floor. ACCEPT the 8.0 m/s creep; a hold "
                "is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "panto_force_N",
                            OrderedDict(
                                [
                                    ("cap", 55.0),
                                    ("observed", 38.0),
                                    ("executed", 38.0),
                                ]
                            ),
                        ),
                        (
                            "cat_voltage_V",
                            OrderedDict(
                                [
                                    ("floor", 550.0),
                                    ("observed", 680.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 198),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 3.09),
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
            ("name", "depot_loop_creep"),
            ("parameters", OrderedDict(params.items())),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 8.0 m/s creep. 38.0 N < 55 N; 680 V > 550 V.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept Magpie-5 at 8.0 m/s. Spark-lift and voltage floors held. "
                "The 680 V sag was not treated as lift-off.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("vehicle", "creep 8.0 m/s completed"),
                        ("panto", "38.0 N, 17 N under spark-lift"),
                        ("catenary", "680 V, 130 V over floor"),
                        ("mission", "depot loop done this cycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 680 V sag packet arrived 198 us after the force pulse; voltage-first would have delayed confirmation without changing legality.",
                    "Delayed (6 min): Magpie-6 on loop 2 logged the same sag-as-lift disagreement; depot policy tags 550 V as the floor, not 700 V.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "panto.contact.n (5.140 ms, 38.0 N)"),
                        ("loser", "cat.voltage.dc (5.338 ms, 680 V)"),
                        ("margin_us", 198),
                        (
                            "counterfactual_if_reversed",
                            "Voltage-first by < 198 us inside the 360 us window would still leave "
                            "38.0 N < 55 N and 680 V > 550 V; the proposal is already legal either way.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5620),
            (
                "reward_inflection_note",
                "Safety and efficiency step up at the ACCEPT gate (5.620 ms, tick 4) as the creep locks in over a false lift-off hold.",
            ),
            ("delayed_surprise_s", 360.0),
        ]
    )
    spikes = [
        spike("wheel.enc.ctx", 1.205, 0.44),
        spike("panto.contact.n", 2.410, 0.61),
        spike("cat.voltage.dc", 3.220, 0.54),
        spike("panto.contact.n", 5.140, 1.28),
        spike("cat.voltage.dc", 5.338, 1.11),
        spike("ctrl.gate", 5.620, 0.99),
        spike("panto.contact.n", 7.120, 0.80),
        spike("cat.voltage.dc", 8.880, 0.65),
        spike("ctrl.gate", 12.400, 0.84),
        spike("panto.contact.n", 16.800, 0.57),
        spike("wheel.enc.ctx", 20.110, 0.40),
        spike("cat.voltage.dc", 24.050, 0.48),
    ]
    ras = raster_core(
        26,
        52,
        38,
        51,
        routing(
            "thalamic-relay.panto-catenary",
            "spikenaut.policy.creep-go",
            [
                ("relay.panto.n", "policy.creep_go", 0.63),
                ("relay.cat.v", "policy.spark_hold", 0.28),
                ("relay.wheel.enc", "policy.creep_go", 0.11),
            ],
            "dopamine",
            0.14,
            "pre_post_stdp; DA at panto win tags creep_go, reward at loop-complete",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("creep_go", 40, 0.50, 250.0, 4),
                    pop("spark_hold", 40, 0.50, 70.0, 1),
                    pop("voltage_floor_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r20-116"),
            (
                "title",
                "Bracken-Wire BW-2 / Magpie-5: pantograph 38.0 N beats catenary 680 V by 198 us; ACCEPT already-legal 8.0 m/s creep",
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
                    "Clean ACCEPT. Tick columns sum to the five heads; total 1.12 = 0.42+0.32+0.18+0.12+0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "trolleybus",
                    [
                        "accept",
                        "trolleybus",
                        "pantograph-vs-catenary",
                        "depot-loop",
                        "designed",
                    ],
                    "Teaches that a catenary sag packet losing to a legal pantograph force does not require a lift-off hold.",
                    1,
                ),
            ),
        ]
    )


def record_117():
    excerpt, extra, _lif_spikes = lif_117_excerpt()
    ticks = [
        tick(2456, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(6180, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(6410, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(7060, 0.10, -0.06, -0.03, 0.02, -0.01),
        tick(26400, 0.05, -0.38, -0.03, 0.01, -0.02),
        tick(720000000, 0.02, -0.03, -0.01, 0.01, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Flint-11 is 14 m into the Cullet-Reach CR-6 tin bath when a laser micrometer "
                "reports ribbon width 3.28 m against a 3.20 m forming limit. Width-first latches "
                "a pull-speed clamp; bath-pyrometer-first would keep the 0.22 m/min cruise. "
                "Dissolved oxygen in the tin is not yet an observable of either race channel.",
            ),
            ("domain", "glass-float-line"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Form a 3.20 m ribbon, keep width <= 3.20 m, and leave the tin bath unmarked by "
                "nickel-sulfide seeds.",
            ),
            ("t0_us", 1756794622000117),
            ("gate_latency_us", 880),
            ("race_window_us", 420),
            ("race_window_rel_ms", [6.0, 6.42]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "laser.ribbon.w 3.28 m residual",
                                "pyro.tin.bath 1048 C still-green",
                            ],
                        ),
                        (
                            "semantics",
                            "Width-first latches pull clamp 0.22 -> 0.14 m/min and width 3.28 -> 3.12 m; "
                            "pyrometer-first keeps cruise pull on a 'bath still in spec' model.",
                        ),
                        (
                            "window_derivation",
                            "420 us = one laser-micrometer sample period minus tin-bath pyrometer "
                            "group delay on this 1 kHz lehr bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 74 us (laser 34 + pyro 40): 3.1x over a "
                            "2.0x trust floor. Reversing order by < 230 us inside the 420 us window "
                            "would have kept 0.22 m/min cruise; predicted next-sample 3.31 m > 3.20 m cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "laser ribbon-width micrometer, 1 kHz, 34 us jitter",
                    "tin-bath pyrometer, 200 Hz burst, 40 us jitter",
                    "lehr encoder (context)",
                    "tin dissolved-oxygen probe, 20 Hz (not in the race)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ribbon_width_cap_m", 3.20),
                        ("observed_width_m", 3.28),
                        ("pull_proposed_m_min", 0.22),
                        ("bath_T_C", 1048.0),
                        ("bath_T_cap_C", 1065.0),
                        ("o2_cap_ppm", 12.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Flint-11 14 m into CR-6; ribbon 3.28 m vs 3.20 m forming cap.",
                    "2. Cruise pull 0.22 m/min armed; bath 1048 C under 1065 C.",
                    "3. Lehr-encoder precursor at 2.456 ms.",
                    "4. Race window [6.000, 6.420] ms.",
                    "5. Laser width 3.28 m at 6.180 ms (winner).",
                    "6. Bath pyrometer 1048 C at 6.410 ms (loser by 230 us).",
                    "7. Gate at 7.060 ms: MODIFY clamp pull 0.22 -> 0.14 m/min, width 3.28 -> 3.12 m.",
                    "8. Clamp executes; next-sample width 3.16 m < 3.20 cap.",
                    "9. At 26.400 ms tin-bath O2 18 ppm > 12 ppm seeds a nickel-sulfide speck.",
                    "10. 12 min ribbon rework + 1 plate scrap; named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_ribbon_pull"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pull_m_min", 0.22),
                        ("width_m", 3.28),
                        ("bath_T_C", 1048.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ribbon_width_m", 3.28),
                        ("ribbon_width_cap_m", 3.20),
                        ("predicted_unclamped_next_m", 3.31),
                        ("pull_m_min", 0.22),
                        ("bath_T_C", 1048.0),
                        ("bath_T_cap_C", 1065.0),
                        ("o2_cap_ppm", 12.0),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 74),
                        ("delayed_surprise_s", 720.0),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.22 m/min cruise: bath 1048 C looks in spec, and the 3.28 m "
                "width is treated as a single-sample overshoot, not a forming excursion.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Laser width 3.28 m won by 230 us, so the ribbon is over the 3.20 m forming cap, "
                "not still approaching. Holding 0.22 m/min predicts next-sample 3.31 m > 3.20. "
                "MODIFY: pull 0.22 -> 0.14 m/min and width command 3.28 -> 3.12 m. Observed after "
                "clamp 3.16 m < 3.20. A full REJECT is not indicated: a sound ribbon accepts 0.14 m/min.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ribbon_width_m",
                            OrderedDict(
                                [
                                    ("cap", 3.20),
                                    ("observed", 3.28),
                                    ("predicted_unclamped_next", 3.31),
                                    ("clamped", 3.12),
                                    ("observed_after_clamp", 3.16),
                                ]
                            ),
                        ),
                        (
                            "pull_m_min",
                            OrderedDict(
                                [
                                    ("proposed", 0.22),
                                    ("clamped", 0.14),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 230),
                                    ("combined_jitter_us", 74),
                                    ("ratio", 3.11),
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
            ("name", "clamped_ribbon_pull"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pull_m_min", 0.14),
                        ("width_m", 3.12),
                        ("bath_T_C", 1048.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: pull 0.22 -> 0.14 m/min and width 3.28 -> 3.12 m. Process-correct vs the "
                "3.20 m cap. Tin-bath O2 burst still occurs at 26.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held width at 3.16 m. At 26.400 ms dissolved oxygen 18 ppm "
                "produced a nickel-sulfide seed. Clamp reduced pull energy; it did not dump the bath "
                "atmosphere. Partnered negative: process heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("ribbon", "clamp executed; peak 3.16 m < 3.20"),
                        ("bath", "O2 18 ppm at 26.400 ms; NiS seed"),
                        ("repair", "12 min ribbon rework + 1 plate scrap"),
                        ("mission", "forming continued; seed isolated downstream"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither laser width nor bath pyrometer predicted the oxygen charge; bath.o2.ppm is a new channel at 26.400 ms, 19.340 ms after the gate, still inside the 34 ms raster.",
                    "Delayed (12 min): 1 plate scrap and ribbon rework close the seed. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "12 min ribbon rework + 1 plate scrap after an 18 ppm O2 nickel-sulfide seed. "
                "Safety head -0.56 prices the seed; task_progress stays +0.34 because the width "
                "clamp completed under the 3.20 m cap. World loss is named here, not subtracted "
                "from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "laser.ribbon.w (6.180 ms, 3.28 m)"),
                        ("loser", "pyro.tin.bath (6.410 ms, 1048 C)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "Pyrometer-first by < 230 us inside the 420 us window would have kept "
                            "0.22 m/min cruise; predicted next-sample 3.31 m would have exceeded the "
                            "3.20 m cap even without the O2 charge. The MODIFY is still the correct "
                            "process. The seed is a later world charge either way, cheaper with the clamp.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 26400),
            (
                "reward_inflection_note",
                "Safety collapses at the 26.400 ms O2 seed (tick t_us=26400), inside the 34 ms "
                "raster. The correct MODIFY at 7.060 ms is in the same excerpt. Do not put "
                "inflection on the +12 min rework tick.",
            ),
            ("delayed_surprise_s", 720.0),
        ]
    )
    spikes = [
        spike("enc.lehr.ctx", 1.205, 0.44),
        spike("laser.ribbon.w", 2.410, 0.61),
        spike("pyro.tin.bath", 3.880, 0.52),
        spike("enc.lehr.ctx", 4.620, 0.47),
        spike("laser.ribbon.w", 6.180, 1.31),
        spike("pyro.tin.bath", 6.410, 1.18),
        spike("ctrl.gate", 7.060, 0.99),
        spike("laser.ribbon.w", 8.220, 0.84),
        spike("pyro.tin.bath", 10.440, 0.66),
        spike("ctrl.gate", 14.880, 0.88),
        spike("bath.o2.ppm", 26.400, 1.42),
        spike("bath.o2.ppm", 28.050, 0.91),
        spike("enc.lehr.ctx", 30.400, 0.41),
        spike("laser.ribbon.w", 32.200, 0.58),
    ]
    ras = raster_core(
        34,
        88,
        26,
        78,
        routing(
            "thalamic-relay.width-pyro",
            "spikenaut.policy.ribbon-clamp",
            [
                ("relay.laser.width", "policy.ribbon_clamp", 0.65),
                ("relay.pyro.bath", "policy.bath_hold", 0.31),
                ("relay.bath.o2", "policy.ribbon_clamp", -0.46),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at width win (6.180 ms) opens a 50 ms eligibility "
            "trace that still covers the 26.400 ms O2 burst",
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
                    pop("ribbon_clamp", 48, 0.50, 240.0, 5),
                    pop("bath_hold", 48, 0.50, 80.0, 2),
                    pop("width_cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r20-117"),
            (
                "title",
                "Cullet-Reach CR-6 / Flint-11: laser width beats tin pyrometer by 230 us; correct MODIFY still eats an in-window O2 seed (partnered negative total -0.34)",
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
                    "34 ms raster. total -0.34 = 0.34 + -0.56 + -0.14 + 0.06 + -0.04. Named "
                    "rework+scrap loss is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "glass-float-line",
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
                    "12 min gap.",
                    2,
                ),
            ),
        ]
    )


def record_118():
    ticks = [
        tick(1635, -0.02, 0.01, -0.03, -0.01, 0.01),
        tick(4540, -0.03, 0.01, -0.04, -0.02, 0.01),
        tick(4731, -0.02, 0.00, -0.03, -0.01, 0.01),
        tick(5780, -0.06, 0.01, -0.10, -0.04, 0.02),
        tick(6220, -0.02, 0.01, -0.04, -0.01, 0.01),
        tick(1080000000, -0.01, 0.00, -0.02, -0.01, 0.00),
    ]
    excerpt = excerpt_items(
        [
            (700, 5),
            (2100, 22),
            (3800, 41),
            (5600, 9),
            (7800, 55),
            (10100, 18),
            (12600, 33),
            (15200, 61),
            (17900, 4),
            (20400, 27),
            (22100, 48),
            (22900, 12),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Tank T-7 at Rime-Causeway RC-3 holds 18.4 kPaG of LNG boil-off while compressor "
                "C-12 already sends 1.12 kg/s. Head-PT-first should confirm the legal sendout; "
                "orifice-first is a false 'flow-as-relief' story. A 2.1 kPa head oscillation is "
                "not a PSV approach.",
            ),
            ("domain", "LNG-boiloff"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Send 1.12 kg/s BOG, keep tank head <= 25.0 kPaG PSV set, and keep flare-header "
                "flow <= 1.80 kg/s.",
            ),
            ("t0_us", 1756794623000118),
            ("gate_latency_us", 1240),
            ("race_window_us", 280),
            ("race_window_rel_ms", [4.5, 4.78]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tank.head.pt 18.4 kPaG",
                                "bog.orifice.m 1.12 kg/s",
                            ],
                        ),
                        (
                            "semantics",
                            "PT-first should confirm ACCEPT sendout at 1.12 kg/s; orifice-first is a "
                            "false flow-as-relief bind. A weak supervisor instead REJECT-holds C-12.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one tank-head PT sample versus the BOG orifice DP publisher "
                            "on this 500 kbit/s tank-farm bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 191 us vs combined jitter 62 us (PT 28 + orifice 34). Order is "
                            "correctly PT-first. The error is treating a 2.1 kPa oscillation as a "
                            "PSV approach, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "tank-head PT, 1 kHz, 28 us jitter",
                    "BOG orifice DP, 500 Hz, 34 us jitter",
                    "flare-header FT (context)",
                    "tank skin RTD (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("tank_p_kPaG", 18.4),
                        ("psv_set_kPaG", 25.0),
                        ("bog_kg_s", 1.12),
                        ("flare_cap_kg_s", 1.80),
                        ("dP_kPa", 2.1),
                        ("dP_trip_kPa", 6.0),
                        ("tank_plus_dP_kPaG", 20.5),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. T-7 at RC-3; C-12 sending 1.12 kg/s; head 18.4 kPaG.",
                    "2. Proposed sendout already under PSV 25.0 and flare 1.80.",
                    "3. Skin-RTD precursor at 1.635 ms.",
                    "4. Race window [4.500, 4.780] ms.",
                    "5. Tank PT 18.4 kPaG at 4.540 ms (winner).",
                    "6. BOG orifice 1.12 kg/s at 4.731 ms (loser by 191 us).",
                    "7. Gate at 5.780 ms: wrong REJECT holds C-12 at 0 kg/s.",
                    "8. Sendout missed; head oscillation 2.1 kPa is still under 6.0 trip.",
                    "9. 18 min missed window; tank heat-leak +1.4 kPa.",
                    "10. QA: correct gate was ACCEPT sendout 1.12 kg/s, compressor left running.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "bog_sendout"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("bog_kg_s", 1.12),
                        ("compressor_run", True),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("tank_p_kPaG", 18.4),
                        ("psv_set_kPaG", 25.0),
                        ("bog_kg_s", 1.12),
                        ("flare_cap_kg_s", 1.80),
                        ("dP_kPa", 2.1),
                        ("dP_trip_kPa", 6.0),
                        ("tank_plus_dP_kPaG", 20.5),
                        ("race_margin_us", 191),
                        ("combined_jitter_us", 62),
                        ("delayed_surprise_s", 1080.0),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.12 kg/s sendout: 18.4 kPaG < 25.0 PSV, 1.12 < 1.80 flare cap, "
                "and 18.4 + 2.1 = 20.5 still under the PSV set.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Tank-head PT 18.4 kPaG is climbing 2.1 kPa this scan toward the 25.0 kPaG PSV. "
                "Hold BOG C-12 at 0 kg/s until the head settles; a sendout through a rising head "
                "is a PSV near-miss.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tank_head_kPaG",
                            OrderedDict(
                                [
                                    ("psv_set", 25.0),
                                    ("observed", 18.4),
                                    ("dP", 2.1),
                                    ("observed_plus_dP", 20.5),
                                    ("executed_hold", True),
                                ]
                            ),
                        ),
                        (
                            "bog_kg_s",
                            OrderedDict(
                                [
                                    ("proposed", 1.12),
                                    ("flare_cap", 1.80),
                                    ("executed", 0.0),
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
            ("name", "bog_hold_wrong_reject"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("bog_kg_s", 0.0),
                        ("compressor_run", False),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): C-12 held at 0 kg/s; sendout abandoned. Routing "
                "relay.tank.pt -> policy.bog_hold; no positive weight to policy.bog_sendout.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT held C-12 while tank head 18.4 kPaG and BOG 1.12 kg/s were both "
                "legal. Missed 18 min sendout; heat-leak +1.4 kPa. Correct gate was ACCEPT "
                "sendout 1.12 kg/s, compressor left running.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("compressor", "held at 0 kg/s; 1.12 kg/s abandoned"),
                        ("tank", "18.4 kPaG, still 6.6 kPa under PSV"),
                        ("flare", "header idle; cap unused"),
                        ("window", "18 min sendout missed"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 2.1 kPa oscillation never crossed the 6.0 kPa trip; 18.4 + 2.1 = 20.5 stayed under 25.0 PSV.",
                    "Delayed (18 min): next cooldown 6.4 h; heat-leak +1.4 kPa logged as a missed-window cost, not a PSV event.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT sendout at 1.12 kg/s; leave compressor C-12 running. Do not hold on a 2.1 kPa oscillation.",
                        ),
                        ("correct_actuator", "bog_sendout"),
                        ("wrong_actuator", "bog_hold"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("bog_kg_s", 0.0), ("compressor_run", False)]),
                        ),
                        (
                            "cost",
                            "Missed 18 min sendout + tank heat-leak +1.4 kPa + next cooldown 6.4 h (task/efficiency); PSV never approached (false safety).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tank.head.pt (4.540 ms, 18.4 kPaG)"),
                        ("loser", "bog.orifice.m (4.731 ms, 1.12 kg/s)"),
                        ("margin_us", 191),
                        (
                            "counterfactual_if_reversed",
                            "Orifice-first by < 191 us would still leave 1.12 < 1.80 and 18.4 < 25.0; "
                            "a correct gate ACCEPTs the sendout either way. The wrong REJECT spent the PT win on a hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5780),
            (
                "reward_inflection_note",
                "Task, efficiency, and coherence drop at the wrong REJECT (5.780 ms, tick 4). The 18 min missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 1080.0),
        ]
    )
    spikes = [
        spike("tank.dP.ctx", 1.088, 0.43),
        spike("tank.head.pt", 2.410, 0.62),
        spike("bog.orifice.m", 3.220, 0.55),
        spike("tank.dP.ctx", 4.018, 0.41),
        spike("tank.head.pt", 4.540, 1.34),
        spike("bog.orifice.m", 4.731, 1.12),
        spike("ctrl.gate", 5.780, 0.97),
        spike("tank.head.pt", 7.120, 0.81),
        spike("bog.orifice.m", 8.880, 0.66),
        spike("ctrl.gate", 12.400, 0.84),
        spike("tank.head.pt", 16.800, 0.58),
        spike("tank.dP.ctx", 20.110, 0.39),
    ]
    ras = raster_core(
        23,
        70,
        42,
        68,
        routing(
            "relay.tank.pt",
            "policy.bog_hold",
            [
                ("relay.tank.pt", "policy.bog_hold", 0.69),
                ("bog.orifice.m", "policy.bog_hold", 0.21),
            ],
            "acetylcholine",
            0.08,
            "psv_false_trip_stdp; ACh tags the (wrong) bog_hold bind at the PT win",
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
                    pop("bog_hold", 48, 0.50, 280.0, 4),
                    pop("bog_sendout", 48, 0.80, 10.0, 0),
                    pop("pop_tank_pt", 32, 0.55, 180.0, 2),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r20-118"),
            (
                "title",
                "WRONG-REJECT at Rime-Causeway RC-3 / T-7: tank 18.4 kPaG and BOG 1.12 kg/s are legal; oscillation treated as PSV approach",
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
                    "Wrong-reject. Sidecar arithmetic 18.4 < 25.0 and 1.12 < 1.80 is true; hold bound to C-12. "
                    "total -0.42 = -0.16 + 0.04 + -0.26 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "LNG-boiloff",
                    [
                        "reject",
                        "wrong-gate",
                        "wrong-reject",
                        "oscillation-as-psv",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that tank_p < psv and bog < flare_cap can still be a wrong gate when "
                    "routing.table[0].to is policy.bog_hold and executed bog_kg_s is 0.",
                    3,
                    supervisor_error_type="wrong-reject",
                ),
            ),
        ]
    )


def record_119():
    ticks = [
        tick(1880, 0.01, 0.04, 0.02, 0.01, 0.01),
        tick(5088, 0.02, 0.08, 0.03, 0.02, 0.01),
        tick(5244, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(6488, 0.04, 0.14, 0.04, 0.04, 0.02),
        tick(6920, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(540000000, 0.01, 0.02, 0.01, 0.01, 0.00),
    ]
    excerpt = excerpt_items(
        [
            (1100, 14),
            (3500, 81),
            (6200, 3),
            (8900, 120),
            (11800, 47),
            (15100, 99),
            (18600, 8),
            (22200, 131),
            (25900, 33),
            (29700, 70),
            (33600, 139),
            (37500, 22),
            (41400, 88),
            (45200, 5),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Weld head WH-6 sits on a 2.1 m girth seam inside Abyss-Joint AJ-2 at 4.8 bar "
                "when an acoustic-emission counter reports 42 hydrogen-crack pulses per second. "
                "AE-first latches a no-strike hold; chamber-pressure-first would treat 4.8 bar as "
                "still under the 6.0 bar working limit and strike 180 A.",
            ),
            ("domain", "hyperbaric-weld"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Do not strike the girth seam unless hydrogen AE <= 15 pps and chamber pressure "
                "<= 6.0 bar; keep current 0 A until the AE burst clears.",
            ),
            ("t0_us", 1756794624000119),
            ("gate_latency_us", 1400),
            ("race_window_us", 310),
            ("race_window_rel_ms", [5.0, 5.31]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.h2.pps 42 hydrogen-crack pulses/s",
                                "chamb.p.bar 4.8 bar working",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches REJECT hold 0 A; chamber-first would strike 180 A on a "
                            "pressure-as-clearance model.",
                        ),
                        (
                            "window_derivation",
                            "310 us = one AE burst bin versus the chamber PT publisher on this "
                            "habitat weld bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 156 us vs combined jitter 58 us (AE 26 + PT 32): 2.7x over a "
                            "2.0x trust floor. Reversing order by < 156 us would have struck 180 A "
                            "with AE 42 > 15 pps cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "AE hydrogen-crack counter, 20 kHz burst, 26 us jitter",
                    "chamber PT, 1 kHz, 32 us jitter",
                    "weld-current shunt (context)",
                    "habitat O2 cell (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 15),
                        ("observed_ae_pps", 42),
                        ("chamber_working_bar", 6.0),
                        ("observed_chamber_bar", 4.8),
                        ("proposed_current_A", 180.0),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "FEM hydrogen-diffusion + AE Monte Carlo, seed 20119; 2.1 m girth, 4.8 bar He-O2, 12 AE stations; NOT a wet-stand, NOT a force-plate, NOT r13 J2 clamp",
                        ),
                        (
                            "fidelity_limits",
                            "Rigid habitat shell; no cavitation; hydrogen is a lumped diffusion field. Raster is kernelized events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. WH-6 indexed on the AJ-2 girth; chamber 4.8 bar.",
                    "2. Proposed strike 180 A; AE 42 pps vs 15 pps cap.",
                    "3. Current-shunt precursor at 1.880 ms.",
                    "4. Race window [5.000, 5.310] ms.",
                    "5. AE 42 pps at 5.088 ms (winner).",
                    "6. Chamber 4.8 bar at 5.244 ms (loser by 156 us).",
                    "7. Gate at 6.488 ms: REJECT hold 0 A; do not strike.",
                    "8. Girth unmarked this cycle; AE cap held.",
                    "9. Purge queued.",
                    "10. Delayed (9 min): habitat policy forbids treating chamber P as AE clearance.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "girth_strike"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("current_A", 180.0),
                        ("hold", False),
                        ("chamber_bar", 4.8),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 42),
                        ("ae_cap_pps", 15),
                        ("chamber_bar", 4.8),
                        ("chamber_working_bar", 6.0),
                        ("race_margin_us", 156),
                        ("combined_jitter_us", 58),
                        ("delayed_surprise_s", 540.0),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 180 A strike because chamber 4.8 bar looks under the 6.0 bar "
                "working limit, treating AE 42 pps as a noisy echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "AE 42 pps is over the 15 pps strike cap. Chamber 4.8 bar is not hydrogen "
                "clearance. REJECT: hold 0 A; do not strike 180 A on the girth. Wait for AE clear.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ae_pps",
                            OrderedDict(
                                [
                                    ("cap", 15),
                                    ("observed", 42),
                                    ("chamber_bar", 4.8),
                                ]
                            ),
                        ),
                        (
                            "current_A",
                            OrderedDict(
                                [
                                    ("proposed", 180.0),
                                    ("executed", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 156),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 2.69),
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
            ("name", "hold_for_ae_clear"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("current_A", 0.0),
                        ("hold", True),
                        ("chamber_bar", 4.8),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0 A; 180 A strike cancelled. AE 42 pps > 15 pps cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held WH-6 at 0 A. Girth unmarked this cycle; AE cap held. "
                "Chamber 4.8 bar was not treated as hydrogen clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("weld", "held; current 0 A"),
                        ("ae", "42 pps uncleared this cycle"),
                        ("chamber", "4.8 bar unused as clearance"),
                        ("mission", "strike deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "AE won the 310 us race even though chamber P was 1.2 bar under working; pressure is not an AE substitute.",
                    "Delayed (9 min): 9 min He purge plus AE re-baseline; habitat policy update forbids treating chamber P as hydrogen clearance.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.h2.pps (5.088 ms, 42 pps)"),
                        ("loser", "chamb.p.bar (5.244 ms, 4.8 bar)"),
                        ("margin_us", 156),
                        (
                            "counterfactual_if_reversed",
                            "Chamber-first by < 156 us inside the 310 us window would have struck "
                            "180 A with AE 42 > 15 pps cap. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6488),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (6.488 ms, tick 4) as the hold locks in over the illegal strike.",
            ),
            ("delayed_surprise_s", 540.0),
        ]
    )
    spikes = [
        spike("weld.i.ctx", 1.205, 0.42),
        spike("ae.h2.pps", 2.410, 0.58),
        spike("chamb.p.bar", 3.105, 0.51),
        spike("ae.h2.pps", 5.088, 1.29),
        spike("chamb.p.bar", 5.244, 1.14),
        spike("ctrl.gate", 6.488, 1.02),
        spike("ae.h2.pps", 7.880, 0.77),
        spike("weld.i.ctx", 9.440, 0.46),
        spike("chamb.p.bar", 12.020, 0.61),
        spike("ctrl.gate", 16.880, 0.85),
        spike("ae.h2.pps", 24.400, 0.55),
        spike("weld.i.ctx", 38.110, 0.38),
        spike("chamb.p.bar", 44.200, 0.44),
    ]
    ras = raster_core(
        46,
        140,
        20,
        129,
        routing(
            "thalamic-relay.ae-chamber",
            "spikenaut.policy.weld-hold",
            [
                ("relay.ae.h2", "policy.weld_hold", 0.67),
                ("relay.chamb.p", "policy.strike_go", 0.27),
                ("relay.weld.i", "policy.weld_hold", 0.10),
            ],
            "serotonin",
            0.18,
            "pre_post_stdp; 5-HT at AE win tags weld_hold, reward at girth-unmarked",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.31),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("weld_hold", 64, 0.50, 260.0, 5),
                    pop("strike_go", 64, 0.50, 50.0, 1),
                    pop("ae_cap_veto", 32, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r20-119"),
            (
                "title",
                "Abyss-Joint AJ-2 / WH-6: AE 42 pps beats chamber 4.8 bar by 156 us; REJECT hold, do not strike",
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
                    "Clean REJECT. Task incomplete (girth unmarked); cap held. "
                    "total 0.78 = 0.10 + 0.38 + 0.14 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "hyperbaric-weld",
                    [
                        "reject",
                        "simulated",
                        "hyperbaric-weld",
                        "ae-vs-chamber",
                        "no-strike",
                    ],
                    "Teaches that chamber pressure under a working limit is not hydrogen-AE clearance when AE exceeds the strike cap.",
                    4,
                ),
            ),
        ]
    )


def record_120():
    ticks = [
        tick(1635, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(4088, 0.08, 0.06, 0.03, 0.02, 0.02),
        tick(4201, 0.05, 0.04, 0.02, 0.02, 0.01),
        tick(4598, 0.12, 0.10, 0.06, 0.04, 0.02),
        tick(5120, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(480000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    excerpt = excerpt_items(
        [
            (600, 2),
            (1900, 17),
            (3600, 29),
            (5400, 6),
            (7600, 31),
            (9900, 11),
            (12300, 24),
            (14800, 34),
            (17400, 4),
            (19900, 20),
            (20900, 8),
        ]
    )
    params = OrderedDict(
        [
            ("track_rate_deg_s", 0.05),
            ("az_err_arcsec", 4.2),
            ("imu_rate_deg_s", 0.18),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Dish-9 on the Gnomon-Well GW-HIL alt-az pad holds 4.2 arcsec of azimuth error "
                "while an injected IMU packet claims 0.18 deg/s of rate. Encoder-first confirms "
                "the already-legal 0.05 deg/s track; IMU-first would treat the rate as a slew "
                "abort that the proposal does not need.",
            ),
            ("domain", "radio-telescope-pointing"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Track at 0.05 deg/s, keep azimuth error <= 8.0 arcsec, and keep IMU rate <= "
                "0.40 deg/s slew-abort.",
            ),
            ("t0_us", 1756794625000120),
            ("gate_latency_us", 510),
            ("race_window_us", 240),
            ("race_window_rel_ms", [4.0, 4.24]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "enc.az.err 4.2 arcsec",
                                "imu.az.rate 0.18 deg/s injected",
                            ],
                        ),
                        (
                            "semantics",
                            "Encoder-first confirms the already-legal 0.05 deg/s track; IMU-first "
                            "would treat 0.18 deg/s as a slew abort the proposal does not need.",
                        ),
                        (
                            "window_derivation",
                            "240 us = one 26-bit tape-encoder slot versus the IMU packet on this "
                            "HIL injection bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 113 us vs combined jitter 44 us (encoder 20 + IMU 24): 2.6x over "
                            "a 2.0x trust floor. Pad injects the IMU 120-160 us before the encoder "
                            "volume (geometric lag, not a sensor fault); the IMU packet is still "
                            "the loser in this 240 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "26-bit tape encoder azimuth error, 1 kHz, 20 us jitter",
                    "IMU rate injection, 400 Hz, 24 us jitter",
                    "elevation encoder (context)",
                    "wind vane on the mock dish (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("az_err_cap_arcsec", 8.0),
                        ("observed_az_err_arcsec", 4.2),
                        ("slew_abort_deg_s", 0.40),
                        ("observed_imu_rate_deg_s", 0.18),
                        ("proposed_track_deg_s", 0.05),
                        ("imu_inject_lead_us", [120, 160]),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Dish-9 on GW-HIL pad; alt-az armed; IMU injection live.",
                    "2. IMU injected 120-160 us before encoder volume sees the rate packet.",
                    "3. Elevation precursor at 1.635 ms.",
                    "4. Race window [4.000, 4.240] ms.",
                    "5. Encoder 4.2 arcsec at 4.088 ms (winner).",
                    "6. IMU 0.18 deg/s at 4.201 ms (loser by 113 us).",
                    "7. Gate at 4.598 ms: ACCEPT; executed identical to proposed 0.05 deg/s track.",
                    "8. Pointing 4.2 < 8.0; rate 0.18 < 0.40 abort.",
                    "9. Track held this cycle.",
                    "10. Delayed (8 min): pad recal + marker re-stick; policy tags IMU-rate as non-abort under 0.40.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "az_track_hold"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("az_err_arcsec", 4.2),
                        ("az_err_cap_arcsec", 8.0),
                        ("imu_rate_deg_s", 0.18),
                        ("slew_abort_deg_s", 0.40),
                        ("track_rate_deg_s", 0.05),
                        ("race_margin_us", 113),
                        ("combined_jitter_us", 44),
                        ("delayed_surprise_s", 480.0),
                        ("abort_s", 480.0),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.05 deg/s track: 4.2 arcsec is under the 8.0 arcsec cap and "
                "0.18 deg/s is under the 0.40 slew-abort floor.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Encoder 4.2 arcsec won by 113 us and sits 3.8 arcsec under the 8.0 cap. IMU "
                "0.18 deg/s is under the 0.40 slew-abort floor. ACCEPT the 0.05 deg/s track; a "
                "slew abort is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "az_err_arcsec",
                            OrderedDict(
                                [
                                    ("cap", 8.0),
                                    ("observed", 4.2),
                                    ("executed", 4.2),
                                ]
                            ),
                        ),
                        (
                            "imu_rate_deg_s",
                            OrderedDict(
                                [
                                    ("abort_floor", 0.40),
                                    ("observed", 0.18),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 113),
                                    ("combined_jitter_us", 44),
                                    ("ratio", 2.57),
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
            ("name", "az_track_hold"),
            ("parameters", OrderedDict(params.items())),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 0.05 deg/s track. 4.2 < 8.0 arcsec; 0.18 < 0.40 deg/s.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept Dish-9 at 0.05 deg/s. Pointing and slew-abort floors held. "
                "The injected IMU rate was not treated as a slew abort.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("dish", "track 0.05 deg/s held"),
                        ("encoder", "4.2 arcsec, 3.8 under cap"),
                        ("imu", "0.18 deg/s unused as abort"),
                        ("mission", "track continued this cycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: IMU was injected 120-160 us before the encoder volume, yet encoder error still won the 240 us race.",
                    "Delayed (8 min): pad recal + marker re-stick; policy forbids treating IMU rate under 0.40 deg/s as a slew abort.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "enc.az.err (4.088 ms, 4.2 arcsec)"),
                        ("loser", "imu.az.rate (4.201 ms, 0.18 deg/s)"),
                        ("margin_us", 113),
                        (
                            "counterfactual_if_reversed",
                            "IMU-first by < 113 us inside the 240 us window would still leave "
                            "4.2 < 8.0 arcsec and 0.18 < 0.40 deg/s; the proposal is already legal either way.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4598),
            (
                "reward_inflection_note",
                "Safety and efficiency step up at the ACCEPT gate (4.598 ms, tick 4) as the track locks in over a false slew abort.",
            ),
            ("delayed_surprise_s", 480.0),
        ]
    )
    spikes = [
        spike("enc.el.ctx", 1.088, 0.44),
        spike("enc.az.err", 2.410, 0.60),
        spike("imu.az.rate", 3.220, 0.53),
        spike("enc.el.ctx", 3.618, 0.46),
        spike("enc.az.err", 4.088, 1.27),
        spike("imu.az.rate", 4.201, 1.09),
        spike("ctrl.gate", 4.598, 0.98),
        spike("enc.az.err", 6.880, 0.80),
        spike("imu.az.rate", 8.440, 0.64),
        spike("enc.el.ctx", 11.020, 0.48),
        spike("ctrl.gate", 14.880, 0.86),
        spike("enc.az.err", 18.210, 0.40),
    ]
    ras = raster_core(
        21,
        36,
        50,
        38,
        routing(
            "thalamic-relay.encoder-imu",
            "spikenaut.policy.track-go",
            [
                ("relay.enc.az", "policy.track_go", 0.62),
                ("relay.imu.rate", "policy.slew_hold", 0.29),
                ("relay.enc.el", "policy.slew_hold", -0.22),
            ],
            "dopamine",
            0.12,
            "pre_post_stdp; DA at encoder win tags track_go, reward at pointing-held",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.24),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("track_go", 32, 0.50, 280.0, 2),
                    pop("slew_hold", 32, 0.50, 80.0, 1),
                    pop("point_cap_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r20-120"),
            (
                "title",
                "Gnomon-Well GW-HIL / Dish-9: encoder 4.2 arcsec beats IMU 0.18 deg/s by 113 us; ACCEPT already-legal 0.05 deg/s track",
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
                    "Clean ACCEPT. Tick columns sum to the five heads; total 1.08 = 0.40+0.30+0.18+0.12+0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "radio-telescope-pointing",
                    [
                        "accept",
                        "hil",
                        "radio-telescope-pointing",
                        "encoder-vs-imu",
                        "alt-az-pad",
                    ],
                    "Teaches that an injected IMU rate under the slew-abort floor losing to a legal encoder error does not require a track abort.",
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


def walk_keys(obj):
    found = set()
    if isinstance(obj, dict):
        found.update(obj.keys())
        for v in obj.values():
            found.update(walk_keys(v))
    elif isinstance(obj, list):
        for v in obj:
            found.update(walk_keys(v))
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
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r20-118":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r20-120"]:
        issues.append(f"hil set {hil}")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    ids = [r["id"] for r in records]
    if ids != [f"ttf-r20-{n}" for n in range(116, 121)]:
        issues.append(f"ids {ids}")
    domains = [r["state"]["domain"] for r in records]
    expected_domains = [
        "trolleybus",
        "glass-float-line",
        "LNG-boiloff",
        "hyperbaric-weld",
        "radio-telescope-pointing",
    ]
    if domains != expected_domains:
        issues.append(f"domains {domains}")
    if len(set(domains)) != 5:
        issues.append("domain collision")
    rights_keys = list(RIGHTS.keys())
    for rec in records:
        if rec["meta"]["round"] != 20:
            issues.append(f"{rec['id']} round")
        if rec["meta"]["rights"] != RIGHTS:
            issues.append(f"{rec['id']} rights mismatch")
        if list(rec["meta"]["rights"].keys()) != rights_keys:
            issues.append(f"{rec['id']} rights key order")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            issues.append(f"{rec['id']} intended_use")
        keys = walk_keys(rec)
        for ban in ("thought", "chain_of_thought", "scratch", "inner_monologue", "training_ready"):
            if ban in keys:
                issues.append(f"{rec['id']} banned key {ban}")
        err = check_refractory(rec["spike_events"])
        if err:
            issues.append(f"{rec['id']} refractory {err}")
        n_spikes = len(rec["spike_events"])
        if not (5 <= n_spikes <= 40):
            issues.append(f"{rec['id']} spike count {n_spikes}")
        err = check_race(rec)
        if err:
            issues.append(f"{rec['id']} {err}")
        lat = rec["state"]["gate_latency_us"]
        win = rec["state"]["race_window_us"]
        if not (50 <= lat <= 2000):
            issues.append(f"{rec['id']} gate_latency")
        if not (50 <= win <= 1000):
            issues.append(f"{rec['id']} race_window")
        n = rec["raster"]["neurons"]
        rate = rec["raster"]["mean_rate_hz"]
        window_s = rec["raster"]["window_s"]
        expected = round(n * rate * window_s)
        if abs(rec["raster"]["spikes"] - expected) > 1:
            issues.append(f"{rec['id']} spike budget {rec['raster']['spikes']} vs {expected}")
        if rec["raster"]["energy_pJ"] != rec["raster"]["spikes"] * 23:
            issues.append(f"{rec['id']} energy_pJ")
        overlap = excerpt_vs_spikes(rec)
        if rec["id"] == "ttf-r20-117":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("117 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("117 inflection outside window")
        elif overlap >= 0.8:
            issues.append(f"{rec['id']} excerpt overlap {overlap:.2f}")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_times = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_times:
            issues.append(f"{rec['id']} inflection {inf} not a tick")
        if len(rec["reward_components"]["ticks"]) != 6:
            issues.append(f"{rec['id']} tick count")
        delay = rec["future_outcome"]["delayed_surprise_s"]
        if tick_times[-1] != int(round(delay * 1e6)):
            issues.append(f"{rec['id']} tick6 vs delayed_surprise_s")
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rec['id']} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rec['id']} gate_snn decision mismatch")
        total = sum(rec["reward_components"][h] for h in HEADS)
        if abs(total - rec["reward_components"]["total"]) > 1e-6:
            issues.append(f"{rec['id']} total mismatch {total}")
        for h in HEADS:
            s = sum(t[h] for t in rec["reward_components"]["ticks"])
            if abs(s - rec["reward_components"][h]) > 1e-6:
                issues.append(f"{rec['id']} {h} tick sum {s} vs {rec['reward_components'][h]}")
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rec['id']} training_ready present")
        if '"real"' in blob and rec["state"]["sim_or_real"] != "real":
            # allow the word in prose? avoid false positive on "already"
            pass
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
        if rec["id"] == "ttf-r20-118":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["tank_p_kPaG"] < ev["psv_set_kPaG"]):
                issues.append("118 tank not under PSV")
            if not (ev["bog_kg_s"] < ev["flare_cap_kg_s"]):
                issues.append("118 bog not under flare")
            if not (ev["dP_kPa"] < ev["dP_trip_kPa"]):
                issues.append("118 dP not under trip")
            if rec["executed_action"]["parameters"]["bog_kg_s"] != 0.0:
                issues.append("118 executed not hold")
            tos = [row["to"] for row in rec["raster"]["routing"]["table"]]
            if "policy.bog_hold" not in tos:
                issues.append("118 missing bog_hold route")
            if any(row["to"] == "policy.bog_sendout" and row["weight"] > 0 for row in rec["raster"]["routing"]["table"]):
                issues.append("118 positive sendout weight")
            if "recovery" not in rec["future_outcome"]:
                issues.append("118 missing recovery")
        for ev in rec["spike_events"]:
            times = [e["t_rel_ms"] for e in rec["spike_events"]]
        if times != sorted(times):
            issues.append(f"{rec['id']} spike order")
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= rec["raster"]["window_ms"] * 1000):
                issues.append(f"{rec['id']} excerpt t_us")
            if not (0 <= item["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rec['id']} neuron_id")
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for p in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in p or "spikes" in p:
                exp = round(p["neurons"] * p["mean_rate_hz"] * dw_s)
                if abs(p["spikes"] - exp) > 1:
                    issues.append(f"{rec['id']} pop {p['name']} spikes {p['spikes']} vs {exp}")
    return issues, jmax


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_116(), record_117(), record_118(), record_119(), record_120()]
    issues, jmax = self_check(records)
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {BATCH_PATH} lines={len(lines)} jmax={jmax:.3f}")
    if issues:
        print("SELF_CHECK_ISSUES:")
        for item in issues:
            print(" -", item)
        return 1
    print("SELF_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
