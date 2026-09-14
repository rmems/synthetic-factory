#!/usr/bin/env python3
"""Emit TTF r14 JSONL (ttf-r14-086..090) into /tmp/ttf-r14/. Never writes outputs/raw/."""

from __future__ import annotations

import json
import math
import random
import re
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

OUT_DIR = Path("/tmp/ttf-r14")
BATCH_PATH = OUT_DIR / "batch-r14.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r14.md"

PJ_PER_SPIKE = 23
RIGHTS = OrderedDict(
    [
        ("provider", "SpaceXAI/xAI"),
        ("model", "grok-4.6"),
        ("channel", "consumer"),
        ("subscription_plan", "SuperGrok Heavy"),
        ("generation_surface", "SuperGrok Heavy chat"),
        ("generated_at", "2026-09-02T21:40:00Z"),
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
FORBIDDEN_KEYS = {
    "thought",
    "thoughts",
    "chain_of_thought",
    "scratch",
    "reasoning",
    "inner_monologue",
    "hidden_reasoning",
    "thinking",
    "cot",
    "training_ready",
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


def lif_086_excerpt():
    """Independent CUBA LIF (seed 14086). Plant remains designed."""

    n = 72
    dt_us = 100
    tau_m_ms = 18.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.90
    i_stim_peak = 2.2
    stim = (17500, 20500)
    seed = 14086
    window_us = 38000
    i_clamp_extra = 0.65
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
    early = [(t, nid) for t, nid in spikes if t < 17500]
    burst = [(t, nid) for t, nid in spikes if 17500 <= t < 20500]
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
            era_early = pool[0][0] < 17500
            have = len([1 for t, _ in picked if (t < 17500) == era_early])
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
    take(burst, 9, label_times=(18400, 18800, 19600))
    clamp = [(t, n) for t, n in picked if t < 17500][:7]
    tear = [(t, n) for t, n in picked if t >= 17500][:9]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    if len(picked) < 12:
        raise ValueError(f"LIF excerpt too short: {len(picked)}")
    channels = ["lif.clamp" if t < 17500 else "lif.tear" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 72),
            ("dt_us", 100),
            ("tau_m_ms", 18.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.90),
            ("i_stim_peak", 2.2),
            ("stim_t_us", [17500, 20500]),
            ("i_clamp_extra", 0.65),
            ("clamp_n", 14),
            ("seed", 14086),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.65 clamp-pathway bias; stim 17.5-20.5 ms is the macular-hole burst.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("delayed_surprise_s", 720),
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
            ("round", 14),
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


def record_086():
    excerpt, extra, _lif_spikes = lif_086_excerpt()
    ticks = [
        tick(1120, 0.04, -0.02, -0.01, 0.01, 0.00),
        tick(5112, 0.07, -0.03, -0.02, 0.01, -0.01),
        tick(5370, 0.03, -0.02, -0.02, 0.00, 0.00),
        tick(5892, 0.09, -0.05, -0.03, 0.02, -0.01),
        tick(18400, 0.06, -0.40, -0.04, 0.00, -0.02),
        tick(720000000, 0.02, -0.04, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Suture-Isle OR-4 has Fen-13 parked in a 23-gauge pars-plana sleeve 1.8 mm off the "
                "foveal avascular zone with infusion already at 24.0 mmHg. The vitreoretinal "
                "stylus still shows a 3.6 Hz filtered tremor, but the live contest is tip IOP "
                "versus OCT axial wander, not force versus shake. An IOP win must cut infusion "
                "under 18.0 mmHg; an OCT win would leave the 24.0 mmHg cruise armed. Vitreous "
                "traction stored in the hyaloid is off both buses until the later OCT burst.",
            ),
            ("domain", "surgical-assist"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Reach the posterior hyaloid at 1.8 mm foveal standoff, keep infusion pressure "
                "<= 18.0 mmHg, and leave the inner retina unmarked.",
            ),
            ("t0_us", 1756838400000086),
            ("gate_latency_us", 780),
            ("race_window_us", 420),
            ("race_window_rel_ms", [5.0, 5.42]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "iop.tip.mmHg 24.0 pulse",
                                "oct.axial.jitter 38 um residual",
                            ],
                        ),
                        (
                            "semantics",
                            "IOP-first latches infusion clamp 24.0 -> 14.0 mmHg and 1.2 -> 0.4 ml/min; "
                            "OCT-first keeps cruise infusion on a 'still approaching' model.",
                        ),
                        (
                            "window_derivation",
                            "420 us = one IOP sample period minus OCT axial demodulation group delay "
                            "on this 2 kHz wrist bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 258 us vs combined jitter 66 us (IOP 28 + OCT 38): 3.9x over a 2.0x "
                            "trust floor. Reversing order by < 258 us inside the 420 us window would have "
                            "kept 24.0 mmHg cruise; predicted next-sample 19.6 mmHg > 18.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "tip IOP, 2 kHz, 28 us timestamp jitter",
                    "OCT axial jitter band 20-60 um, 38 us jitter",
                    "optical standoff to ILM, 200 Hz (context)",
                    "joint encoders (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("infusion_cap_mmHg", 18.0),
                        ("proposed_infusion_mmHg", 24.0),
                        ("infusion_rate_proposed_ml_min", 1.2),
                        ("standoff_mm", 1.8),
                        ("gauge", 23),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Fen-13 indexed through the 23-gauge port; standoff 1.8 mm to the hyaloid.",
                    "2. Cruise infusion 24.0 mmHg at 1.2 ml/min armed; OCT residual 38 um.",
                    "3. Encoder precursor at 1.120 ms; IOP warm-start 24.0 mmHg.",
                    "4. Race window [5.000, 5.420] ms opens on the wrist bus.",
                    "5. IOP tip 24.0 mmHg at 5.112 ms (winner).",
                    "6. OCT axial jitter at 5.370 ms (loser by 258 us).",
                    "7. Gate at 5.892 ms (winner + 780 us): MODIFY clamp 14.0 mmHg, 0.4 ml/min.",
                    "8. Clamp executes; next-sample IOP 16.4 mmHg < 18.0 cap.",
                    "9. At 18.400 ms vitreous traction opens a 0.3 mm macular hole; OCT burst.",
                    "10. Fluid-air exchange 12 min + ILM peel; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_hyaloid_infusion"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("infusion_mmHg", 24.0),
                        ("infusion_ml_min", 1.2),
                        ("standoff_mm", 1.8),
                        ("tremor_filter_hz", 3.6),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("iop_tip_mmHg", 24.0),
                        ("infusion_cap_mmHg", 18.0),
                        ("predicted_unclamped_next_mmHg", 19.6),
                        ("oct_jitter_um", 38.0),
                        ("race_margin_us", 258),
                        ("combined_jitter_us", 66),
                        ("standoff_mm", 1.8),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 24.0 mmHg cruise at 1.2 ml/min: OCT residual 38 um looks like "
                "approach shake, not contact, and the 1.8 mm standoff is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "IOP tip 24.0 mmHg won by 258 us, so the cannula is loading vitreous, not still "
                "approaching. Holding 24.0 mmHg predicts next-sample 19.6 mmHg > 18.0 mmHg cap. "
                "MODIFY: infusion 24.0 -> 14.0 mmHg and 1.2 -> 0.4 ml/min. Observed after clamp "
                "16.4 mmHg < 18.0. A full REJECT is not indicated: a sound hyaloid accepts 14.0 mmHg.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "infusion_mmHg",
                            OrderedDict(
                                [
                                    ("cap", 18.0),
                                    ("observed", 24.0),
                                    ("predicted_unclamped_next", 19.6),
                                    ("clamped", 14.0),
                                    ("observed_after_clamp", 16.4),
                                ]
                            ),
                        ),
                        (
                            "infusion_ml_min",
                            OrderedDict([("proposed", 1.2), ("clamped", 0.4)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 258),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 3.91),
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
            ("name", "clamped_hyaloid_infusion"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("infusion_mmHg", 14.0),
                        ("infusion_ml_min", 0.4),
                        ("standoff_mm", 1.8),
                        ("tremor_filter_hz", 3.6),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: infusion 24.0 -> 14.0 mmHg and 1.2 -> 0.4 ml/min. Process-correct vs the "
                "18.0 mmHg cap. Macular hole still occurs at 18.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held infusion at 16.4 mmHg. At 18.400 ms stored vitreous "
                "traction produced a 0.3 mm macular hole. Clamp reduced dump energy; it did not "
                "prevent the shear. Partnered negative: process heads stay honest; world loss is "
                "named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("instrument", "clamp executed; peak 16.4 mmHg < 18.0"),
                        ("retina", "0.3 mm macular hole at 18.400 ms"),
                        ("repair", "12 min fluid-air exchange + ILM peel"),
                        ("mission", "hyaloid still reached; hole controlled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither IOP nor OCT predicted the traction dump; tissue.oct.tear is a new channel at 18.400 ms, 12.508 ms after the gate, still inside the 38 ms raster.",
                    "Delayed (12 min / delayed_surprise_s=720): fluid-air exchange and ILM peel close the hole. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "12 min fluid-air exchange + ILM peel after a 0.3 mm macular hole. Safety head "
                "-0.56 prices the hole; task_progress stays +0.31 because the pressure clamp "
                "completed under the 18.0 mmHg cap. World loss is named here, not subtracted "
                "from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "iop.tip.mmHg (5.112 ms, 24.0 mmHg)"),
                        ("loser", "oct.axial.jitter (5.370 ms, 38 um residual)"),
                        ("margin_us", 258),
                        (
                            "counterfactual_if_reversed",
                            "OCT-first by < 258 us inside the 420 us window would have kept "
                            "24.0 mmHg cruise; predicted next-sample 19.6 mmHg would have exceeded "
                            "the 18.0 mmHg cap even without the traction dump. The MODIFY is still "
                            "the correct process. The hole is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 18400),
            (
                "reward_inflection_note",
                "Safety collapses at the 18.400 ms macular hole (tick t_us=18400), inside the "
                "38 ms raster. The correct MODIFY at 5.892 ms is in the same excerpt. Do not put "
                "inflection on the +12 min fluid-air tick.",
            ),
            ("delayed_surprise_s", 720),
        ]
    )
    spikes = [
        spike("encoder.pos.ctx", 0.880, 0.42),
        spike("iop.tip.mmHg", 2.210, 0.63),
        spike("oct.axial.jitter", 3.640, 0.51),
        spike("optical.standoff.ctx", 4.180, 0.46),
        spike("iop.tip.mmHg", 5.112, 1.33),
        spike("oct.axial.jitter", 5.370, 1.16),
        spike("ctrl.gate", 5.892, 0.98),
        spike("iop.tip.mmHg", 7.440, 0.82),
        spike("oct.axial.jitter", 9.880, 0.64),
        spike("ctrl.gate", 13.200, 0.86),
        spike("tissue.oct.tear", 18.400, 1.44),
        spike("tissue.oct.tear", 20.050, 0.92),
        spike("encoder.pos.ctx", 26.800, 0.40),
        spike("iop.tip.mmHg", 34.100, 0.55),
    ]
    ras = raster_core(
        38,
        72,
        28,
        77,
        routing(
            "thalamic-relay.iop-oct",
            "spikenaut.policy.infusion-clamp",
            [
                ("relay.iop.tip", "policy.infusion_clamp", 0.66),
                ("relay.oct.jitter", "policy.oct_hold", 0.31),
                ("relay.tissue.tear", "policy.infusion_clamp", -0.46),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at IOP win (5.112 ms) opens a 40 ms eligibility "
            "trace that still covers the 18.400 ms hole",
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
                    pop("iop_clamp", 40, 0.50, 280.0, 5),
                    pop("oct_hold", 40, 0.50, 80.0, 1),
                    pop("iop_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r14-086"),
            (
                "title",
                "Suture-Isle Theatre OR-4 / Fen-13: IOP tip beats OCT jitter by 258 us; correct "
                "MODIFY still eats an in-window macular hole (partnered negative total -0.39)",
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
                    "38 ms raster. total -0.39 = 0.31 + -0.56 + -0.14 + 0.04 + -0.04. Named "
                    "fluid-air+ILM loss is not netted into task_progress. Tick 6 t_us binds "
                    "raster.delayed_surprise_s=720.",
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


def record_087():
    ticks = [
        tick(1880, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(6980, 0.08, 0.06, 0.03, 0.02, 0.01),
        tick(7128, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(7520, 0.12, 0.10, 0.05, 0.03, 0.02),
        tick(9100, 0.06, 0.05, 0.03, 0.02, 0.01),
        tick(180000000, 0.03, 0.03, 0.02, 0.01, 0.01),
    ]
    excerpt = excerpt_items(
        [
            (620, 5),
            (2100, 22),
            (3900, 41),
            (5600, 9),
            (7400, 33),
            (9100, 14),
            (10900, 50),
            (12800, 2),
            (14700, 27),
            (16700, 58),
            (18800, 11),
            (20900, 36),
            (23100, 7),
            (25200, 44),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Gantry-R4 has laid 90 mm of a 12 mm adhesive fillet along the Kiln-Spur Cell K "
                "battery-tray seam when the nozzle transducer reports 28.4 N against a 22.0 N "
                "bead-force cap. Bead surface is 41.2 C, still under the 55 C gel point, so a "
                "thermal-first read would keep cruise press. Force-first binds a nozzle hold "
                "before the fillet stars.",
            ),
            ("domain", "industrial-assembly"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the 12 mm fillet on the aluminum tray seam, keep nozzle force <= 22.0 N, "
                "and leave the gel front under 55 C.",
            ),
            ("t0_us", 1756838401000087),
            ("gate_latency_us", 540),
            ("race_window_us", 310),
            ("race_window_rel_ms", [6.9, 7.21]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.nozzle.n 28.4 N contact",
                                "therm.bead.C 41.2 C under gel",
                            ],
                        ),
                        (
                            "semantics",
                            "FT-first latches nozzle clamp 28.4 -> 16.0 N and 18 -> 9 mm/s; "
                            "therm-first keeps cruise press because 41.2 C is still under 55 C gel.",
                        ),
                        (
                            "window_derivation",
                            "310 us = one nozzle-FT EtherCAT slot versus the bead IR publisher "
                            "on this 4 kHz cell bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 148 us vs combined jitter 58 us (FT 26 + IR 32): 2.6x over a 2.0x "
                            "trust floor. Reversing order by < 148 us inside the 310 us window would "
                            "have kept 28.4 N cruise; predicted next-sample 24.1 N > 22.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "nozzle 6-axis FT, 4 kHz, 26 us jitter",
                    "bead IR pyrometer, 2 kHz, 32 us jitter",
                    "gantry linear encoder (context)",
                    "adhesive pump pressure (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bead_force_cap_N", 22.0),
                        ("observed_nozzle_N", 28.4),
                        ("gel_point_C", 55.0),
                        ("bead_surface_C", 41.2),
                        ("fillet_mm", 12.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Gantry-R4 90 mm into the 12 mm fillet on Cell K tray seam.",
                    "2. Cruise press 28.4 N at 18 mm/s armed; bead 41.2 C under 55 C gel.",
                    "3. Encoder precursor at 1.880 ms.",
                    "4. Race window [6.900, 7.210] ms.",
                    "5. Nozzle FT 28.4 N at 6.980 ms (winner).",
                    "6. Bead IR 41.2 C at 7.128 ms (loser by 148 us).",
                    "7. Gate at 7.520 ms: MODIFY clamp 16.0 N, 9 mm/s.",
                    "8. After clamp 17.8 N < 22.0; gel front still 41.6 C.",
                    "9. Fillet completes without star; seam leak-check passes.",
                    "10. Delayed (3 min / delayed_surprise_s=180): QC tags the force-first bind on the next tray.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_fillet_press"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("nozzle_N", 28.4),
                        ("bead_mm_s", 18.0),
                        ("fillet_mm", 12.0),
                        ("gel_point_C", 55.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("nozzle_N", 28.4),
                        ("bead_force_cap_N", 22.0),
                        ("predicted_unclamped_next_N", 24.1),
                        ("bead_surface_C", 41.2),
                        ("gel_point_C", 55.0),
                        ("race_margin_us", 148),
                        ("combined_jitter_us", 58),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 28.4 N cruise at 18 mm/s: bead 41.2 C is under 55 C gel, so the "
                "force spike is treated as a still-wet contact, not a star.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Nozzle FT 28.4 N won by 148 us, so the fillet is over the 22.0 N bead-force cap, "
                "not still a thermal-limited wet contact. Holding 28.4 N predicts next-sample "
                "24.1 N > 22.0. MODIFY: nozzle 28.4 -> 16.0 N and 18 -> 9 mm/s. Observed after "
                "clamp 17.8 N < 22.0. A full REJECT is not indicated: a 12 mm fillet accepts 16.0 N.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "nozzle_N",
                            OrderedDict(
                                [
                                    ("cap", 22.0),
                                    ("observed", 28.4),
                                    ("predicted_unclamped_next", 24.1),
                                    ("clamped", 16.0),
                                    ("observed_after_clamp", 17.8),
                                ]
                            ),
                        ),
                        (
                            "bead_mm_s",
                            OrderedDict([("proposed", 18.0), ("clamped", 9.0)]),
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
            ("name", "clamped_fillet_press"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("nozzle_N", 16.0),
                        ("bead_mm_s", 9.0),
                        ("fillet_mm", 12.0),
                        ("gel_point_C", 55.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: nozzle 28.4 -> 16.0 N and 18 -> 9 mm/s. Process-correct vs the 22.0 N cap. "
                "Gel front stayed under 55 C.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct MODIFY held nozzle force at 17.8 N under the 22.0 N cap. Fillet completed "
                "without a star. Bead IR remaining under gel was the losing channel and did not "
                "justify cruise press.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("nozzle", "clamp executed; peak 17.8 N < 22.0"),
                        ("fillet", "12 mm bead complete, no star"),
                        ("gel", "surface 41.6 C < 55 C"),
                        ("tray", "leak-check pass"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "IR remaining under gel did not predict the force overshoot; reversing 148 us would have left 24.1 N on the seam.",
                    "Delayed (3 min / delayed_surprise_s=180): QC tags force-first bind as the standing Cell K rule for the next tray.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.nozzle.n (6.980 ms, 28.4 N)"),
                        ("loser", "therm.bead.C (7.128 ms, 41.2 C)"),
                        ("margin_us", 148),
                        (
                            "counterfactual_if_reversed",
                            "Therm-first by < 148 us inside the 310 us window would have kept "
                            "28.4 N cruise; predicted next-sample 24.1 N would have exceeded the "
                            "22.0 N cap and starred the fillet.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7520),
            (
                "reward_inflection_note",
                "Heads rise at the correct clamp (7.520 ms, tick 4). The 3 min QC tag is delayed "
                "surprise bound to raster.delayed_surprise_s=180, not the inflection.",
            ),
            ("delayed_surprise_s", 180),
        ]
    )
    spikes = [
        spike("enc.j3.pos.ctx", 0.940, 0.41),
        spike("ft.nozzle.n", 2.660, 0.60),
        spike("therm.bead.C", 4.020, 0.52),
        spike("pump.psi.ctx", 5.410, 0.44),
        spike("ft.nozzle.n", 6.980, 1.29),
        spike("therm.bead.C", 7.128, 1.11),
        spike("ctrl.gate", 7.520, 0.96),
        spike("ft.nozzle.n", 9.100, 0.80),
        spike("therm.bead.C", 11.440, 0.63),
        spike("ctrl.gate", 14.880, 0.85),
        spike("ft.nozzle.n", 18.200, 0.57),
        spike("enc.j3.pos.ctx", 22.050, 0.39),
        spike("therm.bead.C", 24.800, 0.48),
    ]
    ras = raster_core(
        26,
        64,
        40,
        67,
        routing(
            "thalamic-relay.nozzle-ir",
            "spikenaut.policy.nozzle-clamp",
            [
                ("relay.ft.nozzle", "policy.nozzle_clamp", 0.69),
                ("relay.therm.bead", "policy.therm_hold", 0.28),
            ],
            "acetylcholine",
            0.06,
            "force_cap_stdp; ACh tags the nozzle_clamp bind at the FT win",
        ),
        excerpt,
        extra=OrderedDict([("delayed_surprise_s", 180)]),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.31),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("nozzle_clamp", 36, 0.50, 320.0, 4),
                    pop("therm_hold", 36, 0.50, 90.0, 1),
                    pop("force_cap_veto", 18, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r14-087"),
            (
                "title",
                "Kiln-Spur Cell K / Gantry-R4: nozzle FT beats bead IR by 148 us; correct MODIFY "
                "clamps 28.4 -> 16.0 N under the 22.0 N fillet cap",
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
                    "Clean correct MODIFY on nozzle force. total 1.04 = 0.38 + 0.32 + 0.17 + 0.10 + 0.07. "
                    "Tick 6 t_us binds raster.delayed_surprise_s=180.",
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
                        "adhesive-fillet",
                        "force-vs-thermal",
                        "tick6-sidecar-bound",
                        "designed",
                    ],
                    "Teaches that an under-gel IR read losing a 148 us race does not license cruise "
                    "press when nozzle force already exceeds the fillet cap.",
                    2,
                ),
            ),
        ]
    )


def record_088():
    ticks = [
        tick(1440, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(4780, 0.02, 0.08, 0.03, 0.02, 0.01),
        tick(5104, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5900, 0.03, 0.14, 0.04, 0.04, 0.02),
        tick(6400, 0.02, 0.05, 0.02, 0.01, 0.01),
        tick(240000000, 0.01, 0.04, 0.01, 0.01, 0.00),
    ]
    excerpt = excerpt_items(
        [
            (800, 8),
            (3200, 41),
            (5900, 77),
            (8400, 3),
            (11200, 55),
            (14100, 19),
            (17200, 88),
            (20500, 12),
            (23900, 63),
            (27400, 30),
            (31000, 91),
            (34700, 6),
            (38400, 48),
            (42100, 14),
            (43800, 70),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Interlocking I-7 at Oxbow-Switch OS-19 is armed to throw the 1:9 turnout to reverse "
                "while a shunt occupancy still sits on the fouling point of the HIL track-circuit "
                "rack. Occupancy-first must hold normal. Axle-counter-first would treat a 2/2 "
                "clear-count as a legal throw and foul the dummy consist.",
            ),
            ("domain", "rail-signaling"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Throw the 1:9 turnout only when fouling occupancy is 0, keep point force under "
                "the 4.5 kN machine cap, and leave the dummy consist clear of the fouling bar.",
            ),
            ("t0_us", 1756838402000088),
            ("gate_latency_us", 1120),
            ("race_window_us", 640),
            ("race_window_rel_ms", [4.6, 5.24]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "track.circuit.occ shunt drop 0.18 ohm",
                                "axle.counter.pulse clear-count 2/2",
                            ],
                        ),
                        (
                            "semantics",
                            "Occupancy-first latches REJECT hold-normal; axle-counter-first would "
                            "commit throw-reverse on a false clear.",
                        ),
                        (
                            "window_derivation",
                            "640 us = one 50 Hz track-circuit demodulation slot versus the axle-counter "
                            "pulse stretcher on this HIL interlocking bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 324 us vs combined jitter 92 us (TC 44 + axle 48): 3.5x over a 2.0x "
                            "trust floor. Reversing order by < 324 us inside the 640 us window would "
                            "have thrown reverse onto an occupied fouling point.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "audio-frequency track circuit, 50 Hz demod, 44 us jitter",
                    "axle-counter head pair, 48 us jitter",
                    "point-machine current (context)",
                    "HIL dummy-consist RFID (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("fouling_occupancy_cap", 0),
                        ("observed_occupancy", 1),
                        ("shunt_ohm", 0.18),
                        ("axle_clear_count", "2/2"),
                        ("point_force_cap_kN", 4.5),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        (
                            "rig",
                            "Oxbow-Switch OS-19 interlocking HIL rack; dummy shunt on the fouling "
                            "section, not a live running line.",
                        ),
                        (
                            "fidelity_limits",
                            "Track-circuit demod and axle-counter stretcher are hardware-in-the-loop; "
                            "ballast resistance is a lumped 0.18 ohm shunt, not distributed rail.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. I-7 armed to throw 1:9 turnout reverse; dummy consist still on fouling bar.",
                    "2. Proposed throw-reverse in 1.8 s; axle-counter already 2/2 clear.",
                    "3. Relay precursor at 1.440 ms.",
                    "4. Race window [4.600, 5.240] ms.",
                    "5. Track-circuit occupancy 0.18 ohm at 4.780 ms (winner).",
                    "6. Axle-counter 2/2 at 5.104 ms (loser by 324 us).",
                    "7. Gate at 5.900 ms: REJECT hold-normal; do not throw.",
                    "8. Point machine stays normal; occupancy remains 1.",
                    "9. Dummy consist reclears after the hold.",
                    "10. Delayed (4 min / delayed_surprise_s=240): interlocking logs the false-clear as a reclear wait.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "throw_reverse"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("throw", True),
                        ("position", "reverse"),
                        ("throw_s", 1.8),
                        ("fouling_check", "axle_clear_2_of_2"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("fouling_occupancy", 1),
                        ("fouling_occupancy_cap", 0),
                        ("shunt_ohm", 0.18),
                        ("axle_clear_count", "2/2"),
                        ("race_margin_us", 324),
                        ("combined_jitter_us", 92),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes throw-reverse because the axle-counter already reports 2/2 "
                "clear and the 1.8 s throw is inside the machine force cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Track-circuit occupancy 0.18 ohm won by 324 us, so the fouling point is still "
                "occupied (observed occupancy 1 > cap 0). Axle-counter 2/2 is a false clear on "
                "this HIL shunt. REJECT: hold-normal, do not throw. A MODIFY that slowed the "
                "throw would still foul the dummy consist.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "fouling_occupancy",
                            OrderedDict(
                                [
                                    ("cap", 0),
                                    ("observed", 1),
                                    ("shunt_ohm", 0.18),
                                    ("axle_clear_count", "2/2"),
                                ]
                            ),
                        ),
                        (
                            "throw",
                            OrderedDict(
                                [
                                    ("proposed", True),
                                    ("executed", False),
                                    ("position_held", "normal"),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 324),
                                    ("combined_jitter_us", 92),
                                    ("ratio", 3.52),
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
            ("name", "hold_normal"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("throw", False),
                        ("position", "normal"),
                        ("throw_s", 0.0),
                        ("fouling_check", "track_circuit_occ"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold-normal. Point machine not commanded. Dummy consist remains on the "
                "fouling bar until reclear.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held the turnout normal. Occupancy 1 stayed on the fouling point. "
                "Axle-counter 2/2 was a false clear against the 0.18 ohm HIL shunt. Task incomplete; "
                "cap held.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("turnout", "held normal; throw not issued"),
                        ("fouling", "occupancy 1 remains"),
                        ("dummy", "consist still on fouling bar"),
                        ("interlocking", "reclear wait armed"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Axle-counter 2/2 did not match the 0.18 ohm shunt; reversing 324 us would have thrown reverse onto occupied fouling.",
                    "Delayed (4 min / delayed_surprise_s=240): reclear wait logged; dummy pulled clear of the fouling bar.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "track.circuit.occ (4.780 ms, 0.18 ohm)"),
                        ("loser", "axle.counter.pulse (5.104 ms, 2/2 clear)"),
                        ("margin_us", 324),
                        (
                            "counterfactual_if_reversed",
                            "Axle-counter-first by < 324 us inside the 640 us window would have "
                            "committed throw-reverse onto an occupied fouling point. The correct "
                            "gate is REJECT hold-normal either way while occupancy is 1.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5900),
            (
                "reward_inflection_note",
                "Safety peaks at the REJECT hold (5.900 ms, tick 4). The 4 min reclear is delayed "
                "surprise bound to raster.delayed_surprise_s=240, not the inflection.",
            ),
            ("delayed_surprise_s", 240),
            ("hazard_avoided", "throw-reverse onto occupied fouling point"),
        ]
    )
    spikes = [
        spike("relay.point.ctx", 0.720, 0.40),
        spike("track.circuit.occ", 2.180, 0.61),
        spike("axle.counter.pulse", 3.440, 0.54),
        spike("point.i.ctx", 4.020, 0.43),
        spike("track.circuit.occ", 4.780, 1.36),
        spike("axle.counter.pulse", 5.104, 1.14),
        spike("ctrl.gate", 5.900, 1.01),
        spike("track.circuit.occ", 7.220, 0.83),
        spike("axle.counter.pulse", 9.880, 0.62),
        spike("ctrl.gate", 14.400, 0.87),
        spike("track.circuit.occ", 22.100, 0.58),
        spike("relay.point.ctx", 31.050, 0.38),
        spike("axle.counter.pulse", 39.200, 0.47),
    ]
    ras = raster_core(
        44,
        96,
        20,
        84,
        routing(
            "thalamic-relay.occ-axle",
            "spikenaut.policy.hold-normal",
            [
                ("relay.track.occ", "policy.hold_reject", 0.74),
                ("relay.axle.clear", "policy.throw_go", 0.22),
            ],
            "serotonin",
            0.10,
            "occupancy_veto_stdp; 5-HT tags the hold_reject bind at the TC win",
        ),
        excerpt,
        extra=OrderedDict([("delayed_surprise_s", 240)]),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.64),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 48, 0.50, 220.0, 7),
                    pop("throw_go", 48, 0.80, 40.0, 1),
                    pop("fouling_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r14-088"),
            (
                "title",
                "Oxbow-Switch OS-19 HIL / interlocking I-7: track-circuit occupancy beats "
                "axle-counter 2/2 by 324 us; REJECT hold-normal, do not throw",
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
                    "total 0.82 = 0.10 + 0.42 + 0.14 + 0.10 + 0.06. Tick 6 t_us binds "
                    "raster.delayed_surprise_s=240.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "rail-signaling",
                    [
                        "reject",
                        "hil",
                        "fouling-occupancy",
                        "axle-false-clear",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that an axle-counter 2/2 clear is not fouling clearance when the "
                    "track-circuit shunt still reads occupied.",
                    3,
                ),
            ),
        ]
    )


def record_089():
    ticks = [
        tick(2210, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(8020, 0.08, 0.05, 0.03, 0.02, 0.02),
        tick(8310, 0.05, 0.04, 0.02, 0.02, 0.01),
        tick(9620, 0.14, 0.10, 0.06, 0.04, 0.02),
        tick(11200, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(45000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    excerpt = excerpt_items(
        [
            (700, 9),
            (2800, 44),
            (5100, 81),
            (7400, 2),
            (9900, 60),
            (12500, 17),
            (15200, 95),
            (18000, 33),
            (20900, 72),
            (23900, 6),
            (27000, 51),
            (30100, 108),
            (31800, 21),
        ]
    )
    params = OrderedDict(
        [
            ("jacket_step_K", -4.0),
            ("agitator_rpm", 180),
            ("raman_band_cm_1", 1610),
            ("runaway_trip_C", 92.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "CSTR-B in Pitch-Kettle PK-3 is at 78.4 C with the 1610 cm-1 Raman peak already "
                "rolling over when the jacket still reports a +0.08 K/s climb. The proposed -4 K "
                "coolant step already sits under the 84 C step-enable and the 92 C runaway trip. "
                "Raman-first confirms that step; jacket-first would hunt an extra clamp the "
                "exotherm does not need.",
            ),
            ("domain", "process-chem"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Step the jacket -4 K while batch T stays under 84 C step-enable and 92 C runaway "
                "trip, and keep agitator at 180 rpm.",
            ),
            ("t0_us", 1756838403000089),
            ("gate_latency_us", 1600),
            ("race_window_us", 880),
            ("race_window_rel_ms", [7.8, 8.68]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "raman.1610 peak falling",
                                "jacket.dTdt +0.08 K/s climb",
                            ],
                        ),
                        (
                            "semantics",
                            "Raman-first confirms the already-legal -4 K jacket step; jacket-first "
                            "would treat the lagging dT/dt as an open exotherm and hunt a further clamp.",
                        ),
                        (
                            "window_derivation",
                            "880 us = one 8 ms Raman CCD frame-slice versus the jacket RTD group delay "
                            "on this reduced-order CSTR bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 290 us vs combined jitter 84 us (Raman 40 + RTD 44): 3.5x over a 2.0x "
                            "trust floor. Reversing order by < 290 us would not make the proposed step "
                            "illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "inline Raman 1610 cm-1, 8 ms frame, 40 us jitter",
                    "jacket RTD dT/dt, 44 us jitter",
                    "agitator tachometer (context)",
                    "batch T probe (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("step_enable_C", 84.0),
                        ("runaway_trip_C", 92.0),
                        ("batch_T_C", 78.4),
                        ("jacket_dTdt_K_s", 0.08),
                        ("raman_dI_dt_sign", "falling"),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "reduced-order CSTR energy balance + Raman intensity ODE, seed 14089; "
                            "NOT CFD, NOT full kinetics",
                        ),
                        (
                            "fidelity_limits",
                            "Jacket lag is a first-order RTD; mixing is a single tau. Raster is "
                            "kernelized events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. CSTR-B at 78.4 C; 1610 cm-1 Raman already rolling over.",
                    "2. Proposed jacket step -4 K at 180 rpm; T under 84 C step-enable.",
                    "3. Agitator precursor at 2.210 ms.",
                    "4. Race window [7.800, 8.680] ms.",
                    "5. Raman 1610 falling at 8.020 ms (winner).",
                    "6. Jacket dT/dt +0.08 K/s at 8.310 ms (loser by 290 us).",
                    "7. Gate at 9.620 ms: ACCEPT; executed identical to proposed.",
                    "8. Batch T peaks 80.1 C << 92 C trip; step completes.",
                    "9. Raman continues falling; no extra clamp.",
                    "10. Delayed (45 s / delayed_surprise_s=45): GC sample confirms conversion on the falling 1610 band.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "jacket_step_minus_4k"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("batch_T_C", 78.4),
                        ("step_enable_C", 84.0),
                        ("runaway_trip_C", 92.0),
                        ("jacket_dTdt_K_s", 0.08),
                        ("raman_dI_dt_sign", "falling"),
                        ("race_margin_us", 290),
                        ("combined_jitter_us", 84),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes -4 K jacket step: Raman 1610 already falling and batch T 78.4 C "
                "is under the 84 C step-enable, so the lagging jacket climb is treated as sensor lag.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Raman 1610 falling won by 290 us, so the exotherm is already rolling over. Batch T "
                "78.4 C is under the 84 C step-enable and 92 C runaway trip. The proposed -4 K "
                "jacket step is already legal. ACCEPT: execute as proposed. A MODIFY extra clamp "
                "is not indicated; jacket +0.08 K/s is lag, not an open runaway.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "batch_T_C",
                            OrderedDict(
                                [
                                    ("step_enable", 84.0),
                                    ("runaway_trip", 92.0),
                                    ("observed", 78.4),
                                    ("peak_after_step", 80.1),
                                ]
                            ),
                        ),
                        (
                            "jacket_step_K",
                            OrderedDict([("proposed", -4.0), ("executed", -4.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 290),
                                    ("combined_jitter_us", 84),
                                    ("ratio", 3.45),
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
            ("name", "jacket_step_minus_4k"),
            ("parameters", OrderedDict(params)),
            (
                "gate_effect",
                "ACCEPT: executed parameters identical to proposed. Peak T 80.1 C under 92 C trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal -4 K jacket step. Raman-first confirmed the "
                "rollover; jacket dT/dt lag did not justify an extra clamp. Peak T 80.1 C.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("jacket", "step -4 K executed as proposed"),
                        ("batch_T_C", "peak 80.1 < 92 trip"),
                        ("raman", "1610 band continues falling"),
                        ("agitator", "180 rpm held"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Jacket +0.08 K/s lagged the Raman rollover by 290 us; reversing that margin would only have delayed confirmation, not made the step illegal.",
                    "Delayed (45 s / delayed_surprise_s=45): GC sample confirms conversion on the falling 1610 band.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "raman.1610 (8.020 ms, falling)"),
                        ("loser", "jacket.dTdt (8.310 ms, +0.08 K/s)"),
                        ("margin_us", 290),
                        (
                            "counterfactual_if_reversed",
                            "Jacket-first by < 290 us inside the 880 us window would have hunted "
                            "an extra clamp the proposed step does not need. The -4 K step remains "
                            "legal either way at 78.4 C.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 9620),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (9.620 ms, tick 4). The 45 s GC sample is delayed "
                "surprise bound to raster.delayed_surprise_s=45, not the inflection.",
            ),
            ("delayed_surprise_s", 45),
        ]
    )
    spikes = [
        spike("agitator.rpm.ctx", 1.105, 0.43),
        spike("raman.1610", 3.220, 0.59),
        spike("jacket.dTdt", 5.010, 0.50),
        spike("batch.T.ctx", 6.440, 0.45),
        spike("raman.1610", 8.020, 1.27),
        spike("jacket.dTdt", 8.310, 1.09),
        spike("ctrl.gate", 9.620, 0.97),
        spike("raman.1610", 11.200, 0.78),
        spike("jacket.dTdt", 14.880, 0.61),
        spike("ctrl.gate", 18.400, 0.84),
        spike("raman.1610", 24.050, 0.56),
        spike("agitator.rpm.ctx", 29.100, 0.40),
    ]
    ras = raster_core(
        32,
        112,
        24,
        86,
        routing(
            "thalamic-relay.raman-jacket",
            "spikenaut.policy.jacket-step",
            [
                ("relay.raman.1610", "policy.step_accept", 0.67),
                ("relay.jacket.dTdt", "policy.extra_clamp", 0.24),
            ],
            "dopamine",
            0.12,
            "rollover_confirm_stdp; DA tags the step_accept bind at the Raman win",
        ),
        excerpt,
        extra=OrderedDict([("delayed_surprise_s", 45)]),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.88),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("step_accept", 56, 0.50, 180.0, 9),
                    pop("extra_clamp", 56, 0.80, 20.0, 1),
                    pop("runaway_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r14-089"),
            (
                "title",
                "Pitch-Kettle PK-3 / CSTR-B: Raman 1610 rollover beats jacket dT/dt by 290 us; "
                "ACCEPT already-legal -4 K coolant step",
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
                    "Clean ACCEPT of an already-legal jacket step. "
                    "total 1.13 = 0.44 + 0.30 + 0.19 + 0.12 + 0.08. Tick 6 t_us binds "
                    "raster.delayed_surprise_s=45.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "process-chem",
                    [
                        "accept",
                        "simulated",
                        "raman-vs-jacket",
                        "cstr-rollover",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging jacket climb losing a 290 us race does not require an "
                    "extra clamp when Raman already shows rollover under the trip.",
                    4,
                ),
            ),
        ]
    )


def record_090():
    ticks = [
        tick(1680, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(6280, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6398, -0.03, -0.03, -0.03, -0.01, 0.01),
        tick(6710, -0.10, -0.08, -0.08, -0.04, 0.02),
        tick(8200, -0.04, -0.04, -0.04, -0.02, 0.01),
        tick(540000000, -0.03, -0.03, -0.04, -0.01, 0.00),
    ]
    excerpt = excerpt_items(
        [
            (500, 3),
            (1900, 18),
            (3400, 31),
            (4900, 7),
            (6400, 22),
            (8000, 11),
            (9600, 40),
            (11300, 1),
            (13100, 27),
            (15000, 44),
            (16900, 9),
            (18800, 35),
            (20600, 15),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "CCS Combo-2 at Shale-Quay stall CQ-6 is holding 312 A DC while the cable-core "
                "thermistor reads 91.2 C against an 85.0 C insulation cap. AC precharge is 18 A, "
                "safely under its 32 A cap. Temp-first should bind a DC current hold; a weak "
                "supervisor instead treats the thermal loop as the AC precharge contactor.",
            ),
            ("domain", "ev-charging"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep CCS DC current under the cable-core 85.0 C cap, leave AC precharge at the "
                "planned 18 A, and finish the 80 percent SOC session.",
            ),
            ("t0_us", 1756838404000090),
            ("gate_latency_us", 430),
            ("race_window_us", 250),
            ("race_window_rel_ms", [6.2, 6.45]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "cable.core.C 91.2 C on insulation",
                                "evse.dc.A 312 A session current",
                            ],
                        ),
                        (
                            "semantics",
                            "Temp-first should latch DC current clamp 312 -> 180 A; AC-first is a "
                            "false 'thermal-loop' bind that freezes precharge instead.",
                        ),
                        (
                            "window_derivation",
                            "250 us = one cable NTC sample versus the EVSE DC current publisher "
                            "on this CCS PLC slot.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 118 us vs combined jitter 46 us (NTC 22 + EVSE 24). Order is "
                            "correctly temp-first. The error is which loop the clamp is bound to, "
                            "not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "cable-core NTC, 2 kHz, 22 us jitter, axis cable_core",
                    "EVSE DC current shunt, 4 kHz, 24 us jitter",
                    "AC precharge current (context)",
                    "inlet latch (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("temp_cap_C", 85.0),
                        ("observed_core_C", 91.2),
                        ("temp_axis", "cable_core"),
                        ("dc_A", 312.0),
                        ("ac_precharge_A", 18.0),
                        ("ac_precharge_cap_A", 32.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. CQ-6 CCS Combo-2 at 312 A DC; cable-core 91.2 C.",
                    "2. AC precharge 18 A under 32 A cap; session at 64 percent SOC.",
                    "3. Inlet precursor at 1.680 ms.",
                    "4. Race window [6.200, 6.450] ms.",
                    "5. Cable-core 91.2 C at 6.280 ms (winner).",
                    "6. EVSE DC 312 A at 6.398 ms (loser by 118 us).",
                    "7. Gate at 6.710 ms: WRONG-MODIFY clamps AC precharge 18 -> 6 A; DC left at 312 A.",
                    "8. Core stays 91.8 C over 85.0 cap; jacket softens.",
                    "9. Session abort; connector derated.",
                    "10. Delayed (9 min / delayed_surprise_s=540): stall CQ-6 outage while the cable cools.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_ccs_312a"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("dc_A", 312.0),
                        ("ac_precharge_A", 18.0),
                        ("target_soc", 0.80),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("core_C", 91.2),
                        ("temp_cap_C", 85.0),
                        ("temp_axis", "cable_core"),
                        ("dc_A", 312.0),
                        ("ac_precharge_A", 18.0),
                        ("ac_precharge_cap_A", 32.0),
                        ("race_margin_us", 118),
                        ("combined_jitter_us", 46),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes holding 312 A DC with AC precharge at 18 A. The NTC read is on "
                "cable_core, not the AC precharge contactor.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Cable-core 91.2 C exceeds the 85.0 C insulation cap (true). At this SOC the AC "
                "precharge contactor is the proximal thermal loop (planned 18 A << 32 A cap). "
                "Clamp AC precharge from 18 A to 6 A to bleed cable heat before the jacket softens.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "cable_core_C",
                            OrderedDict(
                                [
                                    ("cap", 85.0),
                                    ("observed", 91.2),
                                    ("executed", 91.8),
                                    ("temp_axis", "cable_core"),
                                ]
                            ),
                        ),
                        (
                            "ac_precharge_A",
                            OrderedDict(
                                [
                                    ("cap", 32.0),
                                    ("planned", 18.0),
                                    ("clamped_wrong", 6.0),
                                ]
                            ),
                        ),
                        (
                            "dc_A",
                            OrderedDict(
                                [
                                    ("proposed", 312.0),
                                    ("executed", 312.0),
                                    ("correct_clamp_would_be", 180.0),
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
            ("name", "ac_precharge_hold_wrong_loop"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("dc_A", 312.0),
                        ("ac_precharge_A", 6.0),
                        ("target_soc", 0.80),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect): AC precharge 18 -> 6 A; DC left at 312 A. Routing "
                "relay.temp.core -> policy.ac_precharge_hold; no positive weight to "
                "policy.dc_current_clamp.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY froze AC precharge while DC stayed at 312 A over the 85.0 C core cap. "
                "Jacket soften plus 9 min stall abort. Correct gate was MODIFY on DC 312 -> 180 A, "
                "AC precharge left at 18 A.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("ac_precharge", "clamped to 6 A; planned 18 A abandoned"),
                        ("dc_A", "still 312 A; core 91.8 C over 85.0 cap"),
                        ("cable", "jacket soften; session aborted"),
                        ("stall", "9 min outage"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "AC freeze did not reduce DC I2R; core stayed 91.8 C.",
                    "Delayed (9 min / delayed_surprise_s=540): stall CQ-6 abort while the cable cools; connector derate logged.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY on DC current: 312 -> 180 A; leave AC precharge at planned 18 A.",
                        ),
                        ("correct_loop", "dc_current"),
                        ("wrong_loop", "ac_precharge"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("ac_precharge_A", 6.0), ("dc_A", 312.0)]),
                        ),
                        (
                            "cost",
                            "jacket soften + 9 min abort (task/efficiency); core still over cap (safety near-miss).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "cable.core.C (6.280 ms, 91.2 C)"),
                        ("loser", "evse.dc.A (6.398 ms, 312 A)"),
                        ("margin_us", 118),
                        (
                            "counterfactual_if_reversed",
                            "DC-first by < 118 us would still be a 312 A session under an 85.0 C "
                            "cap already broken; a correct gate binds NTC to DC current either way. "
                            "The wrong MODIFY spent the temp win on the AC precharge loop.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6710),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong clamp (6.710 ms, tick 4). The 9 min "
                "abort is delayed surprise bound to raster.delayed_surprise_s=540, not the inflection.",
            ),
            ("delayed_surprise_s", 540),
        ]
    )
    spikes = [
        spike("inlet.latch.ctx", 0.810, 0.41),
        spike("cable.core.C", 2.440, 0.64),
        spike("evse.dc.A", 3.880, 0.55),
        spike("ac.precharge.A", 5.020, 0.47),
        spike("cable.core.C", 6.280, 1.38),
        spike("evse.dc.A", 6.398, 1.15),
        spike("ctrl.gate", 6.710, 0.99),
        spike("cable.core.C", 8.200, 0.84),
        spike("evse.dc.A", 10.440, 0.66),
        spike("ctrl.gate", 13.100, 0.86),
        spike("ac.precharge.A", 16.800, 0.52),
        spike("cable.core.C", 19.400, 0.58),
    ]
    ras = raster_core(
        21,
        48,
        50,
        50,
        routing(
            "relay.temp.core",
            "policy.ac_precharge_hold",
            [
                ("relay.temp.core", "policy.ac_precharge_hold", 0.73),
                ("relay.evse.dc", "policy.ac_precharge_hold", 0.21),
            ],
            "histamine",
            0.07,
            "thermal_cap_stdp; HA tags the (wrong) ac_precharge_hold bind at the NTC win",
        ),
        excerpt,
        extra=OrderedDict([("delayed_surprise_s", 540)]),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.25),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("ac_precharge_hold", 32, 0.50, 400.0, 3),
                    pop("dc_current_clamp", 32, 0.80, 20.0, 0),
                    pop("temp_cap_veto", 16, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r14-090"),
            (
                "title",
                "WRONG-MODIFY at Shale-Quay stall CQ-6 / CCS Combo-2: core 91.2 C read correctly; "
                "clamp applied to AC precharge not DC current",
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
                    "Wrong-modify. Sidecar arithmetic 91.2 > 85.0 is true; clamp bound to AC "
                    "precharge. total -0.79 = -0.26 + -0.24 + -0.24 + -0.11 + 0.06. Tick 6 t_us "
                    "binds raster.delayed_surprise_s=540.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "ev-charging",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-loop",
                        "sidecar-convictable",
                        "tick6-sidecar-bound",
                        "designed",
                    ],
                    "Teaches a probe that a correct core_C>cap read can still be a wrong gate when "
                    "routing.table[0].to is policy.ac_precharge_hold and executed dc_A is not reduced.",
                    5,
                    supervisor_error_type="wrong-modify",
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


def walk_keys(obj, prefix=""):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            if str(k).lower() in FORBIDDEN_KEYS:
                found.append(path)
            found.extend(walk_keys(v, path))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(walk_keys(v, f"{prefix}[{i}]"))
    return found


def self_check(records):
    issues = []
    descs = [r["state"]["description"] for r in records]
    opens = [d.split(".")[0] for d in descs]
    if len(set(opens)) != 5:
        issues.append("opening sentences not unique")
    jmax = 0.0
    jpairs = []
    for i in range(5):
        for j in range(i + 1, 5):
            val = jaccard(descs[i], descs[j])
            jpairs.append((val, records[i]["id"], records[j]["id"]))
            jmax = max(jmax, val)
            if val >= 0.4:
                issues.append(f"Jaccard {records[i]['id']}/{records[j]['id']} = {val:.3f}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r14-090":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if decisions != ["MODIFY", "MODIFY", "REJECT", "ACCEPT", "MODIFY"]:
        issues.append(f"decision mix {decisions}")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domains not unique {domains}")
    banned = {
        "warehouse-amr",
        "aerial-swarm",
        "underwater-rov",
        "grid-inspection",
        "humanoid-locomotion",
    }
    if set(domains) & banned:
        issues.append(f"banned r12 domains {set(domains) & banned}")
    plants = json.dumps(records)
    for name in (
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
        "Calyx-9",
        "Spindle-H6",
        "Plover-4",
    ):
        if name in plants:
            issues.append(f"cloned plant token {name}")
    for rec in records:
        rid = rec["id"]
        if rec["meta"]["round"] != 14:
            issues.append(f"{rid} round")
        if rec["meta"]["factory"] != "thalamic-trajectory-factory":
            issues.append(f"{rid} factory")
        if rec["meta"]["generator"] != "grok-4.6":
            issues.append(f"{rid} generator")
        if rec["meta"]["run_label"] != "2026-09-02-final-heavy":
            issues.append(f"{rid} run_label")
        rights = rec["meta"]["rights"]
        if list(rights.keys()) != list(RIGHTS.keys()):
            issues.append(f"{rid} rights keys {list(rights.keys())}")
        if rights["intended_use"] != "research_only":
            issues.append(f"{rid} intended_use")
        if rights["linear_issue"] != "RM-793":
            issues.append(f"{rid} linear")
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rid} training_ready present")
        if '"real"' in blob and rec["state"]["sim_or_real"] != "real":
            # allow the word in prose only if not a sim_or_real value; still scan values
            pass
        forbidden = walk_keys(rec)
        if forbidden:
            issues.append(f"{rid} forbidden keys {forbidden}")
        err = check_refractory(rec["spike_events"])
        if err:
            issues.append(f"{rid} refractory {err}")
        err = check_race(rec)
        if err:
            issues.append(f"{rid} {err}")
        n_spk = len(rec["spike_events"])
        if not (5 <= n_spk <= 40):
            issues.append(f"{rid} spike count {n_spk}")
        times = [ev["t_rel_ms"] for ev in rec["spike_events"]]
        if times != sorted(times):
            issues.append(f"{rid} spike order")
        n = rec["raster"]["neurons"]
        rate = rec["raster"]["mean_rate_hz"]
        window_s = rec["raster"]["window_s"]
        expected = round(n * rate * window_s)
        if abs(rec["raster"]["spikes"] - expected) > 1:
            issues.append(f"{rid} spike budget {rec['raster']['spikes']} vs {expected}")
        if rec["raster"]["energy_pJ"] != rec["raster"]["spikes"] * 23:
            issues.append(f"{rid} energy")
        overlap = excerpt_vs_spikes(rec)
        if rec["id"] == "ttf-r14-086":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("086 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("086 inflection outside window")
        elif overlap >= 0.8:
            issues.append(f"{rid} excerpt overlap {overlap:.2f}")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_times = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_times:
            issues.append(f"{rid} inflection {inf} not a tick")
        if not (3 <= len(rec["reward_components"]["ticks"]) <= 8):
            issues.append(f"{rid} tick count")
        delayed = rec["raster"]["delayed_surprise_s"]
        if rec["reward_components"]["ticks"][-1]["t_us"] != delayed * 1_000_000:
            issues.append(f"{rid} tick6 not bound to delayed_surprise_s")
        if rec["future_outcome"].get("delayed_surprise_s") != delayed:
            issues.append(f"{rid} future delayed_surprise_s mismatch")
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rid} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rid} gate_snn decision mismatch")
        tf = rec["raster"]["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            issues.append(f"{rid} tau pair")
        gl = rec["state"]["gate_latency_us"]
        rw = rec["state"]["race_window_us"]
        if not (50 <= gl <= 2000):
            issues.append(f"{rid} gate_latency")
        if not (50 <= rw <= 1000):
            issues.append(f"{rid} race_window")
        heads = ["task_progress", "safety", "efficiency", "coherence", "exploration"]
        total = sum(rec["reward_components"][h] for h in heads)
        if abs(total - rec["reward_components"]["total"]) > 1e-6:
            issues.append(f"{rid} total mismatch {total}")
        if rec["reward_components"]["_aggregation"] != AGG:
            issues.append(f"{rid} aggregation")
        for h in heads:
            s = sum(t[h] for t in rec["reward_components"]["ticks"])
            if abs(s - rec["reward_components"][h]) > 1e-6:
                issues.append(f"{rid} {h} tick sum {s} vs {rec['reward_components'][h]}")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rid} ACCEPT params differ")
        win_ms = rec["raster"]["window_ms"]
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= win_ms * 1000):
                issues.append(f"{rid} excerpt t_us")
            if not (0 <= item["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rid} neuron_id")
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for p in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in p:
                exp = round(p["neurons"] * p["mean_rate_hz"] * dw_s)
                if abs(p["spikes"] - exp) > 1:
                    issues.append(f"{rid} gate pop {p['name']} spikes {p['spikes']} vs {exp}")
    r13 = Path("/tmp/ttf-r13/batch-r13.jsonl")
    jmax_r13 = 0.0
    if r13.exists():
        prior = [json.loads(line) for line in r13.read_text().splitlines() if line.strip()]
        for rec in records:
            for old in prior:
                val = jaccard(rec["state"]["description"], old["state"]["description"])
                jmax_r13 = max(jmax_r13, val)
                if val >= 0.4:
                    issues.append(f"Jaccard vs r13 {rec['id']}/{old['id']} = {val:.3f}")
    return issues, jmax, jmax_r13, jpairs


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_086(), record_087(), record_088(), record_089(), record_090()]
    issues, jmax, jmax_r13, jpairs = self_check(records)
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {BATCH_PATH} lines={len(lines)} jmax={jmax:.3f} jmax_r13={jmax_r13:.3f}")
    for val, a, b in sorted(jpairs, reverse=True)[:5]:
        print(f"  pair {a}/{b} j={val:.3f}")
    if issues:
        print("SELF_CHECK_ISSUES:")
        for item in issues:
            print(" -", item)
        return 1
    print("SELF_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
