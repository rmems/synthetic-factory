#!/usr/bin/env python3
"""Emit TTF r13 JSONL (ttf-r13-081..085) into /tmp/ttf-r13/. Never writes outputs/raw/."""

from __future__ import annotations

import json
import math
import random
import re
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

OUT_DIR = Path("/tmp/ttf-r13")
BATCH_PATH = OUT_DIR / "batch-r13.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r13.md"

PJ_PER_SPIKE = 23
RIGHTS = OrderedDict(
    [
        ("provider", "SpaceXAI/xAI"),
        ("model", "grok-4.6"),
        ("channel", "consumer"),
        ("subscription_plan", "SuperGrok Heavy"),
        ("generation_surface", "SuperGrok Heavy chat"),
        ("generated_at", "2026-09-02T18:45:00Z"),
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


def D(*parts: str) -> float:
    acc = Decimal("0")
    for part in parts:
        acc += Decimal(part)
    return float(acc)


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


def lif_081_excerpt():
    """Independent CUBA LIF using the plan sidecar params (seed 13081)."""

    n = 80
    dt_us = 100
    tau_m_ms = 20.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.92
    i_stim_peak = 2.4
    stim = (21000, 24000)
    seed = 13081
    window_us = 42000
    i_clamp_extra = 0.70
    clamp_n = 16
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
            if len([1 for t, _ in picked if (t < 21000) == (pool[0][0] < 21000)]) >= want:
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
    take(burst, 9, label_times=(22100, 22400, 23000))
    picked.sort(key=lambda item: (item[0], item[1]))
    # Keep 16, unique neurons, clamp then tear.
    clamp = [(t, n) for t, n in picked if t < 21000][:7]
    tear = [(t, n) for t, n in picked if t >= 21000][:9]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    channels = ["lif.clamp" if t < 21000 else "lif.tear" for t, _ in picked]
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
            ("i_stim_peak", 2.4),
            ("stim_t_us", [21000, 24000]),
            ("i_clamp_extra", 0.70),
            ("clamp_n", 16),
            ("seed", 13081),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-15 carry +0.70 clamp-pathway bias; stim 21-24 ms is the tear burst.",
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
            ("round", 13),
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


def record_081():
    excerpt, extra, _lif_spikes = lif_081_excerpt()
    ticks = [
        tick(2456, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(6140, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(6355, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(7060, 0.10, -0.06, -0.03, 0.02, -0.01),
        tick(22100, 0.07, -0.42, -0.04, 0.00, -0.02),
        tick(480000000, 0.02, -0.05, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Calyx-9 occupies a 3 mm right-subcostal port in Nacre-Well Theatre 2 "
                "while the insertion axis still holds 2.40 N toward a 4.2 mm hepatic-vein "
                "tributary standoff. A tremor-filtered 6-DoF wrist still carries a 4.1 Hz "
                "residual. Force-first latches a process clamp under the 1.50 N cap; "
                "tremor-first would keep cruise insertion. Stored elastic energy in the "
                "vessel wall is not yet an observable of either race channel.",
            ),
            ("domain", "surgical-assist"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Reach the right hepatic vein tributary at 4.2 mm standoff, keep insertion "
                "force <= 1.50 N, and leave the adventitia unmarked.",
            ),
            ("t0_us", 1756794621000081),
            ("gate_latency_us", 920),
            ("race_window_us", 380),
            ("race_window_rel_ms", [6.0, 6.38]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.insert.z 2.40 N pulse",
                                "imu.tremor.band 4.1 Hz residual",
                            ],
                        ),
                        (
                            "semantics",
                            "FT-first latches insertion clamp 2.40 -> 1.10 N and 1.8 -> 0.6 mm/s; "
                            "tremor-first keeps cruise insertion on a 'still approaching' model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one FT sample period minus tremor-band demodulation group delay "
                            "on this 1 kHz wrist bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 215 us vs combined jitter ~70 us (FT 32 + IMU 38): 3.1x over a 2.0x "
                            "trust floor. Reversing order by < 215 us inside the 380 us window would have "
                            "kept 2.40 N cruise; predicted next-sample 1.82 N > 1.50 N cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "wrist FT insert-Z, 1 kHz, 32 us timestamp jitter",
                    "IMU tremor band 4-12 Hz, 38 us jitter",
                    "optical standoff to adventitia, 200 Hz (context)",
                    "joint encoders (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("insertion_force_cap_N", 1.5),
                        ("proposed_insertion_N", 2.4),
                        ("insertion_rate_proposed_mm_s", 1.8),
                        ("standoff_mm", 4.2),
                        ("port_mm", 3.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Calyx-9 indexed through the 3 mm port; standoff 4.2 mm to the tributary.",
                    "2. Cruise insertion 2.40 N at 1.8 mm/s armed; tremor band 4.1 Hz residual.",
                    "3. Encoder precursor at 2.456 ms; FT warm-start 2.40 N.",
                    "4. Race window [6.000, 6.380] ms opens on the wrist bus.",
                    "5. FT insert-Z 2.40 N at 6.140 ms (winner).",
                    "6. IMU tremor band at 6.355 ms (loser by 215 us).",
                    "7. Gate at 7.060 ms (winner + 920 us): MODIFY clamp 1.10 N, 0.6 mm/s.",
                    "8. Clamp executes; next-sample force 1.18 N < 1.50 cap.",
                    "9. At 22.100 ms vessel-wall elastic recoil tears 0.6 mm adventitia; AE burst.",
                    "10. Irrigation 8 min + 6-0 suture; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_hepatic_insertion"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("insertion_N", 2.4),
                        ("insertion_mm_s", 1.8),
                        ("standoff_mm", 4.2),
                        ("tremor_filter_hz", 4.1),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ft_insert_z_N", 2.4),
                        ("insertion_cap_N", 1.5),
                        ("predicted_unclamped_next_N", 1.82),
                        ("tremor_band_hz", 4.1),
                        ("race_margin_us", 215),
                        ("combined_jitter_us", 70),
                        ("standoff_mm", 4.2),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.40 N cruise at 1.8 mm/s: tremor residual 4.1 Hz looks like "
                "approach shake, not contact, and the 4.2 mm standoff is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "FT insert-Z 2.40 N won by 215 us, so the tip is loading tissue, not still "
                "approaching. Holding 2.40 N predicts next-sample 1.82 N > 1.50 N cap. MODIFY: "
                "insertion 2.40 -> 1.10 N and 1.8 -> 0.6 mm/s. Observed after clamp 1.18 N < 1.50. "
                "A full REJECT is not indicated: a sound tributary accepts 1.10 N.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "insertion_force_N",
                            OrderedDict(
                                [
                                    ("cap", 1.5),
                                    ("observed", 2.4),
                                    ("predicted_unclamped_next", 1.82),
                                    ("clamped", 1.1),
                                    ("observed_after_clamp", 1.18),
                                ]
                            ),
                        ),
                        (
                            "insertion_mm_s",
                            OrderedDict(
                                [
                                    ("proposed", 1.8),
                                    ("clamped", 0.6),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 215),
                                    ("combined_jitter_us", 70),
                                    ("ratio", 3.07),
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
            ("name", "clamped_hepatic_insertion"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("insertion_N", 1.1),
                        ("insertion_mm_s", 0.6),
                        ("standoff_mm", 4.2),
                        ("tremor_filter_hz", 4.1),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: insertion 2.40 -> 1.10 N and 1.8 -> 0.6 mm/s. Process-correct vs the "
                "1.50 N cap. Vessel-wall tear still occurs at 22.100 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held insertion at 1.18 N. At 22.100 ms stored elastic "
                "energy produced a 0.6 mm adventitial tear / bleed pulse. Clamp reduced dump "
                "energy; it did not prevent the shear. Partnered negative: process heads stay "
                "honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("instrument", "clamp executed; peak 1.18 N < 1.50"),
                        ("vessel", "0.6 mm adventitial tear at 22.100 ms"),
                        ("repair", "8 min irrigation + 6-0 suture"),
                        ("mission", "tributary still reached; bleed controlled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither FT nor tremor predicted the wall charge; tissue.acoustic.tear is a new channel at 22.100 ms, 15.040 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (8 min): 6-0 suture and irrigation close the tear. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "8 min irrigation + 6-0 suture after a 0.6 mm adventitial tear. Safety head -0.62 "
                "prices the bleed; task_progress stays +0.36 because the force clamp completed "
                "under the 1.50 N cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.insert.z (6.140 ms, 2.40 N)"),
                        ("loser", "imu.tremor.band (6.355 ms, 4.1 Hz residual)"),
                        ("margin_us", 215),
                        (
                            "counterfactual_if_reversed",
                            "Tremor-first by < 215 us inside the 380 us window would have kept "
                            "2.40 N cruise; predicted next-sample 1.82 N would have exceeded the "
                            "1.50 N cap even without the wall charge. The MODIFY is still the "
                            "correct process. The tear is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22100),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.100 ms vessel-wall tear (tick t_us=22100), inside the "
                "42 ms raster. The correct MODIFY at 7.060 ms is in the same excerpt. Do not put "
                "inflection on the +8 min suture tick.",
            ),
        ]
    )
    spikes = [
        spike("encoder.pos.ctx", 1.205, 0.44),
        spike("ft.insert.z", 2.410, 0.61),
        spike("imu.tremor.band", 3.880, 0.52),
        spike("optical.standoff.ctx", 4.620, 0.47),
        spike("ft.insert.z", 6.140, 1.31),
        spike("imu.tremor.band", 6.355, 1.18),
        spike("ctrl.gate", 7.060, 0.99),
        spike("ft.insert.z", 8.220, 0.84),
        spike("imu.tremor.band", 10.440, 0.66),
        spike("ctrl.gate", 14.880, 0.88),
        spike("tissue.acoustic.tear", 22.100, 1.42),
        spike("tissue.acoustic.tear", 24.050, 0.91),
        spike("encoder.pos.ctx", 28.400, 0.41),
        spike("ft.insert.z", 36.200, 0.58),
    ]
    ras = raster_core(
        42,
        80,
        25,
        84,
        routing(
            "thalamic-relay.force-tremor",
            "spikenaut.policy.insert-clamp",
            [
                ("relay.ft.insert_z", "policy.insert_clamp", 0.64),
                ("relay.imu.tremor", "policy.tremor_hold", 0.33),
                ("relay.tissue.tear", "policy.insert_clamp", -0.48),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at FT win (6.140 ms) opens a 50 ms eligibility "
            "trace that still covers the 22.100 ms tear",
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
                    pop("insert_clamp", 48, 0.50, 280.0, 5),
                    pop("tremor_hold", 48, 0.50, 90.0, 2),
                    pop("force_cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r13-081"),
            (
                "title",
                "Nacre-Well Theatre 2 / Calyx-9: FT insert-Z beats tremor by 215 us; correct "
                "MODIFY still eats an in-window vessel-wall tear (partnered negative total -0.42)",
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
                    "42 ms raster. total -0.42 = 0.36 + -0.62 + -0.16 + 0.04 + -0.04. Named "
                    "irrigation+suture loss is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "surgical-assist",
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
                    "1.8 s gap.",
                    1,
                ),
            ),
        ]
    )


def record_082():
    ticks = [
        tick(2084, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(5210, -0.04, -0.03, -0.04, -0.02, 0.01),
        tick(5488, -0.03, -0.02, -0.03, -0.01, 0.01),
        tick(5850, -0.08, -0.07, -0.08, -0.04, 0.02),
        tick(6370, -0.03, -0.03, -0.04, -0.01, 0.01),
        tick(660000000, -0.02, -0.02, -0.03, -0.01, 0.00),
    ]
    excerpt = excerpt_items(
        [
            (740, 4),
            (1950, 19),
            (3400, 33),
            (4700, 8),
            (6300, 41),
            (8000, 12),
            (9600, 27),
            (11500, 50),
            (13800, 3),
            (16100, 22),
            (18400, 45),
            (20700, 15),
            (22600, 38),
            (23900, 7),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Spindle-H6 already has an 8 mm steel bushing 4.1 mm into the Quern-Forge Cell B "
                "fixture when the wrist transducer reports Fz 48.2 N against a 40.0 N tool-Z limit. "
                "J2 shoulder pitch is planned at 80 Nm, safely below its 110 Nm torque bound. "
                "FT-leading should bind a J6 press hold; a weak supervisor instead treats the "
                "contact loop as proximal J2.",
            ),
            ("domain", "industrial-assembly"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Press-fit the 8 mm steel bushing on insertion-Z, keep Fz <= 40.0 N, and leave J2 "
                "at the planned 80 Nm support torque.",
            ),
            ("t0_us", 1756794622000082),
            ("gate_latency_us", 640),
            ("race_window_us", 520),
            ("race_window_rel_ms", [5.0, 5.52]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.wrist.z 48.2 N on wrist_insert_z",
                                "enc.j2.tau 80 Nm planned",
                            ],
                        ),
                        (
                            "semantics",
                            "FT-first should latch J6 insertion clamp 48.2 -> 32 N; J2-first is a "
                            "false 'force-loop' bind that freezes shoulder pitch instead.",
                        ),
                        (
                            "window_derivation",
                            "520 us = one wrist-FT CAN slot at 500 kbit/s versus the J2 torque "
                            "publisher on this bus cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 278 us vs combined jitter 82 us (FT 40 + encoder 42). Order is "
                            "correctly FT-first. The error is which actuator the clamp is bound to, "
                            "not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "wrist 6-axis FT, 2 kHz, 40 us jitter, axis wrist_insert_z",
                    "J2 shoulder-pitch torque encoder, 1 kHz, 42 us jitter",
                    "J6 insertion linear encoder (context)",
                    "press oil-film temperature (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("insertion_cap_N", 40.0),
                        ("observed_fz_N", 48.2),
                        ("ft_axis", "wrist_insert_z"),
                        ("j2_tau_Nm", 80.0),
                        ("j2_cap_Nm", 110.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Spindle-H6 indexed; 8 mm bushing 4.1 mm into the Cell B fixture.",
                    "2. Wrist Fz 48.2 N on wrist_insert_z; J2 planned 80 Nm << 110 Nm cap.",
                    "3. Encoder precursor at 2.084 ms.",
                    "4. Race window [5.000, 5.520] ms.",
                    "5. FT wrist Z 48.2 N at 5.210 ms (winner).",
                    "6. J2 encoder 80 Nm at 5.488 ms (loser by 278 us).",
                    "7. Gate at 5.850 ms: wrong MODIFY clamps J2 80 -> 35 Nm; insert-Z stays 48.2 N.",
                    "8. Chamfer chips; J2 stalls; insertion still over cap.",
                    "9. Cell abort 11 min; bushing scrap.",
                    "10. QA: correct gate was MODIFY on J6 insertion-Z 48.2 -> 32 N, J2 left at 80 Nm.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "bushing_press_fit"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("insert_z_N", 48.2),
                        ("j2_tau_Nm", 80.0),
                        ("j6_insert_mm_s", 1.2),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("fz_N", 48.2),
                        ("ft_axis", "wrist_insert_z"),
                        ("insertion_cap_N", 40.0),
                        ("j2_tau_Nm", 80.0),
                        ("j2_cap_Nm", 110.0),
                        ("race_margin_us", 278),
                        ("combined_jitter_us", 82),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing the press at the observed 48.2 N on wrist_insert_z "
                "with J2 support at 80 Nm. The FT read is on insertion-Z, not shoulder pitch.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Fz 48.2 N exceeds the 40.0 N insertion-Z cap (true). At this pose J2 is the "
                "proximal joint in the force loop (planned 80 Nm << 110 Nm cap). Clamp J2 from "
                "80 Nm to 35 Nm to bleed insertion force before the bushing galls.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "insertion_z_N",
                            OrderedDict(
                                [
                                    ("cap", 40.0),
                                    ("observed", 48.2),
                                    ("executed", 48.2),
                                    ("ft_axis", "wrist_insert_z"),
                                ]
                            ),
                        ),
                        (
                            "j2_tau_Nm",
                            OrderedDict(
                                [
                                    ("cap", 110.0),
                                    ("planned", 80.0),
                                    ("clamped_wrong", 35.0),
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
            ("name", "j2_hold_wrong_axis"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("insert_z_N", 48.2),
                        ("j2_tau_Nm", 35.0),
                        ("j6_insert_mm_s", 1.2),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect): J2 80 -> 35 Nm; insertion-Z left at 48.2 N. Routing "
                "relay.ft.z -> policy.j2_hold; no positive weight to policy.j6_insert_clamp.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY froze J2 while insertion-Z stayed at 48.2 N over the 40.0 N cap. "
                "J2 stall plus chamfer chip; 11 min cell abort. Correct gate was MODIFY on J6 "
                "insertion-Z 48.2 -> 32 N, J2 left at 80 Nm.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("j2", "stalled at 35 Nm; planned 80 Nm abandoned"),
                        ("insert_z", "still 48.2 N, over 40.0 N cap"),
                        ("bushing", "chamfer chip; press aborted"),
                        ("cell", "11 min abort"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "J2 freeze removed Fxy compliance and did not reduce Fz; insertion stayed 48.2 N.",
                    "Delayed (11 min): Cell B abort while KS-adjacent waits on the bushing; chamfer scrap logged.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY on insertion Z / J6: Fz 48.2 -> 32 N; leave J2 at planned 80 Nm.",
                        ),
                        ("correct_actuator", "j6_insert"),
                        ("wrong_actuator", "j2"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("j2_tau_Nm", 35.0), ("insert_z_N", 48.2)]),
                        ),
                        (
                            "cost",
                            "J2 stall + chamfer chip + 11 min abort (task/efficiency); insertion still over cap (safety near-miss).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.wrist.z (5.210 ms, 48.2 N)"),
                        ("loser", "enc.j2.tau (5.488 ms, 80 Nm)"),
                        ("margin_us", 278),
                        (
                            "counterfactual_if_reversed",
                            "J2-first by < 278 us would still be under the 110 Nm J2 cap; a correct "
                            "gate binds FT to J6 insertion-Z either way. The wrong MODIFY spent the FT win on the wrong actuator.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5850),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong clamp (5.850 ms, tick 4). The 11 min abort is delayed surprise, not the inflection.",
            ),
        ]
    )
    spikes = [
        spike("enc.j6.pos.ctx", 1.088, 0.43),
        spike("ft.wrist.z", 2.410, 0.62),
        spike("enc.j2.tau", 3.220, 0.55),
        spike("press.oil.ctx", 4.018, 0.41),
        spike("ft.wrist.z", 5.210, 1.34),
        spike("enc.j2.tau", 5.488, 1.12),
        spike("ctrl.gate", 5.850, 0.97),
        spike("ft.wrist.z", 7.120, 0.81),
        spike("enc.j2.tau", 8.880, 0.66),
        spike("ctrl.gate", 12.400, 0.84),
        spike("ft.wrist.z", 16.800, 0.58),
        spike("enc.j6.pos.ctx", 20.110, 0.39),
    ]
    ras = raster_core(
        24,
        56,
        45,
        60,
        routing(
            "relay.ft.z",
            "policy.j2_hold",
            [
                ("relay.ft.z", "policy.j2_hold", 0.71),
                ("enc.j2.tau", "policy.j2_hold", 0.22),
            ],
            "acetylcholine",
            0.08,
            "force_cap_stdp; ACh tags the (wrong) j2_hold bind at the FT win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.52),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("j2_hold", 48, 0.50, 250.0, 6),
                    pop("j6_insert_clamp", 48, 0.80, 20.0, 0),
                    pop("pop_ft_z", 32, 0.55, 180.0, 3),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r13-082"),
            (
                "title",
                "WRONG-MODIFY at Quern-Forge Cell B / Spindle-H6: Fz 48.2 N read correctly; clamp applied to J2 not insertion-Z/J6",
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
                    "Wrong-modify. Sidecar arithmetic 48.2 > 40.0 is true; clamp bound to J2. "
                    "total -0.68 = -0.22 + -0.18 + -0.24 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "industrial-assembly",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-axis",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct Fz>cap read can still be a wrong gate when "
                    "routing.table[0].to is policy.j2_hold and executed insert_z_N is not reduced.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_083():
    ticks = [
        tick(1635, 0.01, 0.04, 0.02, 0.01, 0.01),
        tick(4088, 0.02, 0.08, 0.03, 0.02, 0.01),
        tick(4201, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5188, 0.03, 0.14, 0.04, 0.04, 0.02),
        tick(5428, 0.02, 0.05, 0.02, 0.01, 0.01),
        tick(420000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    excerpt = excerpt_items(
        [
            (900, 11),
            (2600, 44),
            (4300, 90),
            (5900, 7),
            (7700, 63),
            (9800, 28),
            (12200, 101),
            (14700, 15),
            (17300, 72),
            (20100, 39),
            (23000, 88),
            (26100, 4),
            (29400, 55),
            (32800, 110),
            (35100, 22),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Plover-4 sits on the Tinder-Box HIL pavement pad at an urban four-way while a "
                "belt-dummy pedestrian and an injected V2X SPaT disagree about whether the box is "
                "clear. 32-beam lidar TTC is 1.10 s; DSRC/C-V2X all-red remaining is 2.40 s. "
                "Commit at 8.0 m/s is legal only if TTC >= 1.80 s. Lidar-first latches hold; "
                "SPaT-first would treat all-red remaining as pedestrian clearance.",
            ),
            ("domain", "autonomous-driving"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not commit the four-way unless pedestrian TTC >= 1.80 s; keep speed 0.0 m/s "
                "until the belt-dummy clears.",
            ),
            ("t0_us", 1756794623000083),
            ("gate_latency_us", 1100),
            ("race_window_us", 240),
            ("race_window_rel_ms", [4.0, 4.24]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "lidar.ttc.ped 1.10 s",
                                "v2x.spat.allred 2.40 s remaining",
                            ],
                        ),
                        (
                            "semantics",
                            "Lidar-first latches REJECT hold 0.0 m/s; V2X-first would commit 8.0 m/s "
                            "on an all-red-as-clearance model.",
                        ),
                        (
                            "window_derivation",
                            "240 us = one 32-beam lidar firing slot versus DSRC SPaT decode on this "
                            "intersection cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 113 us vs combined jitter ~45 us (lidar 22 + V2X 23): 2.5x over "
                            "a 2.0x trust floor. Pad injects SPaT 140-180 us before the lidar volume "
                            "sees the dummy (geometric lag, not a sensor fault); the all-red packet "
                            "is still the loser in this 240 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "32-beam lidar TTC, 20 Hz burst, 22 us jitter",
                    "DSRC/C-V2X SPaT, 10 Hz, 23 us jitter",
                    "wheel odometry, 100 Hz (context)",
                    "belt-dummy photoelectric trip (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("commit_ttc_floor_s", 1.8),
                        ("observed_ttc_s", 1.1),
                        ("v2x_allred_remaining_s", 2.4),
                        ("proposed_speed_m_s", 8.0),
                        ("spat_inject_lead_us", [140, 180]),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Plover-4 on the Tinder-Box pad; four-way armed; dummy on the belt.",
                    "2. SPaT injected 140-180 us before dummy enters the lidar volume.",
                    "3. Wheel-odo precursor at 1.635 ms.",
                    "4. Race window [4.000, 4.240] ms.",
                    "5. Lidar TTC 1.10 s at 4.088 ms (winner).",
                    "6. V2X all-red 2.40 s at 4.201 ms (loser by 113 us).",
                    "7. Gate at 5.188 ms: REJECT hold 0.0 m/s; do not commit 8.0 m/s.",
                    "8. Dummy remains in the box this cycle; cap held.",
                    "9. Belt recycle queued.",
                    "10. Delayed (7 min): pad policy tags SPaT-all-red as non-clearance vs lidar TTC.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "commit_intersection_box"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_s", 8.0),
                        ("hold", False),
                        ("v2x_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("lidar_ttc_s", 1.1),
                        ("ttc_commit_floor_s", 1.8),
                        ("v2x_allred_remaining_s", 2.4),
                        ("race_margin_us", 113),
                        ("combined_jitter_us", 45),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 8.0 m/s through the box because V2X all-red remaining 2.40 s "
                "looks like a cleared intersection, treating lidar TTC 1.10 s as a noisy echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Lidar TTC 1.10 s is under the 1.80 s commit floor. V2X all-red remaining 2.40 s "
                "is not a pedestrian clearance. REJECT: hold 0.0 m/s; do not commit 8.0 m/s "
                "through the box. Wait for belt-dummy clear.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "pedestrian_ttc_s",
                            OrderedDict(
                                [
                                    ("floor", 1.8),
                                    ("observed_lidar", 1.1),
                                    ("v2x_allred_remaining", 2.4),
                                ]
                            ),
                        ),
                        (
                            "speed_m_s",
                            OrderedDict(
                                [
                                    ("proposed", 8.0),
                                    ("executed", 0.0),
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
            ("name", "hold_for_dummy_clear"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_s", 0.0),
                        ("hold", True),
                        ("v2x_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0.0 m/s; 8.0 m/s commit cancelled. TTC 1.10 s < 1.80 s floor.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Plover-4 at 0.0 m/s. Dummy uncleared this cycle; commit "
                "cap held. V2X all-red remaining was not treated as pedestrian clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("vehicle", "held; speed 0.0 m/s"),
                        ("dummy", "still in box this cycle"),
                        ("spat", "all-red remaining 2.40 s unused as clearance"),
                        ("mission", "commit deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: SPaT was injected 140-180 us before the dummy entered the lidar volume, yet lidar TTC still won the 240 us race.",
                    "Delayed (7 min): pad policy update forbids treating SPaT all-red remaining as a pedestrian-clearance substitute.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "lidar.ttc.ped (4.088 ms, 1.10 s TTC)"),
                        ("loser", "v2x.spat.allred (4.201 ms, 2.40 s remaining)"),
                        ("margin_us", 113),
                        (
                            "counterfactual_if_reversed",
                            "V2X-first by < 113 us inside the 240 us window would have committed "
                            "8.0 m/s with TTC 1.10 s < 1.80 s floor. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5188),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (5.188 ms, tick 4) as the hold locks in over the illegal commit.",
            ),
        ]
    )
    spikes = [
        spike("wheel.odo.ctx", 1.205, 0.42),
        spike("lidar.ttc.ped", 2.410, 0.58),
        spike("v2x.spat.allred", 3.105, 0.51),
        spike("lidar.ttc.ped", 4.088, 1.29),
        spike("v2x.spat.allred", 4.201, 1.14),
        spike("ctrl.gate", 5.188, 1.02),
        spike("lidar.ttc.ped", 6.880, 0.77),
        spike("wheel.odo.ctx", 8.440, 0.46),
        spike("v2x.spat.allred", 11.020, 0.61),
        spike("ctrl.gate", 14.880, 0.85),
        spike("lidar.ttc.ped", 22.400, 0.55),
        spike("wheel.odo.ctx", 30.110, 0.38),
    ]
    ras = raster_core(
        36,
        120,
        22,
        95,
        routing(
            "thalamic-relay.intersection-ttc",
            "spikenaut.policy.box-hold",
            [
                ("relay.lidar.ttc", "policy.hold_reject", 0.66),
                ("relay.v2x.allred", "policy.commit_go", 0.29),
                ("relay.wheel.odo", "policy.hold_reject", 0.12),
            ],
            "dopamine",
            0.20,
            "pre_post_stdp; DA at lidar TTC win tags hold_reject, reward at dummy-still-in-box",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.24),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 64, 0.50, 280.0, 4),
                    pop("commit_go", 64, 0.50, 70.0, 1),
                    pop("ttc_floor_veto", 32, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r13-083"),
            (
                "title",
                "Tinder-Box HIL / Plover-4: lidar TTC 1.10 s beats V2X all-red 2.40 s by 113 us; REJECT hold, do not commit",
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
                    "Clean REJECT. Task incomplete (dummy uncleared); cap held. "
                    "total 0.80 = 0.10 + 0.40 + 0.14 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "autonomous-driving",
                    [
                        "reject",
                        "hil",
                        "v2x-spat",
                        "lidar-ttc",
                        "intersection-hold",
                    ],
                    "Teaches that an all-red SPaT remainder is not pedestrian clearance when lidar TTC is under the commit floor.",
                    3,
                ),
            ),
        ]
    )


def record_084():
    ticks = [
        tick(2848, 0.05, 0.03, 0.02, 0.01, 0.01),
        tick(7120, 0.08, 0.05, 0.03, 0.02, 0.02),
        tick(7334, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(7500, 0.12, 0.10, 0.05, 0.04, 0.02),
        tick(7950, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(540000000, 0.04, 0.02, 0.02, 0.01, 0.01),
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
            (22200, 141),
            (25900, 33),
            (29700, 70),
            (33600, 155),
            (37500, 22),
            (41400, 88),
            (45200, 5),
            (47800, 112),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Five survey quads of Whimbrel-Stack W-12 hold 18 m AGL, 3 m below a ridge, when "
                "an advancing-blade Kulite records a BVI pressure pulse 214 us before the mast "
                "anemometer sees the gust front. The proposed trim already includes a 4 deg "
                "collective drop and 1.05 m/s climb that keeps retreating-blade stall margin "
                ">= 1.2 deg and predicted min spacing 2.11 m over the 2.00 m floor. BVI-first "
                "confirms that trim; it does not require a further clamp.",
            ),
            ("domain", "aerial-swarm"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold the five-ship survey at 18 m AGL under the ridge, keep inter-agent spacing "
                ">= 2.00 m, and keep retreating-blade stall margin >= 1.2 deg.",
            ),
            ("t0_us", 1756794624000084),
            ("gate_latency_us", 380),
            ("race_window_us", 450),
            ("race_window_rel_ms", [7.0, 7.45]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "blade.kulite.bvi advancing-blade pressure pulse",
                                "mast.anem.gust front",
                            ],
                        ),
                        (
                            "semantics",
                            "BVI-first confirms the already-legal 4 deg collective drop and 1.05 m/s "
                            "climb; gust-first would have treated the pulse as a mast-only thermal and "
                            "looked for an extra clamp that the trim does not need.",
                        ),
                        (
                            "window_derivation",
                            "450 us = one 24-azimuth-bin rotor step versus the mast anemometer front "
                            "on this rigid 4-blade disk.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 214 us vs combined jitter 68 us (Kulite 30 + anemometer 38): 3.1x "
                            "over a 2.0x trust floor. Reversing order by < 214 us would not make the "
                            "proposed trim illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "advancing-blade Kulite BVI, 24 azimuth bins, 30 us jitter",
                    "mast anemometer gust front, 38 us jitter",
                    "UWB inter-agent ranging (context)",
                    "IMU attitude (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("inter_agent_floor_m", 2.0),
                        ("predicted_min_spacing_m", 2.11),
                        ("stall_margin_floor_deg", 1.2),
                        ("collective_drop_deg", 4.0),
                        ("climb_rate_m_s", 1.05),
                        ("formation_n", 5),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "U-RANS + vortex-particle BVI, seed 13; 4-blade rigid rotor, 24 azimuth bins, 3 radial stations; NOT actuator-disk",
                        ),
                        (
                            "fidelity_limits",
                            "No structural blade flex; BVI is a rigid-blade vortex encounter. Raster is kernelized events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Five-ship W-12 at 18 m AGL, 3 m below the ridge.",
                    "2. Proposed trim: 4 deg collective drop, climb 1.05 m/s, predicted spacing 2.11 m.",
                    "3. IMU precursor at 2.848 ms.",
                    "4. Race window [7.000, 7.450] ms.",
                    "5. Advancing-blade Kulite BVI at 7.120 ms (winner).",
                    "6. Mast gust at 7.334 ms (loser by 214 us).",
                    "7. Gate at 7.500 ms: ACCEPT; executed identical to proposed.",
                    "8. Min spacing 2.11 m; stall margin 1.3 deg.",
                    "9. Ridge passed as a five-ship.",
                    "10. Delayed (9 min): policy update requires blade-azimuth tags in pitot fusion.",
                ],
            ),
        ]
    )
    params = OrderedDict(
        [
            ("collective_drop_deg", 4.0),
            ("climb_rate_m_s", 1.05),
            ("formation_n", 5),
            ("airspeed_m_s", 5.8),
            ("agl_m", 18.0),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "ridge_trim_five_ship"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bvi_pulse", True),
                        ("predicted_min_spacing_m", 2.11),
                        ("inter_agent_floor_m", 2.0),
                        ("stall_margin_deg", 1.3),
                        ("stall_margin_floor_deg", 1.2),
                        ("race_margin_us", 214),
                        ("combined_jitter_us", 68),
                    ]
                ),
            ),
            (
                "basis",
                "Planner already includes a 4 deg collective drop and 1.05 m/s climb that keeps "
                "retreating-blade stall margin >= 1.2 deg and predicted min spacing 2.11 m >= 2.00 m. "
                "Unclamped 3.10 m/s is not the proposal.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Proposed trim already drops collective 4 deg and climbs 1.05 m/s; predicted min "
                "spacing 2.11 m >= 2.00 m floor; retreating-blade stall margin 1.3 deg >= 1.2 deg. "
                "BVI-first confirms the trim. ACCEPT executed identical to proposed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "inter_agent_spacing_m",
                            OrderedDict(
                                [
                                    ("floor", 2.0),
                                    ("predicted", 2.11),
                                ]
                            ),
                        ),
                        (
                            "stall_margin_deg",
                            OrderedDict(
                                [
                                    ("floor", 1.2),
                                    ("predicted", 1.3),
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
            ("name", "ridge_trim_five_ship"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed_action; 4 deg collective drop and 1.05 m/s climb held for the ridge pass.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Five-ship W-12 cleared the ridge with min spacing 2.11 m and stall margin 1.3 deg. "
                "BVI-first confirmed an already-legal trim; no further clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("formation", "five-ship intact; min spacing 2.11 m"),
                        ("rotor", "stall margin 1.3 deg"),
                        ("trim", "4 deg collective drop and 1.05 m/s climb held"),
                        ("ridge", "passed"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The BVI pulse was a rigid-blade vortex encounter in the U-RANS + vortex-particle solver, not a disk-average downwash sheet.",
                    "Delayed (9 min): policy update requiring blade-azimuth tags in pitot fusion so a later mast-gust cannot be fused without azimuth context.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "blade.kulite.bvi (7.120 ms)"),
                        ("loser", "mast.anem.gust (7.334 ms)"),
                        ("margin_us", 214),
                        (
                            "counterfactual_if_reversed",
                            "Gust-first by < 214 us inside the 450 us window would have delayed "
                            "confirmation of the same legal trim; it would not have required an extra "
                            "climb-rate clamp. Unclamped 3.10 m/s was never proposed.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7500),
            (
                "reward_inflection_note",
                "Safety and task_progress step up at the ACCEPT gate (7.500 ms, tick 4) as the already-legal trim locks in.",
            ),
        ]
    )
    spikes = [
        spike("imu.att.ctx", 1.880, 0.45),
        spike("blade.kulite.bvi", 3.210, 0.63),
        spike("mast.anem.gust", 4.640, 0.57),
        spike("uwb.spacing.ctx", 5.920, 0.49),
        spike("blade.kulite.bvi", 7.120, 1.36),
        spike("mast.anem.gust", 7.334, 1.17),
        spike("ctrl.gate", 7.500, 1.01),
        spike("blade.kulite.bvi", 9.880, 0.78),
        spike("uwb.spacing.ctx", 12.440, 0.52),
        spike("mast.anem.gust", 16.210, 0.64),
        spike("imu.att.ctx", 22.800, 0.47),
        spike("blade.kulite.bvi", 31.050, 0.59),
        spike("ctrl.gate", 40.220, 0.83),
    ]
    ras = raster_core(
        48,
        160,
        18,
        138,
        routing(
            "thalamic-relay.bvi-gust",
            "spikenaut.policy.trim-accept",
            [
                ("relay.blade.bvi", "policy.trim_accept", 0.59),
                ("relay.mast.gust", "policy.extra_clamp", 0.28),
                ("relay.uwb.spacing", "policy.trim_accept", 0.21),
            ],
            "serotonin",
            0.30,
            "pre_post_stdp; 5-HT at BVI win tags trim_accept, reward at ridge-clear",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.45),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("trim_accept", 80, 0.50, 220.0, 8),
                    pop("extra_clamp", 80, 0.50, 40.0, 1),
                    pop("stall_margin_veto", 40, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r13-084"),
            (
                "title",
                "Whimbrel-Stack W-12 five-ship: blade-resolved BVI beats mast gust by 214 us; ACCEPT already-legal 4 deg / 1.05 m/s trim",
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
                    "Clean ACCEPT of an already-legal blade-resolved trim. "
                    "total 1.02 = 0.40 + 0.28 + 0.16 + 0.10 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "aerial-swarm",
                    [
                        "accept",
                        "simulated",
                        "blade-resolved-bvi",
                        "five-ship",
                        "already-legal-trim",
                    ],
                    "Teaches a fusion head that a blade-resolved BVI pulse can confirm an already-legal trim without a further climb-rate clamp.",
                    4,
                ),
            ),
        ]
    )


def record_085():
    ticks = [
        tick(2018, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(5044, 0.09, 0.07, 0.04, 0.03, 0.02),
        tick(5188, 0.06, 0.05, 0.03, 0.02, 0.01),
        tick(5219, 0.14, 0.12, 0.06, 0.04, 0.02),
        tick(5529, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    excerpt = excerpt_items(
        [
            (650, 2),
            (1900, 18),
            (3300, 7),
            (4800, 31),
            (6400, 11),
            (8100, 24),
            (9900, 0),
            (11800, 35),
            (13700, 9),
            (15600, 21),
            (17600, 4),
            (19600, 28),
            (21500, 16),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Tugger T-11 rolls a 14 m packing lane at Cinder-Loft heading to packer stand P-4 "
                "when an RFID zone-exit pulse races a floor-magnet waypoint that claims 1.6 m of "
                "open path. Human-shared speed limit is 0.40 m/s; pedestrian floor is 0.70 m at the "
                "packer stand. Proposed 0.35 m/s creep with 0.50 m lateral. RFID-leading selects "
                "the creep; magnet-leading would keep 0.90 m/s transit through a false-clear waypoint.",
            ),
            ("domain", "warehouse-amr"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Reach packer stand P-4 on the 14 m packing lane, keep speed <= 0.40 m/s in "
                "human-shared mode, and keep packer range >= 0.70 m.",
            ),
            ("t0_us", 1756794625000085),
            ("gate_latency_us", 175),
            ("race_window_us", 310),
            ("race_window_rel_ms", [5.0, 5.31]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rfid.zone.exit packer-badge-clear",
                                "magnet.waypoint.free 1.6 m claim",
                            ],
                        ),
                        (
                            "semantics",
                            "RFID-first latches 0.35 m/s human-shared creep with 0.50 m lateral; "
                            "magnet-first latches 0.90 m/s cruise through a false-clear waypoint.",
                        ),
                        (
                            "window_derivation",
                            "310 us = one RFID reader slot versus the floor-magnet waypoint publisher "
                            "on this packing-lane cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 144 us vs combined jitter 54 us (RFID 24 + magnet 30): 2.7x over "
                            "a 2.0x trust floor. Reversing order by < 144 us would have kept 0.90 m/s "
                            "cruise past P-4.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "RFID zone-exit reader, 24 us jitter",
                    "floor-magnet waypoint, 30 us jitter",
                    "wheel encoder (context)",
                    "packer-stand photoelectric (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("human_shared_speed_cap_m_s", 0.4),
                        ("packer_range_floor_m", 0.7),
                        ("proposed_speed_m_s", 0.35),
                        ("lateral_offset_m", 0.5),
                        ("lane_length_m", 14.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Tugger T-11 indexed onto the Cinder-Loft packing lane; tote mass 22 kg.",
                    "2. Floor-magnet waypoint claims 1.6 m free; packer badge still in zone.",
                    "3. Wheel-enc precursor at 2.018 ms.",
                    "4. Race window [5.000, 5.310] ms.",
                    "5. RFID zone-exit at 5.044 ms (winner).",
                    "6. Magnet waypoint-free at 5.188 ms (loser by 144 us).",
                    "7. Gate at 5.219 ms: ACCEPT 0.35 m/s creep, 0.50 m lateral.",
                    "8. Min packer range 0.82 m; speed 0.35 m/s under 0.40 cap.",
                    "9. Lane cleared; tote at P-4.",
                    "10. Delayed (6 min): sister-lane T-12 RFID-authoritative policy under packer-present mode.",
                ],
            ),
        ]
    )
    params = OrderedDict(
        [
            ("speed_m_s", 0.35),
            ("lateral_offset_m", 0.5),
            ("horn", "soft-pulse 1 Hz"),
            ("mode", "human-shared-packing"),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "packing_lane_creep"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("rfid_zone_exit", True),
                        ("magnet_free_claim_m", 1.6),
                        ("human_shared_speed_cap_m_s", 0.4),
                        ("packer_range_floor_m", 0.7),
                        ("race_margin_us", 144),
                        ("combined_jitter_us", 54),
                    ]
                ),
            ),
            (
                "basis",
                "RFID zone-exit returned packer-badge-clear before the floor-magnet claimed 1.6 m "
                "free; 0.35 m/s creep stays under the 0.40 m/s cap and 0.50 m lateral keeps the "
                "0.70 m packer-stand floor.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "RFID zone-exit won by 144 us; commanded 0.35 m/s is 0.05 m/s under the 0.40 m/s "
                "human-shared cap; 0.50 m lateral keeps the 0.70 m packer-stand floor. ACCEPT the "
                "creep. A 0.90 m/s magnet-holdover would violate the floor if the 1.6 m waypoint "
                "were believed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "packer_range_m",
                            OrderedDict(
                                [
                                    ("floor", 0.7),
                                    ("lateral_offset", 0.5),
                                ]
                            ),
                        ),
                        (
                            "speed_m_s",
                            OrderedDict(
                                [
                                    ("cap", 0.4),
                                    ("commanded", 0.35),
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
            ("name", "packing_lane_creep"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed_action; 0.35 m/s creep and 0.50 m offset held for the 14 m packing lane.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "T-11 completed the packing-lane pass with min packer range 0.82 m; packer unharmed; "
                "tote on time. RFID-authoritative under packer-present mode confirmed.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("lane", "14 m packing lane cleared; packer P-4 resumed"),
                        ("tugger", "tote delivered stand P-4"),
                        ("policy", "RFID-authoritative under packer-present mode"),
                        ("near_miss_log", "none; min range 0.82 m"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 1.6 m magnet waypoint was not a calibration fault: a steel tote-leg can saturate the floor magnet while the packer badge is still in zone.",
                    "Delayed (6 min): sister tugger T-12 on lane 3 logged the same RFID-vs-magnet disagreement; hall policy flipped RFID-authoritative before the next packer rotation.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rfid.zone.exit (5.044 ms, packer-badge-clear)"),
                        ("loser", "magnet.waypoint.free (5.188 ms, 1.6 m claim)"),
                        ("margin_us", 144),
                        (
                            "counterfactual_if_reversed",
                            "Magnet-first by < 144 us inside the 310 us window would have kept "
                            "0.90 m/s cruise through a false-clear waypoint and closed on the packer "
                            "stand under the 0.70 m floor.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5219),
            (
                "reward_inflection_note",
                "Safety and efficiency both step up at the ACCEPT gate (5.219 ms, tick 4) as the creep locks in over cruise.",
            ),
        ]
    )
    spikes = [
        spike("wheel.enc.ctx", 1.088, 0.44),
        spike("rfid.zone.exit", 2.410, 0.60),
        spike("magnet.waypoint.free", 3.220, 0.53),
        spike("packer.stand.ctx", 4.018, 0.46),
        spike("rfid.zone.exit", 5.044, 1.27),
        spike("magnet.waypoint.free", 5.188, 1.09),
        spike("ctrl.gate", 5.219, 0.98),
        spike("rfid.zone.exit", 6.880, 0.80),
        spike("magnet.waypoint.free", 8.440, 0.64),
        spike("packer.stand.ctx", 11.020, 0.48),
        spike("ctrl.gate", 14.880, 0.86),
        spike("wheel.enc.ctx", 18.210, 0.40),
    ]
    ras = raster_core(
        22,
        40,
        55,
        48,
        routing(
            "thalamic-relay.packing-rfid",
            "spikenaut.policy.creep-go",
            [
                ("relay.rfid.exit", "policy.creep_go", 0.61),
                ("relay.magnet.free", "policy.cruise_hold", 0.30),
                ("relay.packer.stand", "policy.cruise_hold", -0.36),
            ],
            "dopamine",
            0.12,
            "pre_post_stdp; DA at RFID win tags creep_go, reward at lane-clear",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.31),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("creep_go", 32, 0.50, 260.0, 3),
                    pop("cruise_hold", 32, 0.50, 70.0, 1),
                    pop("packer_floor_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r13-085"),
            (
                "title",
                "Cinder-Loft packing hall / tugger T-11: RFID zone-exit beats floor-magnet waypoint by 144 us; ACCEPT 0.35 m/s creep",
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
                    "Clean ACCEPT. Tick columns sum to the five heads; total 1.18 = 0.44+0.34+0.20+0.12+0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "warehouse-amr",
                    [
                        "accept",
                        "packing-hall",
                        "rfid-vs-magnet",
                        "human-shared-packing",
                        "designed",
                    ],
                    "Teaches that a floor-magnet waypoint-free can lose to an RFID zone-exit when a packer badge is still in zone; reversing 144 us would have selected an illegal cruise.",
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
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r13-082":
        issues.append(f"wrong-gate set { [w['id'] for w in wrong] }")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
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
        if rec["id"] == "ttf-r13-081":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("081 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("081 inflection outside window")
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
        heads = ["task_progress", "safety", "efficiency", "coherence", "exploration"]
        total = sum(rec["reward_components"][h] for h in heads)
        if abs(total - rec["reward_components"]["total"]) > 1e-6:
            issues.append(f"{rec['id']} total mismatch {total}")
        for h in heads:
            s = sum(t[h] for t in rec["reward_components"]["ticks"])
            if abs(s - rec["reward_components"][h]) > 1e-6:
                issues.append(f"{rec['id']} {h} tick sum {s} vs {rec['reward_components'][h]}")
        if "training_ready" in json.dumps(rec):
            issues.append(f"{rec['id']} training_ready present")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
    return issues, jmax


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_081(), record_082(), record_083(), record_084(), record_085()]
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
