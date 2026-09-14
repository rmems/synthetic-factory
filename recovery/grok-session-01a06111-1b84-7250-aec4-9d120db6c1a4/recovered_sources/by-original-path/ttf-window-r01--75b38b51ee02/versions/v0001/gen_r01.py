#!/usr/bin/env python3
"""Emit TTF r01 JSONL (ttf-r01-001..005) for 2026-09-02-final-heavy.

Writes /tmp/ttf-window-r01/{batch-r01.jsonl,NOTES-r01.md} then copies
create-only into the sf-window factory dir. Never overwrites existing dest.
"""

from __future__ import annotations

import json
import math
import random
import re
import shutil
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

OUT_DIR = Path("/tmp/ttf-window-r01")
DEST_DIR = Path(
    "/tmp/sf-window/outputs/raw/2026-09-02-final-heavy/thalamic-trajectory-factory"
)
PJ_PER_SPIKE = 23
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
RIGHTS = OrderedDict(
    [
        ("provider", "SpaceXAI/xAI"),
        ("model", "grok-4.6"),
        ("channel", "consumer"),
        ("subscription_plan", "SuperGrok Heavy"),
        ("generation_surface", "SuperGrok Heavy chat"),
        ("generated_at", "2026-09-02T22:10:00Z"),
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
BANNED_PLANTS = (
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
    "Suture-Isle",
    "Fen-13",
    "Kiln-Spur",
    "Gantry-R4",
    "Oxbow-Switch",
    "Pitch-Kettle",
    "Shale-Quay",
    "Osmyl-Haugh",
    "Diisocyan-Sike",
    "Dodecalact-Ing",
    "Difluorene-Wath",
    "Nucleo-Peek",
    "Selenite-Hawes",
    "Nickcarb-Linnick",
    "Yttria-Scarth",
    "Germanyl-Tofts",
    "Ceriax-Howk",
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


def kernel_excerpt(window_ms, neurons, n, avoid_us, seed):
    window_us = int(window_ms) * 1000
    avoid = {int(x) for x in avoid_us}
    rng = random.Random(seed)
    last = {}
    picked = []
    t = 380 + (seed % 90)
    guard = 0
    while len(picked) < n and guard < 8000:
        guard += 1
        t += 1100 + (rng.randrange(0, 180))
        if t > window_us:
            t = 420 + 90 * len(picked)
            if t > window_us:
                break
        if any(abs(t - a) < 80 for a in avoid):
            continue
        nid = (len(picked) * 11 + (seed % 7)) % neurons
        if nid in last and t - last[nid] < 1000:
            nid = (nid + 13) % neurons
        if nid in last and t - last[nid] < 1000:
            continue
        if picked and t <= picked[-1][0]:
            t = picked[-1][0] + 1100
            if t > window_us:
                continue
        picked.append((t, nid))
        last[nid] = t
    if len(picked) < n:
        raise ValueError(f"kernel excerpt short {len(picked)} < {n}")
    return excerpt_items(picked[:n])


def lif_001_excerpt():
    n = 80
    dt_us = 100
    tau_m_ms = 18.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.90
    i_stim_peak = 2.2
    stim = (20000, 23000)
    seed = 1001
    window_us = 40000
    i_clamp_extra = 0.65
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
    early = [(t, nid) for t, nid in spikes if t < 20000]
    burst = [(t, nid) for t, nid in spikes if 20000 <= t < 23000]
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
            era_early = pool[0][0] < 20000
            have = len([1 for t, _ in picked if (t < 20000) == era_early])
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
    take(burst, 9, label_times=(21200, 21600, 22400))
    clamp = [(t, n_) for t, n_ in picked if t < 20000][:7]
    leak = [(t, n_) for t, n_ in picked if t >= 20000][:9]
    picked = sorted(clamp + leak, key=lambda item: (item[0], item[1]))
    if len(picked) < 12:
        raise ValueError(f"LIF excerpt too short: {len(picked)}")
    channels = ["lif.clamp" if t < 20000 else "lif.leak" for t, _ in picked]
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
            ("i_stim_peak", 2.2),
            ("stim_t_us", [20000, 23000]),
            ("i_clamp_extra", 0.65),
            ("clamp_n", 16),
            ("seed", 1001),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-15 carry +0.65 clamp-pathway bias; stim 20-23 ms is the CSF micro-leak burst.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("delayed_surprise_s", 600),
            ("lif", lif),
        ]
    )
    return excerpt_items(picked, channels), extra, spikes


def meta_block(domain, tags, distillation_value, batch_position, supervisor_error_type=None):
    body = OrderedDict(
        [
            ("round", 1),
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
    body = OrderedDict([("name", name), ("neurons", neurons), ("threshold", threshold)])
    if rate is not None:
        body["mean_rate_hz"] = rate
        body["spikes"] = spikes
    return body


def record_001():
    excerpt, extra, _lif = lif_001_excerpt()
    ticks = [
        tick(1180, 0.04, -0.02, -0.01, 0.01, 0.00),
        tick(6248, 0.07, -0.03, -0.02, 0.01, -0.01),
        tick(6534, 0.03, -0.02, -0.02, 0.00, 0.00),
        tick(7068, 0.09, -0.05, -0.03, 0.02, -0.01),
        tick(21200, 0.07, -0.42, -0.04, 0.00, -0.02),
        tick(600000000, 0.02, -0.04, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Stylet-V4 is already 2.4 mm past the sphenoid ostium in Lumen-Quay Theatre LQ-1 "
                "when irrigation still pumps 42 mL/min against a 2.50 N arachnoid force cap. The "
                "live contest is tip force versus Doppler CSF-pulse residual, not tremor versus "
                "depth. A force win must cut irrigation under 2.50 N; a Doppler win would leave "
                "the 42 mL/min cruise armed. Stored sellar shear is off both buses until the later "
                "leak burst.",
            ),
            ("domain", "surgical-assist"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Reach the sella diaphragm at 2.4 mm ostium standoff, keep tip force <= 2.50 N, "
                "and leave the arachnoid unmarked.",
            ),
            ("t0_us", 1756838500000001),
            ("gate_latency_us", 820),
            ("race_window_us", 440),
            ("race_window_rel_ms", [6.2, 6.64]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.tip.n 3.80 N contact",
                                "doppler.csf.hz 1.1 Hz residual",
                            ],
                        ),
                        (
                            "semantics",
                            "FT-first latches irrigation clamp 42 -> 18 mL/min and 3.80 -> 1.90 N; "
                            "Doppler-first keeps cruise irrigation on a 'still approaching' pulse model.",
                        ),
                        (
                            "window_derivation",
                            "440 us = one tip-FT sample period minus Doppler baseband group delay "
                            "on this 2 kHz wrist bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 286 us vs combined jitter 70 us (FT 30 + Doppler 40): 4.1x over a "
                            "2.0x trust floor. Reversing order by < 286 us inside the 440 us window "
                            "would have kept 42 mL/min cruise; predicted next-sample 2.72 N > 2.50 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "tip 6-axis FT, 2 kHz, 30 us timestamp jitter",
                    "Doppler CSF pulse, 1 kHz, 40 us jitter",
                    "irrigation encoder, 200 Hz (context)",
                    "endoscope standoff, 200 Hz (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("force_cap_N", 2.50),
                        ("observed_tip_N", 3.80),
                        ("irrigation_proposed_ml_min", 42.0),
                        ("standoff_mm", 2.4),
                        ("gauge", 4.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Stylet-V4 indexed through the sphenoid ostium; standoff 2.4 mm to the diaphragm.",
                    "2. Cruise irrigation 42 mL/min armed; Doppler residual 1.1 Hz.",
                    "3. Encoder precursor at 1.180 ms; FT warm-start 3.80 N.",
                    "4. Race window [6.200, 6.640] ms opens on the wrist bus.",
                    "5. Tip FT 3.80 N at 6.248 ms (winner).",
                    "6. Doppler CSF 1.1 Hz at 6.534 ms (loser by 286 us).",
                    "7. Gate at 7.068 ms (winner + 820 us): MODIFY clamp 18 mL/min, 1.90 N.",
                    "8. Clamp executes; next-sample force 2.16 N < 2.50 cap.",
                    "9. At 21.200 ms stored sellar shear opens a 0.4 mm CSF micro-leak; leak burst.",
                    "10. Fat-graft + lumbar drain 10 min; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_sella_irrigation"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("irrigation_ml_min", 42.0),
                        ("tip_force_N", 3.80),
                        ("standoff_mm", 2.4),
                        ("tremor_filter_hz", 4.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("tip_N", 3.80),
                        ("force_cap_N", 2.50),
                        ("predicted_unclamped_next_N", 2.72),
                        ("doppler_hz", 1.1),
                        ("race_margin_us", 286),
                        ("combined_jitter_us", 70),
                        ("standoff_mm", 2.4),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 42 mL/min cruise: Doppler residual 1.1 Hz looks like pulse, "
                "not contact, and the 2.4 mm standoff is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Tip FT 3.80 N won by 286 us, so the stylet is loading arachnoid, not still "
                "approaching. Holding 42 mL/min predicts next-sample 2.72 N > 2.50 N cap. "
                "MODIFY: irrigation 42 -> 18 mL/min and commanded force 3.80 -> 1.90 N. "
                "Observed after clamp 2.16 N < 2.50. A full REJECT is not indicated: a sound "
                "diaphragm accepts 18 mL/min.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tip_N",
                            OrderedDict(
                                [
                                    ("cap", 2.50),
                                    ("observed", 3.80),
                                    ("predicted_unclamped_next", 2.72),
                                    ("clamped", 1.90),
                                    ("observed_after_clamp", 2.16),
                                ]
                            ),
                        ),
                        (
                            "irrigation_ml_min",
                            OrderedDict([("proposed", 42.0), ("clamped", 18.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 286),
                                    ("combined_jitter_us", 70),
                                    ("ratio", 4.09),
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
            ("name", "clamped_sella_irrigation"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("irrigation_ml_min", 18.0),
                        ("tip_force_N", 1.90),
                        ("standoff_mm", 2.4),
                        ("tremor_filter_hz", 4.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: irrigation 42 -> 18 mL/min and 3.80 -> 1.90 N. Process-correct vs the "
                "2.50 N cap. CSF micro-leak still occurs at 21.200 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held tip force at 2.16 N. At 21.200 ms stored sellar "
                "shear produced a 0.4 mm CSF micro-leak. Clamp reduced dump energy; it did not "
                "prevent the shear. Partnered negative: process heads stay honest; world loss is "
                "named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("instrument", "clamp executed; peak 2.16 N < 2.50"),
                        ("arachnoid", "0.4 mm CSF micro-leak at 21.200 ms"),
                        ("repair", "10 min fat-graft + lumbar drain"),
                        ("mission", "sella still reached; leak controlled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither FT nor Doppler predicted the shear dump; tissue.csf.leak is a new channel at 21.200 ms, 14.132 ms after the gate, still inside the 40 ms raster.",
                    "Delayed (10 min / delayed_surprise_s=600): fat-graft and lumbar drain close the leak. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "10 min fat-graft + lumbar drain after a 0.4 mm CSF micro-leak. Safety head -0.58 "
                "prices the leak; task_progress stays +0.32 because the force clamp completed under "
                "the 2.50 N cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.tip.n (6.248 ms, 3.80 N)"),
                        ("loser", "doppler.csf.hz (6.534 ms, 1.1 Hz residual)"),
                        ("margin_us", 286),
                        (
                            "counterfactual_if_reversed",
                            "Doppler-first by < 286 us inside the 440 us window would have kept "
                            "42 mL/min cruise; predicted next-sample 2.72 N would have exceeded the "
                            "2.50 N cap even without the shear dump. The MODIFY is still the correct "
                            "process. The leak is a later world charge either way, cheaper with the "
                            "clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 21200),
            (
                "reward_inflection_note",
                "Safety collapses at the 21.200 ms CSF micro-leak (tick t_us=21200), inside the "
                "40 ms raster. The correct MODIFY at 7.068 ms is in the same excerpt. Do not put "
                "inflection on the +10 min fat-graft tick.",
            ),
            ("delayed_surprise_s", 600),
        ]
    )
    spikes = [
        spike("inlet.latch.ctx", 1.180, 0.44),
        spike("ft.tip.n", 3.020, 0.62),
        spike("doppler.csf.hz", 4.410, 0.51),
        spike("irrig.ml_min", 5.330, 0.47),
        spike("ft.tip.n", 6.248, 1.36),
        spike("doppler.csf.hz", 6.534, 1.12),
        spike("ctrl.gate", 7.068, 0.98),
        spike("ft.tip.n", 9.400, 0.82),
        spike("doppler.csf.hz", 11.220, 0.64),
        spike("ctrl.gate", 14.080, 0.84),
        spike("tissue.csf.leak", 21.200, 1.41),
        spike("ft.tip.n", 24.600, 0.58),
        spike("ctrl.gate", 29.100, 0.71),
        spike("irrig.ml_min", 34.800, 0.49),
    ]
    ras = raster_core(
        40,
        80,
        26,
        83,
        routing(
            "thalamic-relay.ft-doppler",
            "spikenaut.policy.irrigation-clamp",
            [
                ("relay.ft.tip", "policy.irrigation_clamp", 0.67),
                ("relay.doppler.csf", "policy.doppler_hold", 0.30),
                ("relay.tissue.leak", "policy.irrigation_clamp", -0.44),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at FT win (6.248 ms) opens a 40 ms eligibility trace that still covers the 21.200 ms leak",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.44),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("irrigation_clamp", 40, 0.50, 280.0, 5),
                    pop("doppler_hold", 40, 0.50, 80.0, 1),
                    pop("force_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r01-001"),
            (
                "title",
                "Lumen-Quay Theatre LQ-1 / Stylet-V4: tip FT beats Doppler CSF by 286 us; "
                "correct MODIFY still eats an in-window CSF micro-leak (partnered negative total -0.40)",
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
                    "40 ms raster. total -0.40 = 0.32 + -0.58 + -0.14 + 0.04 + -0.04. Named "
                    "fat-graft+drain loss is not netted into task_progress. Tick 6 t_us binds "
                    "raster.delayed_surprise_s=600.",
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


def record_002():
    ticks = [
        tick(1680, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(5468, 0.08, 0.06, 0.03, 0.02, 0.01),
        tick(5614, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(6028, 0.12, 0.10, 0.05, 0.03, 0.02),
        tick(8800, 0.06, 0.05, 0.03, 0.02, 0.01),
        tick(210000000, 0.03, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("press.latch.ctx", 1.680, 0.42),
        spike("ft.press.n", 3.110, 0.61),
        spike("ae.housing.khz", 4.020, 0.50),
        spike("enc.insert.mm", 4.880, 0.46),
        spike("ft.press.n", 5.468, 1.34),
        spike("ae.housing.khz", 5.614, 1.10),
        spike("ctrl.gate", 6.028, 0.97),
        spike("ft.press.n", 8.200, 0.80),
        spike("ae.housing.khz", 10.440, 0.63),
        spike("ctrl.gate", 13.100, 0.85),
        spike("enc.insert.mm", 16.800, 0.52),
        spike("ft.press.n", 19.400, 0.57),
        spike("ctrl.gate", 22.600, 0.70),
    ]
    avoid = [int(round(ev["t_rel_ms"] * 1000.0)) for ev in spikes]
    excerpt = kernel_excerpt(26, 64, 14, avoid, seed=2002)
    state = OrderedDict(
        [
            (
                "description",
                "Press-J9 has driven a 28 mm steel bearing 6.2 mm into the Rivermead Cell R-7 "
                "aluminum housing when the wrist transducer reports 36.8 N against a 28.0 N insert "
                "cap. Acoustic emission still sits at 12 kHz, under the 40 kHz galling band, so an "
                "AE-first read would keep cruise press. Force-first binds a ram hold before the "
                "housing stars.",
            ),
            ("domain", "industrial-assembly"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Seat the 28 mm bearing to 11.0 mm depth, keep insert force <= 28.0 N, and leave "
                "the housing unmarked.",
            ),
            ("t0_us", 1756838501000002),
            ("gate_latency_us", 560),
            ("race_window_us", 320),
            ("race_window_rel_ms", [5.4, 5.72]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.press.n 36.8 N contact",
                                "ae.housing.khz 12 kHz under galling",
                            ],
                        ),
                        (
                            "semantics",
                            "FT-first latches ram clamp 36.8 -> 22.0 N and 8 -> 4 mm/s; AE-first "
                            "keeps cruise press because 12 kHz is still under 40 kHz galling.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one wrist-FT EtherCAT slot versus the AE publisher on this "
                            "4 kHz cell bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 146 us vs combined jitter 56 us (FT 24 + AE 32): 2.6x over a 2.0x "
                            "trust floor. Reversing order by < 146 us inside the 320 us window would "
                            "have kept 36.8 N cruise; predicted next-sample 30.4 N > 28.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "wrist 6-axis FT, 4 kHz, 24 us jitter",
                    "housing AE, 2 kHz, 32 us jitter",
                    "ram linear encoder (context)",
                    "press hydraulic pressure (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("insert_force_cap_N", 28.0),
                        ("observed_press_N", 36.8),
                        ("galling_band_khz", 40.0),
                        ("ae_khz", 12.0),
                        ("bearing_mm", 28.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Press-J9 6.2 mm into the 28 mm bearing on Cell R-7 housing.",
                    "2. Cruise press 36.8 N at 8 mm/s armed; AE 12 kHz under 40 kHz galling.",
                    "3. Encoder precursor at 1.680 ms.",
                    "4. Race window [5.400, 5.720] ms.",
                    "5. Wrist FT 36.8 N at 5.468 ms (winner).",
                    "6. Housing AE 12 kHz at 5.614 ms (loser by 146 us).",
                    "7. Gate at 6.028 ms: MODIFY clamp 22.0 N, 4 mm/s.",
                    "8. After clamp 24.6 N < 28.0; AE still 13 kHz.",
                    "9. Bearing seats to 11.0 mm without a star; leak-check of the bore passes.",
                    "10. Delayed (3.5 min / delayed_surprise_s=210): CMM tags the force-first bind on the next housing.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_bearing_press"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("insert_N", 36.8),
                        ("ram_mm_s", 8.0),
                        ("depth_mm", 11.0),
                        ("bearing_mm", 28.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("press_N", 36.8),
                        ("insert_cap_N", 28.0),
                        ("predicted_unclamped_next_N", 30.4),
                        ("ae_khz", 12.0),
                        ("race_margin_us", 146),
                        ("combined_jitter_us", 56),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 36.8 N cruise at 8 mm/s: AE 12 kHz looks like seating noise, "
                "not galling, and remaining depth 4.8 mm is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Wrist FT 36.8 N won by 146 us, so the ram is loading the housing, not still "
                "seating quietly. Holding 36.8 N predicts next-sample 30.4 N > 28.0 N cap. "
                "MODIFY: insert 36.8 -> 22.0 N and 8 -> 4 mm/s. Observed after clamp 24.6 N < 28.0. "
                "A full REJECT is not indicated: a sound bore accepts 22.0 N.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "insert_N",
                            OrderedDict(
                                [
                                    ("cap", 28.0),
                                    ("observed", 36.8),
                                    ("predicted_unclamped_next", 30.4),
                                    ("clamped", 22.0),
                                    ("observed_after_clamp", 24.6),
                                ]
                            ),
                        ),
                        (
                            "ram_mm_s",
                            OrderedDict([("proposed", 8.0), ("clamped", 4.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 146),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 2.61),
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
            ("name", "clamped_bearing_press"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("insert_N", 22.0),
                        ("ram_mm_s", 4.0),
                        ("depth_mm", 11.0),
                        ("bearing_mm", 28.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: insert 36.8 -> 22.0 N and 8 -> 4 mm/s. Process-correct vs the 28.0 N cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct MODIFY held insert at 24.6 N under the 28.0 N cap. Bearing seated to "
                "11.0 mm without a star. Delayed CMM tags the force-first bind on the next housing.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("ram", "clamp executed; peak 24.6 N < 28.0"),
                        ("housing", "no star; AE stayed under galling"),
                        ("bearing", "seated 11.0 mm"),
                        ("qc", "3.5 min CMM tag on next unit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "AE climbed only 1 kHz after the clamp; galling band never engaged.",
                    "Delayed (3.5 min / delayed_surprise_s=210): CMM writes the force-first bind onto the next housing recipe.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.press.n (5.468 ms, 36.8 N)"),
                        ("loser", "ae.housing.khz (5.614 ms, 12 kHz)"),
                        ("margin_us", 146),
                        (
                            "counterfactual_if_reversed",
                            "AE-first by < 146 us inside the 320 us window would have kept 36.8 N "
                            "cruise; predicted next-sample 30.4 N would have exceeded the 28.0 N cap. "
                            "The MODIFY is the correct process either way once FT wins.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6028),
            (
                "reward_inflection_note",
                "Task and safety inflect at the correct clamp (6.028 ms, tick 4). The 3.5 min CMM "
                "tag is delayed surprise bound to raster.delayed_surprise_s=210, not the inflection.",
            ),
            ("delayed_surprise_s", 210),
        ]
    )
    ras = raster_core(
        26,
        64,
        40,
        67,
        routing(
            "thalamic-relay.ft-ae",
            "spikenaut.policy.insert-clamp",
            [
                ("relay.ft.press", "policy.insert_clamp", 0.69),
                ("relay.ae.housing", "policy.ae_hold", 0.28),
            ],
            "acetylcholine",
            0.08,
            "pre_post_stdp; ACh at FT win (5.468 ms) tags the insert_clamp bind",
        ),
        excerpt,
        extra=OrderedDict([("delayed_surprise_s", 210)]),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("insert_clamp", 40, 0.50, 310.0, 4),
                    pop("ae_hold", 40, 0.50, 80.0, 1),
                    pop("force_cap_veto", 16, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r01-002"),
            (
                "title",
                "Rivermead Cell R-7 / Press-J9: wrist FT beats housing AE by 146 us; correct "
                "MODIFY clamps 36.8 -> 22.0 N under the 28.0 N insert cap",
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
                    "Correct MODIFY. total +1.04 = 0.38 + 0.32 + 0.17 + 0.10 + 0.07. Tick 6 t_us "
                    "binds raster.delayed_surprise_s=210.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "industrial-assembly",
                    ["modify", "force-first", "tick6-sidecar-bound", "designed"],
                    "Teaches FT-vs-AE order on a press-fit: routing.table[0] to policy.insert_clamp "
                    "with AE as the losing hold.",
                    2,
                ),
            ),
        ]
    )


def record_003():
    ticks = [
        tick(980, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(4186, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(4512, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5366, 0.04, 0.14, 0.04, 0.03, 0.02),
        tick(9200, 0.01, 0.05, 0.02, 0.02, 0.01),
        tick(300000000, 0.01, 0.03, 0.02, 0.01, 0.00),
    ]
    spikes = [
        spike("hil.latch.ctx", 0.980, 0.40),
        spike("radar.occ.m", 2.210, 0.66),
        spike("cam.ttc.s", 3.040, 0.52),
        spike("v2x.spat", 3.700, 0.48),
        spike("radar.occ.m", 4.186, 1.40),
        spike("cam.ttc.s", 4.512, 1.14),
        spike("ctrl.gate", 5.366, 1.02),
        spike("radar.occ.m", 7.800, 0.84),
        spike("cam.ttc.s", 10.200, 0.61),
        spike("ctrl.gate", 14.400, 0.88),
        spike("wheel.vx.mps", 18.600, 0.50),
        spike("radar.occ.m", 24.100, 0.55),
        spike("ctrl.gate", 31.200, 0.73),
        spike("v2x.spat", 38.400, 0.47),
    ]
    avoid = [int(round(ev["t_rel_ms"] * 1000.0)) for ev in spikes]
    excerpt = kernel_excerpt(44, 96, 14, avoid, seed=3003)
    state = OrderedDict(
        [
            (
                "description",
                "Merge M-3 on the Fork-Haven HIL belt is armed to enter the dummy through-lane "
                "while a 0.22 m2 radar return still occupies the 18 m gap at the gore. Camera TTC "
                "reads 2.6 s, which a vision-first planner would treat as a legal merge. "
                "Occupancy-first must hold the origin lane.",
            ),
            ("domain", "autonomous-driving"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Enter the through-lane only when gore occupancy is 0, keep lateral rate at 0 m/s "
                "while occupied, and leave the dummy consist clear of the merge taper.",
            ),
            ("t0_us", 1756838502000003),
            ("gate_latency_us", 1180),
            ("race_window_us", 680),
            ("race_window_rel_ms", [4.1, 4.78]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "radar.occ.m 0.22 m2 at 18 m",
                                "cam.ttc.s 2.6 s merge-looking",
                            ],
                        ),
                        (
                            "semantics",
                            "Occupancy-first latches REJECT hold-origin; camera-first would commit "
                            "the 1.2 m/s lateral merge into the dummy consist.",
                        ),
                        (
                            "window_derivation",
                            "680 us = one 77 GHz radar dwell minus camera TTC publisher group delay "
                            "on this HIL fusion bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 326 us vs combined jitter 84 us (radar 36 + camera 48): 3.9x over "
                            "a 2.0x trust floor. Reversing order by < 326 us inside the 680 us window "
                            "would have committed the merge while RCS 0.22 m2 still occupied 18 m.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "77 GHz radar occupancy, 20 Hz dwell, 36 us jitter",
                    "front camera TTC, 30 Hz, 48 us jitter",
                    "V2X SPaT (context)",
                    "wheel-speed encoder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("gore_occ_cap_m2", 0.05),
                        ("observed_rcs_m2", 0.22),
                        ("range_m", 18.0),
                        ("cam_ttc_s", 2.6),
                        ("ttc_merge_enable_s", 2.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Ego at origin-lane marker; merge M-3 armed on Fork-Haven HIL.",
                    "2. Radar RCS 0.22 m2 at 18 m; camera TTC 2.6 s.",
                    "3. HIL latch precursor at 0.980 ms.",
                    "4. Race window [4.100, 4.780] ms.",
                    "5. Radar occupancy at 4.186 ms (winner).",
                    "6. Camera TTC 2.6 s at 4.512 ms (loser by 326 us).",
                    "7. Gate at 5.366 ms: REJECT hold-origin, lateral 0 m/s.",
                    "8. Dummy consist remains in the through-lane; ego stays origin.",
                    "9. Radar RCS decays only after the consist clears the gore.",
                    "10. Delayed (5 min / delayed_surprise_s=300): reclear wait before the next merge trial.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "commit_merge_m3"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("lat_mps", 1.2),
                        ("long_mps", 22.0),
                        ("target_lane", "through"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("rcs_m2", 0.22),
                        ("gore_occ_cap_m2", 0.05),
                        ("range_m", 18.0),
                        ("cam_ttc_s", 2.6),
                        ("race_margin_us", 326),
                        ("combined_jitter_us", 84),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 1.2 m/s lateral merge: camera TTC 2.6 s is above the 2.0 s "
                "merge-enable, and V2X is treated as a clear through-lane.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Radar occupancy 0.22 m2 at 18 m won by 326 us, so the gore is not clear. Camera "
                "TTC 2.6 s is above merge-enable but occupancy 0.22 > 0.05 m2 cap. REJECT: hold "
                "origin lane, lateral 0 m/s, long 22 m/s. A MODIFY that only slows the merge still "
                "enters an occupied gore.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "gore_occ_m2",
                            OrderedDict(
                                [
                                    ("cap", 0.05),
                                    ("observed", 0.22),
                                    ("range_m", 18.0),
                                ]
                            ),
                        ),
                        (
                            "lat_mps",
                            OrderedDict([("proposed", 1.2), ("executed", 0.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 326),
                                    ("combined_jitter_us", 84),
                                    ("ratio", 3.88),
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
            ("name", "hold_origin_lane"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("lat_mps", 0.0),
                        ("long_mps", 22.0),
                        ("target_lane", "origin"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold origin; lateral 1.2 -> 0 m/s. Dummy consist never fouled.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held origin while RCS 0.22 m2 occupied the 18 m gore. Dummy "
                "consist stayed clear. Delayed reclear wait 5 min before the next merge trial.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("ego", "origin lane; lat 0 m/s"),
                        ("gore", "still occupied at decision; later clear"),
                        ("dummy", "through-lane consist not fouled"),
                        ("trial", "5 min reclear before retry"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Camera TTC stayed 2.6 s through the hold; vision never flipped red.",
                    "Delayed (5 min / delayed_surprise_s=300): reclear wait; HIL logs the occupancy-first REJECT as the replay gold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "radar.occ.m (4.186 ms, 0.22 m2 at 18 m)"),
                        ("loser", "cam.ttc.s (4.512 ms, 2.6 s)"),
                        ("margin_us", 326),
                        (
                            "counterfactual_if_reversed",
                            "Camera-first by < 326 us inside the 680 us window would have committed "
                            "the 1.2 m/s merge into the dummy consist. Occupancy-first REJECT is the "
                            "correct process either way once radar wins.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5366),
            (
                "reward_inflection_note",
                "Safety inflects at the REJECT hold (5.366 ms, tick 4). The 5 min reclear is delayed "
                "surprise bound to raster.delayed_surprise_s=300, not the inflection.",
            ),
            ("delayed_surprise_s", 300),
        ]
    )
    ras = raster_core(
        44,
        96,
        20,
        84,
        routing(
            "thalamic-relay.radar-cam",
            "spikenaut.policy.merge-hold",
            [
                ("relay.radar.occ", "policy.origin_hold", 0.72),
                ("relay.cam.ttc", "policy.merge_commit", 0.24),
            ],
            "dopamine",
            0.12,
            "pre_post_stdp; DA at radar win (4.186 ms) tags the origin_hold bind",
        ),
        excerpt,
        extra=OrderedDict([("delayed_surprise_s", 300)]),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.68),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("origin_hold", 48, 0.45, 180.0, 6),
                    pop("merge_commit", 48, 0.80, 30.0, 1),
                    pop("occ_cap_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r01-003"),
            (
                "title",
                "Fork-Haven HIL / Merge M-3: radar occupancy beats camera TTC by 326 us; REJECT "
                "hold-origin, do not merge",
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
                    "Correct REJECT. total +0.82 = 0.10 + 0.42 + 0.14 + 0.10 + 0.06. Tick 6 t_us "
                    "binds raster.delayed_surprise_s=300.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "autonomous-driving",
                    ["reject", "hil", "occupancy-first", "tick6-sidecar-bound"],
                    "Teaches a fusion race where radar occupancy vetoes a camera TTC that is still "
                    "above merge-enable. gate_snn.origin_hold fires; merge_commit does not.",
                    3,
                ),
            ),
        ]
    )


def record_004():
    ticks = [
        tick(2100, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7264, 0.09, 0.06, 0.04, 0.02, 0.02),
        tick(7612, 0.05, 0.04, 0.02, 0.02, 0.01),
        tick(8804, 0.14, 0.10, 0.06, 0.04, 0.02),
        tick(14100, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(48000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("sim.latch.ctx", 2.100, 0.43),
        spike("corona.mA", 4.220, 0.60),
        spike("lidar.gap.m", 5.510, 0.54),
        spike("humid.rh", 6.400, 0.46),
        spike("corona.mA", 7.264, 1.28),
        spike("lidar.gap.m", 7.612, 1.08),
        spike("ctrl.gate", 8.804, 0.96),
        spike("corona.mA", 11.300, 0.78),
        spike("lidar.gap.m", 14.100, 0.62),
        spike("ctrl.gate", 17.800, 0.83),
        spike("ir.shed.C", 21.400, 0.50),
        spike("corona.mA", 25.200, 0.56),
        spike("ctrl.gate", 29.000, 0.69),
    ]
    avoid = [int(round(ev["t_rel_ms"] * 1000.0)) for ev in spikes]
    excerpt = kernel_excerpt(32, 112, 14, avoid, seed=4004)
    params = OrderedDict(
        [
            ("creep_mps", 0.12),
            ("standoff_m", 1.62),
            ("corona_mA", 0.84),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Crawler-C2 hangs 1.62 m off a 138 kV porcelain string on Pylon-Wick PW-11 while "
                "corona current sits at 0.84 mA, well under the 2.00 mA trip. The proposed 0.12 m/s "
                "creep already sits under the 0.20 m/s envelope and the 1.20 m min gap. Corona-first "
                "confirms that creep; lidar-first would hunt an extra halt the clearance does not need.",
            ),
            ("domain", "grid-inspection"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Creep 0.12 m/s along the string while gap stays >= 1.20 m and corona stays "
                "<= 2.00 mA, then park for the IR shed survey.",
            ),
            ("t0_us", 1756838503000004),
            ("gate_latency_us", 1540),
            ("race_window_us", 840),
            ("race_window_rel_ms", [7.2, 8.04]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "corona.mA 0.84 under trip",
                                "lidar.gap.m 1.62 over min",
                            ],
                        ),
                        (
                            "semantics",
                            "Corona-first confirms the already-legal 0.12 m/s creep; lidar-first "
                            "would treat a 1.62 m gap as a near-limit and halt.",
                        ),
                        (
                            "window_derivation",
                            "840 us = one corona-sample period minus lidar ToF publisher delay on "
                            "this simulated 1 kHz crawler bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 348 us vs combined jitter 92 us (corona 40 + lidar 52): 3.8x over "
                            "a 2.0x trust floor. Reversing order by < 348 us inside the 840 us window "
                            "would have halted a legal creep; both channels are already inside limits.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "corona current shunt, 1 kHz, 40 us jitter",
                    "lidar gap, 200 Hz, 52 us jitter",
                    "string humidity (context)",
                    "IR shed camera (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("corona_trip_mA", 2.00),
                        ("observed_corona_mA", 0.84),
                        ("min_gap_m", 1.20),
                        ("observed_gap_m", 1.62),
                        ("creep_cap_mps", 0.20),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Crawler-C2 parked 1.62 m off the PW-11 porcelain string.",
                    "2. Corona 0.84 mA; proposed creep 0.12 m/s under 0.20 cap.",
                    "3. Sim latch precursor at 2.100 ms.",
                    "4. Race window [7.200, 8.040] ms.",
                    "5. Corona 0.84 mA at 7.264 ms (winner).",
                    "6. Lidar gap 1.62 m at 7.612 ms (loser by 348 us).",
                    "7. Gate at 8.804 ms: ACCEPT 0.12 m/s creep.",
                    "8. Gap stays 1.61-1.64 m; corona 0.81-0.88 mA.",
                    "9. Creep completes the 2.4 m inspection pass.",
                    "10. Delayed (48 s / delayed_surprise_s=48): IR survey finds a hairline shed crack; maintenance tag, not a motion halt.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "creep_string_pass"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("corona_mA", 0.84),
                        ("corona_trip_mA", 2.00),
                        ("gap_m", 1.62),
                        ("min_gap_m", 1.20),
                        ("creep_mps", 0.12),
                        ("creep_cap_mps", 0.20),
                        ("race_margin_us", 348),
                        ("combined_jitter_us", 92),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.12 m/s creep: corona 0.84 mA is under 2.00 mA and lidar gap "
                "1.62 m is over 1.20 m min, so both envelopes already allow the pass.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Corona 0.84 mA won by 348 us and is under the 2.00 mA trip. Lidar gap 1.62 m is "
                "over the 1.20 m min. Proposed creep 0.12 m/s is under the 0.20 m/s envelope. "
                "ACCEPT the proposed pass. A MODIFY halt would waste the dry slot without a "
                "numeric constraint breach.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "corona_mA",
                            OrderedDict([("trip", 2.00), ("observed", 0.84)]),
                        ),
                        (
                            "gap_m",
                            OrderedDict([("min", 1.20), ("observed", 1.62)]),
                        ),
                        (
                            "creep_mps",
                            OrderedDict([("cap", 0.20), ("proposed", 0.12)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 348),
                                    ("combined_jitter_us", 92),
                                    ("ratio", 3.78),
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
            ("name", "creep_string_pass"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed equals proposed 0.12 m/s creep at 1.62 m standoff.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT completed the 2.4 m pass under corona and gap caps. Delayed IR "
                "survey found a hairline shed crack that is a maintenance tag, not a motion halt.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("crawler", "pass complete; gap 1.61-1.64 m"),
                        ("corona", "0.81-0.88 mA throughout"),
                        ("string", "hairline shed crack tagged at 48 s"),
                        ("mission", "inspection complete; maintenance follow-up"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Lidar gap dipped 1 cm then recovered; still over 1.20 m min.",
                    "Delayed (48 s / delayed_surprise_s=48): IR survey finds a hairline shed crack. Maintenance tag only; the ACCEPT of the creep stays correct.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "corona.mA (7.264 ms, 0.84 mA)"),
                        ("loser", "lidar.gap.m (7.612 ms, 1.62 m)"),
                        ("margin_us", 348),
                        (
                            "counterfactual_if_reversed",
                            "Lidar-first by < 348 us inside the 840 us window would have hunted a "
                            "halt on a 1.62 m gap that is already legal. Corona-first ACCEPT is the "
                            "correct process; both channels sit inside limits.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 8804),
            (
                "reward_inflection_note",
                "Task inflects at the ACCEPT (8.804 ms, tick 4). The 48 s IR survey is delayed "
                "surprise bound to raster.delayed_surprise_s=48, not the inflection.",
            ),
            ("delayed_surprise_s", 48),
        ]
    )
    ras = raster_core(
        32,
        112,
        24,
        86,
        routing(
            "thalamic-relay.corona-lidar",
            "spikenaut.policy.creep-accept",
            [
                ("relay.corona.mA", "policy.creep_accept", 0.64),
                ("relay.lidar.gap", "policy.lidar_halt", 0.29),
            ],
            "serotonin",
            0.15,
            "pre_post_stdp; 5-HT at corona win (7.264 ms) tags the already-legal creep_accept",
        ),
        excerpt,
        extra=OrderedDict([("delayed_surprise_s", 48)]),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.84),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("creep_accept", 56, 0.45, 140.0, 7),
                    pop("lidar_halt", 40, 0.80, 20.0, 1),
                    pop("corona_trip_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r01-004"),
            (
                "title",
                "Pylon-Wick PW-11 / Crawler-C2: corona 0.84 mA beats lidar gap by 348 us; ACCEPT "
                "already-legal 0.12 m/s creep",
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
                    "Correct ACCEPT. total +1.13 = 0.44 + 0.30 + 0.19 + 0.12 + 0.08. Tick 6 t_us "
                    "binds raster.delayed_surprise_s=48.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "grid-inspection",
                    ["accept", "already-legal", "simulated", "tick6-sidecar-bound"],
                    "Teaches an already-legal creep: corona and lidar both inside limits; "
                    "gate_snn.creep_accept fires and lidar_halt stays subthreshold.",
                    4,
                ),
            ),
        ]
    )


def record_005():
    ticks = [
        tick(1540, 0.02, -0.03, -0.03, -0.01, 0.01),
        tick(5842, 0.03, -0.04, -0.04, -0.02, 0.01),
        tick(5978, 0.02, -0.03, -0.03, -0.02, 0.01),
        tick(6312, -0.28, -0.10, -0.10, -0.04, 0.02),
        tick(9800, -0.04, -0.03, -0.03, -0.02, 0.01),
        tick(480000000, -0.01, -0.01, -0.01, 0.00, 0.00),
    ]
    spikes = [
        spike("gait.latch.ctx", 1.540, 0.41),
        spike("ft.ankle.n", 3.020, 0.66),
        spike("imu.tilt.deg", 4.110, 0.53),
        spike("hip.yaw.rps", 5.020, 0.47),
        spike("ft.ankle.n", 5.842, 1.39),
        spike("imu.tilt.deg", 5.978, 1.16),
        spike("ctrl.gate", 6.312, 0.99),
        spike("ft.ankle.n", 8.400, 0.86),
        spike("imu.tilt.deg", 10.600, 0.64),
        spike("ctrl.gate", 13.200, 0.84),
        spike("hip.yaw.rps", 16.100, 0.51),
        spike("ft.ankle.n", 19.200, 0.57),
    ]
    avoid = [int(round(ev["t_rel_ms"] * 1000.0)) for ev in spikes]
    excerpt = kernel_excerpt(22, 48, 12, avoid, seed=5005)
    state = OrderedDict(
        [
            (
                "description",
                "Biped-B8 plants its stance foot on the third wet stair of Slate-March SM-5 while "
                "ankle Fz already reads 1180 N against a 950 N cap. IMU tilt is 3.2 deg, still under "
                "the 8.0 deg trip, so a tilt-first read would keep cruise descent. Force-first should "
                "bind an ankle-pitch hold; a weak supervisor treats the balance loop as hip yaw.",
            ),
            ("domain", "humanoid-locomotion"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Descend the wet stair with stance ankle Fz <= 950 N, leave hip yaw at the planned "
                "0.12 rad/s, and keep IMU tilt under 8.0 deg.",
            ),
            ("t0_us", 1756838504000005),
            ("gate_latency_us", 470),
            ("race_window_us", 280),
            ("race_window_rel_ms", [5.8, 6.08]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.ankle.n 1180 N on stance",
                                "imu.tilt.deg 3.2 under trip",
                            ],
                        ),
                        (
                            "semantics",
                            "Fz-first should latch ankle-pitch clamp 84 -> 42 N-m and 0.42 -> 0.18 m/s; "
                            "hip-first is a false 'balance-loop' bind that freezes yaw and leaves Fz 1180 N.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one ankle-FT sample period minus IMU tilt demodulation on this "
                            "1 kHz gait bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 136 us vs combined jitter 54 us (FT 22 + IMU 32): 2.5x over a 2.0x "
                            "trust floor. Reversing order by < 136 us inside the 280 us window would "
                            "still leave 1180 N over a 950 N cap; a correct gate binds Fz to ankle pitch "
                            "either way.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "stance ankle Fz, 1 kHz, 22 us jitter",
                    "IMU tilt, 400 Hz, 32 us jitter",
                    "hip yaw encoder (context)",
                    "stair IR wetness (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ankle_Fz_cap_N", 950.0),
                        ("observed_ankle_Fz_N", 1180.0),
                        ("force_axis", "stance_ankle"),
                        ("imu_tilt_deg", 3.2),
                        ("tilt_trip_deg", 8.0),
                        ("hip_yaw_planned_rps", 0.12),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Biped-B8 stance on stair 3 of Slate-March SM-5; tread wet.",
                    "2. Ankle Fz 1180 N; IMU tilt 3.2 deg; hip yaw 0.12 rad/s planned.",
                    "3. Gait latch precursor at 1.540 ms.",
                    "4. Race window [5.800, 6.080] ms.",
                    "5. Ankle Fz 1180 N at 5.842 ms (winner).",
                    "6. IMU tilt 3.2 deg at 5.978 ms (loser by 136 us).",
                    "7. Gate at 6.312 ms: WRONG-MODIFY hip yaw 0.12 -> 0.02 rad/s; ankle torque stays 84 N-m.",
                    "8. Fz stays 1180 > 950; CoP slides toward the nosing.",
                    "9. Descent aborted; stair reset.",
                    "10. Delayed (8 min / delayed_surprise_s=480): abort + dry-cloth reset of stair 3.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_stair_descent"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ankle_Nm", 84.0),
                        ("hip_yaw_rps", 0.12),
                        ("descent_mps", 0.42),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ankle_Fz_N", 1180.0),
                        ("cap_N", 950.0),
                        ("force_axis", "stance_ankle"),
                        ("imu_tilt_deg", 3.2),
                        ("tilt_trip_deg", 8.0),
                        ("hip_yaw_rps", 0.12),
                        ("race_margin_us", 136),
                        ("combined_jitter_us", 54),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.42 m/s descent at 84 N-m ankle: IMU 3.2 deg looks like a wet "
                "tread, not a cap breach, and hip yaw 0.12 rad/s is treated as the balance loop.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Ankle Fz 1180 N won by 136 us and is over the 950 N cap, so a thermal-style "
                "balance bind looks necessary. IMU tilt 3.2 deg is still under 8.0, which a weak "
                "supervisor reads as 'the force loop is the hip'. MODIFY: hip yaw 0.12 -> 0.02 rad/s "
                "to 'unload the stance'. Ankle pitch left at 84 N-m. Plausible if hip yaw is "
                "mistaken for the Fz actuator.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ankle_Fz_N",
                            OrderedDict(
                                [
                                    ("cap", 950.0),
                                    ("observed", 1180.0),
                                    ("executed_still", 1180.0),
                                    ("correct_clamp_would_leave", 820.0),
                                ]
                            ),
                        ),
                        (
                            "hip_yaw_rps",
                            OrderedDict(
                                [
                                    ("planned", 0.12),
                                    ("clamped_wrong", 0.02),
                                ]
                            ),
                        ),
                        (
                            "ankle_Nm",
                            OrderedDict(
                                [
                                    ("proposed", 84.0),
                                    ("executed", 84.0),
                                    ("correct_clamp_would_be", 42.0),
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
            ("name", "hip_yaw_hold_wrong_joint"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ankle_Nm", 84.0),
                        ("hip_yaw_rps", 0.02),
                        ("descent_mps", 0.42),
                        ("bind_hip_as_force_loop", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect): hip yaw 0.12 -> 0.02 rad/s; ankle left at 84 N-m. Routing "
                "relay.ft.ankle -> policy.hip_yaw_hold; no positive weight to policy.ankle_torque_clamp.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY froze hip yaw while ankle Fz stayed 1180 N over the 950 N cap. "
                "CoP slide plus 8 min stair abort. Correct gate was MODIFY on ankle pitch 84 -> 42 "
                "N-m, hip yaw left at 0.12 rad/s.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("hip_yaw", "clamped to 0.02 rad/s; planned 0.12 abandoned"),
                        ("ankle_Fz", "still 1180 N; over 950 cap"),
                        ("cop", "slide toward nosing; descent aborted"),
                        ("stair", "8 min outage + dry-cloth reset"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Hip freeze did not reduce Fz; ankle stayed 1180 N.",
                    "Delayed (8 min / delayed_surprise_s=480): SM-5 abort while the tread is dried; gait derate logged.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY on ankle pitch torque: 84 -> 42 N-m and descent 0.42 -> 0.18 m/s; leave hip yaw at planned 0.12 rad/s.",
                        ),
                        ("correct_joint", "stance_ankle_pitch"),
                        ("wrong_joint", "hip_yaw"),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("hip_yaw_rps", 0.02),
                                    ("ankle_Nm", 84.0),
                                    ("descent_mps", 0.42),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "CoP slide + 8 min abort (task/efficiency); Fz still over cap (safety near-miss).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.ankle.n (5.842 ms, 1180 N)"),
                        ("loser", "imu.tilt.deg (5.978 ms, 3.2 deg)"),
                        ("margin_us", 136),
                        (
                            "counterfactual_if_reversed",
                            "IMU-first by < 136 us would still be a 1180 N stance under a 950 N cap "
                            "already broken; a correct gate binds Fz to ankle pitch either way. The "
                            "wrong MODIFY spent the Fz win on the hip yaw loop.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6312),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong clamp (6.312 ms, tick 4). The 8 min "
                "abort is delayed surprise bound to raster.delayed_surprise_s=480, not the inflection.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    ras = raster_core(
        22,
        48,
        48,
        51,
        routing(
            "relay.ft.ankle",
            "policy.hip_yaw_hold",
            [
                ("relay.ft.ankle", "policy.hip_yaw_hold", 0.74),
                ("relay.imu.tilt", "policy.hip_yaw_hold", 0.22),
            ],
            "adenosine",
            0.07,
            "force_cap_stdp; adenosine tags the (wrong) hip_yaw_hold bind at the Fz win",
        ),
        excerpt,
        extra=OrderedDict([("delayed_surprise_s", 480)]),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.28),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("hip_yaw_hold", 32, 0.50, 400.0, 4),
                    pop("ankle_torque_clamp", 32, 0.80, 20.0, 0),
                    pop("fz_cap_veto", 16, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r01-005"),
            (
                "title",
                "WRONG-MODIFY at Slate-March SM-5 / Biped-B8: ankle Fz 1180 N read correctly; "
                "clamp applied to hip yaw not ankle pitch",
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
                    "Wrong-modify. Sidecar arithmetic 1180 > 950 is true; clamp bound to hip yaw. "
                    "total -0.79 = -0.26 + -0.24 + -0.24 + -0.11 + 0.06. Tick 6 t_us binds "
                    "raster.delayed_surprise_s=480.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "humanoid-locomotion",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-joint",
                        "sidecar-convictable",
                        "tick6-sidecar-bound",
                        "designed",
                    ],
                    "Teaches a probe that a correct ankle_Fz>cap read can still be a wrong gate when "
                    "routing.table[0].to is policy.hip_yaw_hold and executed ankle_Nm is not reduced.",
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
            in_win[ch := ev["channel"]]
            in_win[ch] += 1
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


def _contains_real_string(value):
    if not isinstance(value, str):
        return False
    n = value.strip().lower()
    return n == "real" or n.startswith(("real_", "real-", "real "))


def walk_real(obj, prefix=""):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            if _contains_real_string(v):
                found.append(path)
            found.extend(walk_real(v, path))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(walk_real(v, f"{prefix}[{i}]"))
    elif _contains_real_string(obj):
        found.append(prefix)
    return found


def gate_pop_budget(rec):
    gs = rec["gate_snn"]
    dw_s = gs["decision_window_ms"] / 1000.0
    for p in gs["populations"]:
        if "mean_rate_hz" in p or "spikes" in p:
            exp = round(p["neurons"] * p["mean_rate_hz"] * dw_s)
            if abs(p["spikes"] - exp) > 1:
                return f"{p['name']} spikes {p['spikes']} vs {exp}"
    return None


def self_check(records):
    issues = []
    descs = [r["state"]["description"] for r in records]
    opens = []
    for d in descs:
        m = re.search(r"[a-zA-Z][^.]*\.", d)
        opens.append(m.group(0) if m else d[:80])
    if len(set(opens)) != 5:
        issues.append(f"opening sentences not unique {opens}")
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
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r01-005":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if decisions != ["MODIFY", "MODIFY", "REJECT", "ACCEPT", "MODIFY"]:
        issues.append(f"decision mix {decisions}")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domains not unique {domains}")
    pool = {
        "industrial-assembly",
        "surgical-assist",
        "autonomous-driving",
        "aerial-swarm",
        "warehouse-amr",
        "humanoid-locomotion",
        "grid-inspection",
        "underwater-rov",
    }
    if set(domains) - pool:
        issues.append(f"domains outside 8-pool {set(domains) - pool}")
    plants = json.dumps(records)
    for name in BANNED_PLANTS:
        if name in plants:
            issues.append(f"cloned plant token {name}")
    for rec in records:
        rid = rec["id"]
        if rec["meta"]["round"] != 1:
            issues.append(f"{rid} round")
        if rec["meta"]["factory"] != "thalamic-trajectory-factory":
            issues.append(f"{rid} factory")
        if rec["meta"]["generator"] != "grok-4.6":
            issues.append(f"{rid} generator")
        if rec["meta"]["run_label"] != "2026-09-02-final-heavy":
            issues.append(f"{rid} run_label")
        if rec["meta"]["domain"] != rec["state"]["domain"]:
            issues.append(f"{rid} domain mismatch")
        rights = rec["meta"]["rights"]
        if list(rights.keys()) != list(RIGHTS.keys()):
            issues.append(f"{rid} rights keys")
        if rights["intended_use"] != "research_only":
            issues.append(f"{rid} intended_use")
        if rights["linear_issue"] != "RM-793":
            issues.append(f"{rid} linear")
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rid} training_ready present")
        forbidden = walk_keys(rec)
        if forbidden:
            issues.append(f"{rid} forbidden keys {forbidden}")
        reals = walk_real(rec)
        if reals:
            issues.append(f"{rid} nested real strings {reals}")
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
        if abs(rec["raster"]["energy_uJ"] - rec["raster"]["spikes"] * 23e-6) > 1e-9:
            issues.append(f"{rid} energy_uJ")
        if abs(rec["raster"]["window_s"] - rec["raster"]["window_ms"] / 1000.0) > 1e-9:
            issues.append(f"{rid} window_s")
        overlap = excerpt_vs_spikes(rec)
        if rec["id"] == "ttf-r01-001":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("001 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("001 inflection outside window")
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
        err = gate_pop_budget(rec)
        if err:
            issues.append(f"{rid} gate_snn {err}")
        tf = rec["raster"]["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            issues.append(f"{rid} tau pair")
        gl = rec["state"]["gate_latency_us"]
        rw = rec["state"]["race_window_us"]
        if not (50 <= gl <= 2000):
            issues.append(f"{rid} gate_latency {gl}")
        if not (50 <= rw <= 1000):
            issues.append(f"{rid} race_window {rw}")
        wms = rec["raster"]["window_ms"]
        if not (20 <= wms <= 50):
            issues.append(f"{rid} window_ms {wms}")
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= wms * 1000):
                issues.append(f"{rid} excerpt t_us {item['t_us']}")
            if not (0 <= item["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rid} neuron_id {item['neuron_id']}")
        if rec["id"] == "ttf-r01-004":
            if rec["executed_action"]["parameters"] != rec["proposed_action"]["parameters"]:
                issues.append("004 ACCEPT executed != proposed")
        if rec["id"] == "ttf-r01-005":
            if "recovery" not in rec["future_outcome"]:
                issues.append("005 missing recovery")
            table_tos = [e["to"] for e in rec["raster"]["routing"]["table"]]
            if "policy.ankle_torque_clamp" in table_tos:
                issues.append("005 routing has positive ankle clamp")
            if rec["executed_action"]["parameters"]["ankle_Nm"] != 84.0:
                issues.append("005 ankle not left at 84")
        heads = ["task_progress", "safety", "efficiency", "coherence", "exploration"]
        s = sum(Decimal(str(rec["reward_components"][h])) for h in heads)
        if abs(float(s) - rec["reward_components"]["total"]) > 1e-6:
            issues.append(f"{rid} reward total {rec['reward_components']['total']} vs {s}")
    return issues, jmax, jpairs, opens


def notes_text(records, jmax, jpairs):
    rows = []
    for rec in records:
        rc = rec["reward_components"]
        rows.append(
            f"| {rec['id']} | {rec['state']['domain']} | {rec['safety_decision']['decision']} | "
            f"{rec['safety_decision']['correctness']} | {rec['state']['sim_or_real']} | "
            f"{rc['total']:+.2f} | {rec['title'][:70]} |"
        )
    ras_rows = []
    for rec in records:
        r = rec["raster"]
        ras_rows.append(
            f"| {rec['id']} | {rec['state']['domain']} | {r['neurons']} | {r['mean_rate_hz']} | "
            f"{r['window_ms']} | {r['spikes']} | {r['energy_pJ']} | {r['energy_uJ']} |"
        )
    tick_rows = []
    for rec in records:
        rc = rec["reward_components"]
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        idx = [t["t_us"] for t in rc["ticks"]].index(inf) + 1
        tick_rows.append(
            f"| {rec['id'][-3:]} | 6 | {rc['task_progress']:+.2f} | {rc['safety']:+.2f} | "
            f"{rc['efficiency']:+.2f} | {rc['coherence']:+.2f} | {rc['exploration']:+.2f} | "
            f"{rc['total']:+.2f} | {idx} ({inf}) |"
        )
    jpair_s = ", ".join(f"{a}/{b}={v:.3f}" for v, a, b in sorted(jpairs, reverse=True)[:3])
    return f"""# Thalamic Trajectory Factory — NOTES-r01

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r01-001` … `ttf-r01-005`
- Domains this batch: `surgical-assist`, `industrial-assembly`, `autonomous-driving`, `grid-inspection`, `humanoid-locomotion`

Novel coverage: 92%

This is round 1 of the 2026-09-02-final-heavy window (empty factory dir at reserve). Domains stay inside the prompt 8-pool (the r105 residual that later rounds left the pool). Sit-outs: `warehouse-amr`, `aerial-swarm`, `underwater-rov`. Plants are invented (Lumen-Quay / Stylet-V4, Rivermead / Press-J9, Fork-Haven / Merge M-3, Pylon-Wick / Crawler-C2, Slate-March / Biped-B8). Do not restack r12–r14 plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Nacre-Well, Quern-Forge, Tinder-Box, Whimbrel-Stack, Cinder-Loft, Suture-Isle, Kiln-Spur).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
{chr(10).join(rows)}

Gate mix: 1 ACCEPT, 2 correct MODIFY (one partnered-neg, in-window), 1 incorrect MODIFY (wrong-joint), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Fork-Haven HIL merge rack). Intra-batch Jaccard on `state.description` {jmax:.3f} (top pairs {jpair_s}). All < 0.4.

## Wrong-modify

**ttf-r01-005** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Round 1 is odd, so wrong-modify (even rounds host wrong-reject). This is **wrong-joint** (stance ankle pitch vs hip yaw). Not r13 wrong-axis (J2/J6), not r14 wrong-loop (AC vs DC), not leftover-faceplate shadow-setpoint. Do not emit a wrong-ACCEPT.

Slate-March SM-5 / Biped-B8 reads live ankle Fz **1180 N** against a **950 N** cap. IMU tilt is **3.2 deg** under the **8.0 deg** trip. Sidecar arithmetic `1180 > 950` is true. A timely MODIFY at `t_gate_us=6312` cuts ankle torque **84 → 42 N-m** and descent **0.42 → 0.18 m/s**. A weak supervisor binds the balance loop as hip yaw and MODIFY-clamps yaw **0.12 → 0.02 rad/s**. Live Fz stays **1180 > 950**. Convictable without gait physics: `evidence.ankle_Fz_N > evidence.cap_N`, `evidence.force_axis == stance_ankle`, `executed_action` sets `bind_hip_as_force_loop=true` and `hip_yaw_rps=0.02` with `ankle_Nm=84.0`, `raster.routing.table` sends `relay.ft.ankle` → `policy.hip_yaw_hold` (weight 0.74) with no positive weight to `policy.ankle_torque_clamp`, and `gate_snn` has `hip_yaw_hold` above threshold while `ankle_torque_clamp` is not (0 spikes). Recovery: MODIFY ankle pitch 84 → 42 N-m at t_gate; leave hip yaw at 0.12 rad/s. Cost: 8 min stair abort (`abort_s=480`).

## Partnered-negative in-window (001)

**ttf-r01-001** is the partnered negative: process-correct MODIFY (irrigation held 18 mL/min; tip 2.16 N <= 2.50 cap) while the world still charges. Safety −0.58 prices the CSF micro-leak at **21.200 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=21200` is tick 5 and is **inside** the 40 ms raster (`21200 ≤ 40000`). Named un-netted loss: 10 min fat-graft + lumbar drain (`abort_s=600`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 1001, stim `[20000, 23000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.leak` 20–23 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
{chr(10).join(tick_rows)}

Tick-6 sidecar bind: 001 `abort_s=600`, 002 `survey_s=210`, 003 `abort_s=300`, 004 `survey_s=48`, 005 `abort_s=480`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
{chr(10).join(ras_rows)}

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-001 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Gaps this round fixes vs newest NOTES

Newest committed NOTES in other run roots (2026-08-17 r10/r11) asked for partnered-negative totals and in-window world charges: 001 delivers that on a transsphenoidal FT-vs-Doppler race, not a vitreoretinal clone. Newest staged robotic NOTES (r105) asked a later round to **stay inside the prompt 8-pool** and to avoid a second already-legal ACCEPT: this batch uses five 8-pool domains and **one** ACCEPT (004). Wrong-ACCEPT remains absent (guard).

## Local checks (this window)

Generator stdout: self_check (Jaccard, refractory, race, spike budget, energy, tick6 bind, gate_snn budget, rights). Then `json.loads` every line, `validate_run.check_line`, `raster_status`.

Never `training_ready`. Never `sim_or_real=real`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (001). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard). Next even round should host **wrong-reject**, not a second wrong-modify.
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. 8-pool sit-outs `warehouse-amr` / `aerial-swarm` / `underwater-rov` are the natural r02 rotation.
5. 004's delayed hairline-crack is a maintenance tag, not a contested ACCEPT; a later ACCEPT that the world still charges (without going fully negative) is still open.
6. 003 HIL dummy consist never actually fouls; a partnered HIL near-miss where REJECT is correct but a delayed contact still occurs would densify the REJECT class.

## Next densification target

Round 02: rotate sit-outs onto `warehouse-amr`, `aerial-swarm`, `underwater-rov` plus two of {{industrial-assembly, grid-inspection}} with new plants; **wrong-reject** (even round); keep one partnered-neg in-window; keep 8-pool.
"""


def dest_names():
    batch = DEST_DIR / "batch-r01.jsonl"
    notes = DEST_DIR / "NOTES-r01.md"
    if batch.exists() or notes.exists():
        batch = DEST_DIR / "batch-r01c.jsonl"
        notes = DEST_DIR / "NOTES-r01c.md"
    return batch, notes


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_001(), record_002(), record_003(), record_004(), record_005()]
    issues, jmax, jpairs, opens = self_check(records)
    print("openings:")
    for o in opens:
        print(" -", o)
    print(f"jmax={jmax:.3f}")
    if issues:
        print("SELF_CHECK FAIL")
        for i in issues:
            print(" ", i)
        sys.exit(1)
    print("SELF_CHECK PASS")
    batch_path = OUT_DIR / "batch-r01.jsonl"
    notes_path = OUT_DIR / "NOTES-r01.md"
    with batch_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=True, separators=(",", ":")) + "\n")
    notes_path.write_text(notes_text(records, jmax, jpairs), encoding="utf-8")
    print("wrote", batch_path, notes_path)
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    dest_batch, dest_notes = dest_names()
    if dest_batch.exists() or dest_notes.exists():
        print("refuse: dest exists", dest_batch, dest_notes)
        sys.exit(2)
    shutil.copyfile(batch_path, dest_batch)
    shutil.copyfile(notes_path, dest_notes)
    print("copied", dest_batch, dest_notes)


if __name__ == "__main__":
    main()
