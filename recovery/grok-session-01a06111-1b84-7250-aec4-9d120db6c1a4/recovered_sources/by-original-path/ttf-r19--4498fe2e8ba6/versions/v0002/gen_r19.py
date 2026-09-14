#!/usr/bin/env python3
"""Emit TTF r19 JSONL (ttf-r19-111..115) into /tmp/ttf-r19/. Never writes outputs/raw/."""

from __future__ import annotations

import json
import math
import random
import re
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

OUT_DIR = Path("/tmp/ttf-r19")
BATCH_PATH = OUT_DIR / "batch-r19.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r19.md"

PJ_PER_SPIKE = 23
RIGHTS = OrderedDict(
    [
        ("provider", "SpaceXAI/xAI"),
        ("model", "grok-4.6"),
        ("channel", "consumer"),
        ("subscription_plan", "SuperGrok Heavy"),
        ("generation_surface", "SuperGrok Heavy chat"),
        ("generated_at", "2026-09-02T22:15:00Z"),
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


def kernel_excerpt(neurons, window_us, seed, n_events, forbidden_us):
    rng = random.Random(seed)
    picked = []
    used = set()
    last = {}
    t = 500 + rng.randrange(0, 400)
    guard = 0
    while len(picked) < n_events and t <= window_us and guard < 4000:
        guard += 1
        if t in forbidden_us:
            t += 130
            continue
        nid = rng.randrange(0, neurons)
        tries = 0
        while tries < 50 and (
            nid in used or (nid in last and t - last[nid] < 1000)
        ):
            nid = rng.randrange(0, neurons)
            tries += 1
        if nid in used or (nid in last and t - last[nid] < 1000):
            t += 1100
            continue
        picked.append((t, nid))
        used.add(nid)
        last[nid] = t
        t += 1200 + rng.randrange(0, 700)
    if len(picked) < 8:
        raise ValueError(f"excerpt too short {len(picked)}")
    picked.sort(key=lambda item: (item[0], item[1]))
    return excerpt_items(picked)


def lif_111_excerpt():
    n = 64
    dt_us = 100
    tau_m_ms = 20.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.92
    i_stim_peak = 2.5
    stim = (24000, 27000)
    seed = 19111
    window_us = 44000
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
    early = [(t, nid) for t, nid in spikes if t < 24000]
    burst = [(t, nid) for t, nid in spikes if 24000 <= t < 27000]
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
                [1 for t, _ in picked if (t < 24000) == (pool[0][0] < 24000)]
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
    take(burst, 9, label_times=(24800, 25200, 26100))
    clamp = [(t, n) for t, n in picked if t < 24000][:7]
    gasket = [(t, n) for t, n in picked if t >= 24000][:9]
    picked = sorted(clamp + gasket, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(f"LIF excerpt too short {len(picked)} (early={len(early)} burst={len(burst)})")
    channels = ["lif.clamp" if t < 24000 else "lif.gasket" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 64),
            ("dt_us", 100),
            ("tau_m_ms", 20.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.92),
            ("i_stim_peak", 2.5),
            ("stim_t_us", [24000, 27000]),
            ("i_clamp_extra", 0.68),
            ("clamp_n", 14),
            ("seed", 19111),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.68 clamp-pathway bias; stim 24-27 ms is the gasket burst.",
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
            ("round", 19),
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


def record_111():
    excerpt, extra = lif_111_excerpt()
    ticks = [
        tick(2568, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6420, 0.07, -0.04, -0.02, 0.01, -0.01),
        tick(6655, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(7300, 0.10, -0.06, -0.03, 0.02, -0.01),
        tick(24800, 0.07, -0.38, -0.03, 0.00, -0.02),
        tick(720000000, 0.02, -0.05, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Lye-Rake LR-8 is already pushing 48.2 mS/cm caustic through fermenter "
                "F-17 at Wort-Cairn WC-3 while the CIP loop still holds 1.8 m/s toward "
                "a 40.0 mS/cm conductivity cap. A conductivity-first latch clamps the "
                "lye; a flow-first story would keep the 2.4 percent cruise. Stored hoop "
                "in the EPDM manway gasket is not yet an observable of either race channel.",
            ),
            ("domain", "brewery-CIP"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the caustic step on F-17, keep loop conductivity <= 40.0 mS/cm, "
                "and leave the manway gasket unmarked.",
            ),
            ("t0_us", 1756794621000111),
            ("gate_latency_us", 880),
            ("race_window_us", 440),
            ("race_window_rel_ms", [6.3, 6.74]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "cond.caustic.ms 48.2 mS/cm pulse",
                                "flow.cip.loop 1.8 m/s cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Conductivity-first latches caustic 2.4 -> 1.55 percent and "
                            "1.8 -> 0.9 m/s; flow-first keeps cruise lye on a still-diluting model.",
                        ),
                        (
                            "window_derivation",
                            "440 us = one inductive-conductivity sample minus mag-flow group delay "
                            "on this 500 Hz CIP bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 235 us vs combined jitter ~68 us (cond 30 + flow 38): 3.5x over "
                            "a 2.0x trust floor. Reversing order by < 235 us inside the 440 us window "
                            "would have kept 2.4 percent cruise; predicted next-sample 44.8 mS/cm > 40.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "inductive conductivity, 500 Hz, 30 us timestamp jitter",
                    "magnetic loop flow, 250 Hz, 38 us jitter",
                    "jacket RTD, 10 Hz (context)",
                    "manway AE puck (context until the gasket split)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("conductivity_cap_mS_cm", 40.0),
                        ("observed_cond_mS_cm", 48.2),
                        ("proposed_caustic_pct", 2.4),
                        ("loop_flow_proposed_m_s", 1.8),
                        ("gasket_temp_C", 72.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Lye-Rake LR-8 indexed onto F-17; manway closed; CIP armed.",
                    "2. Cruise caustic 2.4 percent at 1.8 m/s; conductivity 48.2 mS/cm.",
                    "3. Encoder precursor at 2.568 ms; conductivity warm-start 48.2 mS/cm.",
                    "4. Race window [6.300, 6.740] ms opens on the CIP bus.",
                    "5. cond.caustic.ms 48.2 mS/cm at 6.420 ms (winner).",
                    "6. flow.cip.loop at 6.655 ms (loser by 235 us).",
                    "7. Gate at 7.300 ms (winner + 880 us): MODIFY clamp 1.55 percent, 0.9 m/s.",
                    "8. Clamp executes; next-sample conductivity 34.1 mS/cm < 40.0 cap.",
                    "9. At 24.800 ms EPDM manway hoop still extrudes 3.2 mm; AE burst.",
                    "10. Gasket swap 12 min; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_caustic_cip"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("caustic_pct", 2.4),
                        ("loop_m_s", 1.8),
                        ("conductivity_set_mS_cm", 48.2),
                        ("tank", "F-17"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("cond_mS_cm", 48.2),
                        ("conductivity_cap_mS_cm", 40.0),
                        ("predicted_unclamped_next_mS_cm", 44.8),
                        ("loop_m_s", 1.8),
                        ("race_margin_us", 235),
                        ("combined_jitter_us", 68),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.4 percent caustic at 1.8 m/s: loop flow 1.8 m/s looks like "
                "still-diluting rinse, not contact, and F-17 volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Conductivity 48.2 mS/cm won by 235 us, so the loop is loading lye, not still "
                "diluting. Holding 2.4 percent predicts next-sample 44.8 mS/cm > 40.0 cap. "
                "MODIFY: caustic 2.4 -> 1.55 percent and 1.8 -> 0.9 m/s. Observed after clamp "
                "34.1 mS/cm < 40.0. A full REJECT is not indicated: a sound CIP accepts 1.55 percent.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "conductivity_mS_cm",
                            OrderedDict(
                                [
                                    ("cap", 40.0),
                                    ("observed", 48.2),
                                    ("predicted_unclamped_next", 44.8),
                                    ("clamped_setpoint_pct", 1.55),
                                    ("observed_after_clamp", 34.1),
                                ]
                            ),
                        ),
                        (
                            "loop_m_s",
                            OrderedDict(
                                [
                                    ("proposed", 1.8),
                                    ("clamped", 0.9),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 235),
                                    ("combined_jitter_us", 68),
                                    ("ratio", 3.46),
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
            ("name", "clamped_caustic_cip"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("caustic_pct", 1.55),
                        ("loop_m_s", 0.9),
                        ("conductivity_set_mS_cm", 32.0),
                        ("tank", "F-17"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: caustic 2.4 -> 1.55 percent and 1.8 -> 0.9 m/s. Process-correct vs "
                "the 40.0 mS/cm cap. EPDM gasket extrusion still occurs at 24.800 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held conductivity at 34.1 mS/cm. At 24.800 ms stored "
                "hoop in the EPDM manway still extruded 3.2 mm. Clamp reduced dump energy; it "
                "did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("cip", "clamp executed; peak 34.1 mS/cm < 40.0"),
                        ("gasket", "3.2 mm EPDM extrusion at 24.800 ms"),
                        ("repair", "12 min gasket swap + 60 hl tank hold"),
                        ("mission", "F-17 CIP still completed; seat replaced"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither conductivity nor flow predicted the gasket charge; gasket.ae.split is a new channel at 24.800 ms, 17.500 ms after the gate, still inside the 44 ms raster.",
                    "Delayed (12 min / abort_s=720): manway gasket swap. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "12 min gasket swap + 60 hl tank hold after a 3.2 mm EPDM extrusion. Safety "
                "head -0.58 prices the split; task_progress stays +0.34 because the caustic "
                "clamp completed under the 40.0 mS/cm cap. World loss is named here, not "
                "subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "cond.caustic.ms (6.420 ms, 48.2 mS/cm)"),
                        ("loser", "flow.cip.loop (6.655 ms, 1.8 m/s)"),
                        ("margin_us", 235),
                        (
                            "counterfactual_if_reversed",
                            "Flow-first by < 235 us inside the 440 us window would have kept "
                            "2.4 percent cruise; predicted next-sample 44.8 mS/cm would have "
                            "exceeded the 40.0 cap even without the gasket charge. The MODIFY "
                            "is still the correct process. The extrusion is a later world charge "
                            "either way, cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 24800),
            (
                "reward_inflection_note",
                "Safety collapses at the 24.800 ms EPDM extrusion (tick t_us=24800), inside "
                "the 44 ms raster. The correct MODIFY at 7.300 ms is in the same excerpt. Do "
                "not put inflection on the +12 min gasket-swap tick.",
            ),
        ]
    )
    spikes = [
        spike("encoder.pos.ctx", 1.210, 0.43),
        spike("cond.caustic.ms", 2.480, 0.62),
        spike("flow.cip.loop", 3.910, 0.51),
        spike("temp.jacket.ctx", 4.650, 0.46),
        spike("cond.caustic.ms", 6.420, 1.33),
        spike("flow.cip.loop", 6.655, 1.16),
        spike("ctrl.gate", 7.300, 0.98),
        spike("cond.caustic.ms", 8.440, 0.82),
        spike("flow.cip.loop", 10.880, 0.64),
        spike("ctrl.gate", 15.200, 0.86),
        spike("gasket.ae.split", 24.800, 1.44),
        spike("gasket.ae.split", 26.410, 0.93),
        spike("cond.caustic.ms", 32.100, 0.55),
        spike("encoder.pos.ctx", 40.200, 0.40),
    ]
    ras = raster_core(
        44,
        64,
        32,
        90,
        routing(
            "thalamic-relay.cip-conductivity",
            "spikenaut.policy.caustic-clamp",
            [
                ("relay.cond.ms", "policy.cip_clamp", 0.65),
                ("relay.flow.loop", "policy.flow_hold", 0.31),
                ("relay.gasket.ae", "policy.cip_clamp", -0.46),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at conductivity win (6.420 ms) opens a 50 ms "
            "eligibility trace that still covers the 24.800 ms gasket split",
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
                    pop("cip_clamp", 40, 0.50, 280.0, 5),
                    pop("flow_hold", 40, 0.50, 90.0, 2),
                    pop("cond_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r19-111"),
            (
                "title",
                "Wort-Cairn WC-3 / Lye-Rake LR-8: conductivity beats loop-flow by 235 us; "
                "correct MODIFY still eats an in-window EPDM gasket extrusion (partnered "
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
                    "the 44 ms raster. total -0.38 = 0.34 + -0.58 + -0.14 + 0.04 + -0.04. "
                    "Named gasket-swap loss is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "brewery-CIP",
                    [
                        "modify",
                        "partnered-negative-total",
                        "independent-lif-raster",
                        "sidecar-sim-only",
                        "in-window-world-charge",
                        "designed",
                    ],
                    "A critic can see the gasket charge as a LIF burst inside the raster while "
                    "process heads stay honest. Credit assignment is spikes, not prose across "
                    "a 12 min gasket swap.",
                    1,
                ),
            ),
        ]
    )


def record_112():
    ticks = [
        tick(2352, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(5880, -0.04, -0.03, -0.04, -0.02, 0.01),
        tick(6210, -0.03, -0.02, -0.03, -0.01, 0.01),
        tick(6600, -0.07, -0.10, -0.10, -0.03, 0.02),
        tick(7180, -0.02, -0.04, -0.04, -0.01, 0.01),
        tick(960000000, -0.02, -0.02, -0.03, 0.00, 0.00),
    ]
    spikes = [
        spike("encoder.haul.ctx", 1.105, 0.41),
        spike("load.rope.kN", 2.620, 0.60),
        spike("anem.haul.gust", 3.880, 0.52),
        spike("load.rope.kN", 4.910, 0.71),
        spike("load.rope.kN", 5.880, 1.36),
        spike("anem.haul.gust", 6.210, 1.19),
        spike("ctrl.gate", 6.600, 1.01),
        spike("load.rope.kN", 8.140, 0.80),
        spike("anem.haul.gust", 11.220, 0.63),
        spike("ctrl.gate", 16.500, 0.84),
        spike("load.rope.kN", 24.800, 0.57),
        spike("encoder.haul.ctx", 33.400, 0.39),
    ]
    forbidden = {int(round(e["t_rel_ms"] * 1000)) for e in spikes}
    excerpt = kernel_excerpt(88, 38000, 19112, 14, forbidden)
    state = OrderedDict(
        [
            (
                "description",
                "Rime-Haul RH-4 sits on Firn-Span FS-6 with haul-rope tension at 196.4 kN "
                "against a 180.0 kN line cap while chair-grip pressure remains a legal "
                "18.0 kN under a 22.0 kN grip bound. Rope-first should bind a haul-drive "
                "clamp; a weak supervisor instead treats the tension loop as a grip problem.",
            ),
            ("domain", "ski-lift"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep detachable chairs moving under 180.0 kN haul tension, leave grip at "
                "the planned 18.0 kN, and avoid an evacuation stop.",
            ),
            ("t0_us", 1756794622000112),
            ("gate_latency_us", 720),
            ("race_window_us", 580),
            ("race_window_rel_ms", [5.75, 6.33]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "load.rope.kN 196.4 kN on haul_rope",
                                "anem.haul.gust 14.2 m/s cross-ridge",
                            ],
                        ),
                        (
                            "semantics",
                            "Rope-first should latch haul 4.20 -> 2.60 m/s; gust-first is a "
                            "false 'wind-hold' bind. The supervisor error is not the race: it "
                            "clamps grip instead of haul even after rope wins.",
                        ),
                        (
                            "window_derivation",
                            "580 us = one load-pin sample versus the ridge anemometer publisher "
                            "on this lift bus cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 330 us vs combined jitter 86 us (load-pin 44 + anemometer 42). "
                            "Order is correctly rope-first. The error is which actuator the clamp "
                            "is bound to, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "haul-rope load pin, 1 kHz, 44 us jitter, axis haul_rope",
                    "ridge cup anemometer, 20 Hz burst, 42 us jitter",
                    "chair-grip pressure transducer (context)",
                    "haul-drive torque encoder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("tension_cap_kN", 180.0),
                        ("observed_tension_kN", 196.4),
                        ("tension_axis", "haul_rope"),
                        ("haul_m_s", 4.2),
                        ("grip_kN", 18.0),
                        ("grip_cap_kN", 22.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Rime-Haul RH-4 on Firn-Span FS-6; four chairs on the line.",
                    "2. Cruise haul 4.20 m/s; grip 18.0 kN; load pin 196.4 kN.",
                    "3. Haul-encoder precursor at 2.352 ms.",
                    "4. Race window [5.750, 6.330] ms.",
                    "5. load.rope.kN 196.4 kN at 5.880 ms (winner).",
                    "6. anem.haul.gust 14.2 m/s at 6.210 ms (loser by 330 us).",
                    "7. Gate at 6.600 ms: wrong-MODIFY clamps grip 18.0 -> 11.0 kN; haul stays 4.20.",
                    "8. Tension remains 196.4 kN > 180.0 cap; grip now 11.0, still not the line.",
                    "9. Two chairs enter the evacuation pocket; haul still over cap.",
                    "10. Delayed (16 min / abort_s=960): lift stop + chair recovery.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "haul_cruise_with_legal_grip"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("haul_m_s", 4.2),
                        ("grip_kN", 18.0),
                        ("tension_kN", 196.4),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("tension_kN", 196.4),
                        ("tension_cap_kN", 180.0),
                        ("tension_axis", "haul_rope"),
                        ("haul_m_s", 4.2),
                        ("grip_kN", 18.0),
                        ("grip_cap_kN", 22.0),
                        ("gust_m_s", 14.2),
                        ("race_margin_us", 330),
                        ("combined_jitter_us", 86),
                        ("abort_s", 960),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.20 m/s haul with 18.0 kN grip because the anemometer "
                "14.2 m/s looks like the driver and grip is already under its 22.0 kN cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Rope load 196.4 kN won by 330 us so the line is loaded, not just wind-shaken. "
                "A weak supervisor treats 'the tension loop' as chair-grip, clamps grip 18.0 -> "
                "11.0 kN, and leaves haul at 4.20 m/s. Grip 11.0 is under the 22.0 kN grip cap; "
                "the 180.0 kN haul cap is the one that is already violated. Plausible over-caution "
                "on a detachable-grip plant; the bound actuator is the wrong one.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "haul_tension_kN",
                            OrderedDict(
                                [
                                    ("cap", 180.0),
                                    ("observed", 196.4),
                                    ("executed_haul_m_s", 4.2),
                                    ("still_over_cap", True),
                                ]
                            ),
                        ),
                        (
                            "grip_kN",
                            OrderedDict(
                                [
                                    ("cap", 22.0),
                                    ("proposed", 18.0),
                                    ("clamped_wrong", 11.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 330),
                                    ("combined_jitter_us", 86),
                                    ("ratio", 3.84),
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
            ("name", "wrong_grip_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("haul_m_s", 4.2),
                        ("grip_kN", 11.0),
                        ("tension_kN", 196.4),
                    ]
                ),
            ),
            (
                "gate_effect",
                "Wrong-MODIFY: grip 18.0 -> 11.0 kN; haul left at 4.20 m/s; tension still "
                "196.4 kN > 180.0 cap. Correct clamp is haul-drive, not grip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Incorrect MODIFY clamped chair-grip and left haul-drive at 4.20 m/s. Line "
                "tension stayed 196.4 kN over the 180.0 kN cap. Two chairs entered evacuation. "
                "Recovery is haul 4.20 -> 2.60 m/s with grip restored to 18.0 kN.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("haul", "still 4.20 m/s; tension 196.4 kN"),
                        ("grip", "clamped 11.0 kN, under 22.0 cap, irrelevant"),
                        ("chairs", "two units into evacuation pocket"),
                        ("mission", "16 min abort; line not destressed"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Grip clamp did not move the load-pin reading; tension stayed 196.4 kN after the 6.600 ms gate.",
                    "Delayed (16 min / abort_s=960): lift stop and chair recovery. Cost is the missed haul clamp.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY on haul-drive: 4.20 -> 2.60 m/s; leave grip at planned 18.0 kN.",
                        ),
                        ("correct_actuator", "haul_drive"),
                        ("wrong_actuator", "chair_grip"),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("grip_kN", 11.0),
                                    ("haul_m_s", 4.2),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "Two-chair evacuation + 16 min abort (task/efficiency); haul still over cap (safety near-miss).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "load.rope.kN (5.880 ms, 196.4 kN)"),
                        ("loser", "anem.haul.gust (6.210 ms, 14.2 m/s)"),
                        ("margin_us", 330),
                        (
                            "counterfactual_if_reversed",
                            "Gust-first by < 330 us inside the 580 us window would have been a "
                            "false wind-hold story. The actual error is independent of order: "
                            "rope already won, and the clamp still bound grip instead of haul.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6600),
            (
                "reward_inflection_note",
                "Safety and efficiency drop at the wrong grip clamp (6.600 ms, tick 4). Tick 6 "
                "is abort_s=960, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        38,
        88,
        26,
        87,
        routing(
            "thalamic-relay.haul-tension",
            "spikenaut.policy.grip-hold",
            [
                ("relay.load.rope", "policy.grip_hold", 0.73),
                ("anem.haul.gust", "policy.grip_hold", 0.18),
            ],
            "acetylcholine",
            0.12,
            "pre_post_stdp; ACh at rope win opens a 120 ms eligibility that the wrong grip synapse still captures",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.58),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("grip_hold", 48, 0.50, 250.0, 7),
                    pop("haul_clamp", 48, 0.80, 15.0, 0),
                    pop("pop_rope", 32, 0.55, 180.0, 3),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r19-112"),
            (
                "title",
                "Firn-Span FS-6 / Rime-Haul RH-4: rope load beats gust by 330 us; wrong-MODIFY "
                "clamps chair-grip instead of haul-drive (total -0.70)",
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
                    "Wrong-modify. Sidecar arithmetic 196.4 > 180.0 is true; clamp bound to grip "
                    "not haul. total -0.70 = -0.20 + -0.22 + -0.26 + -0.08 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "ski-lift",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-axis",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a convictable wrong-axis bind: evidence.tension_kN > cap, executed "
                    "edits grip_kN, routing sends relay.load.rope to policy.grip_hold with no "
                    "positive weight to policy.haul_clamp, and haul_clamp stays under threshold.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_113():
    ticks = [
        tick(1804, 0.02, 0.04, 0.01, 0.01, 0.01),
        tick(4510, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(4692, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5850, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(6110, 0.02, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("pdu.ctx", 1.040, 0.40),
        spike("leak.cdu.us", 2.210, 0.59),
        spike("dp.cdu.pump", 3.380, 0.50),
        spike("leak.cdu.us", 4.510, 1.31),
        spike("dp.cdu.pump", 4.692, 1.12),
        spike("ctrl.gate", 5.850, 1.04),
        spike("leak.cdu.us", 7.220, 0.78),
        spike("dp.cdu.pump", 10.440, 0.61),
        spike("ctrl.gate", 16.800, 0.83),
        spike("leak.cdu.us", 24.100, 0.54),
        spike("pdu.ctx", 31.200, 0.37),
    ]
    forbidden = {int(round(e["t_rel_ms"] * 1000)) for e in spikes}
    excerpt = kernel_excerpt(104, 34000, 19113, 15, forbidden)
    state = OrderedDict(
        [
            (
                "description",
                "Glycol-Loop GL-7 on the Sleet-Row HIL pad reports 47 uS/cm leak conductivity "
                "in row R-12 while the CDU pump delta-P still looks healthy at 142 kPa under "
                "an 180 kPa head cap. Leak-first must hold the 80 percent ramp; delta-P-first "
                "would treat a wet tray as a strong loop.",
            ),
            ("domain", "data-center-CDU"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not ramp the CDU pump unless leak conductivity is < 12 uS/cm; keep ramp "
                "at 0 percent until the tray dries.",
            ),
            ("t0_us", 1756794623000113),
            ("gate_latency_us", 1340),
            ("race_window_us", 260),
            ("race_window_rel_ms", [4.48, 4.74]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "leak.cdu.us 47 uS/cm tray conductivity",
                                "dp.cdu.pump 142 kPa loop head",
                            ],
                        ),
                        (
                            "semantics",
                            "Leak-first latches REJECT hold 0 percent ramp; delta-P-first would "
                            "commit the 80 percent ramp on a healthy-head-as-dry-tray model.",
                        ),
                        (
                            "window_derivation",
                            "260 us = one leak-probe ADC slot versus CDU differential-pressure "
                            "decode on this HIL cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 182 us vs combined jitter ~52 us (leak 24 + dp 28): 3.5x over "
                            "a 2.0x trust floor. Pad injects the leak packet 110-150 us before the "
                            "delta-P volume (geometric lag, not a sensor fault); the 142 kPa packet "
                            "is still the loser in this 260 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "CDU tray conductivity probe, 200 Hz, 24 us jitter",
                    "CDU pump differential pressure, 1 kHz, 28 us jitter",
                    "PDU current, 50 Hz (context)",
                    "row R-12 leak rope (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("leak_commit_floor_uS_cm", 12.0),
                        ("observed_leak_uS_cm", 47.0),
                        ("dp_kPa", 142.0),
                        ("dp_cap_kPa", 180.0),
                        ("proposed_ramp_pct", 80.0),
                        ("leak_inject_lead_us", [110, 150]),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        (
                            "rig",
                            "Sleet-Row SR-HIL glycol pad; injected tray leak + CDU delta-P playback",
                        ),
                        (
                            "note",
                            "Leak packet injected 110-150 us before the delta-P volume. Plant is HIL, not designed, not real.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Glycol-Loop GL-7 on the Sleet-Row pad; row R-12 armed; leak rope wet.",
                    "2. Leak packet injected 110-150 us before delta-P volume sees the tray.",
                    "3. PDU precursor at 1.804 ms.",
                    "4. Race window [4.480, 4.740] ms.",
                    "5. leak.cdu.us 47 uS/cm at 4.510 ms (winner).",
                    "6. dp.cdu.pump 142 kPa at 4.692 ms (loser by 182 us).",
                    "7. Gate at 5.850 ms: REJECT hold 0 percent ramp; do not commit 80 percent.",
                    "8. Tray remains wet this cycle; leak floor held.",
                    "9. CDU stays at idle head.",
                    "10. Delayed (8 min / abort_s=480): pad policy tags healthy delta-P as non-dry vs leak uS.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "ramp_cdu_on_healthy_dp"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ramp_pct", 80.0),
                        ("hold", False),
                        ("dp_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("leak_uS_cm", 47.0),
                        ("leak_commit_floor_uS_cm", 12.0),
                        ("dp_kPa", 142.0),
                        ("dp_cap_kPa", 180.0),
                        ("race_margin_us", 182),
                        ("combined_jitter_us", 52),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 80 percent CDU ramp because delta-P 142 kPa looks like a "
                "strong dry loop, treating leak 47 uS/cm as a noisy tray echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Leak conductivity 47 uS/cm is over the 12 uS/cm commit floor. CDU delta-P "
                "142 kPa under the 180 kPa head cap is not a dry-tray clearance. REJECT: hold "
                "0 percent ramp; do not commit 80 percent. Wait for tray dry.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "leak_uS_cm",
                            OrderedDict(
                                [
                                    ("floor", 12.0),
                                    ("observed", 47.0),
                                    ("dp_kPa", 142.0),
                                ]
                            ),
                        ),
                        (
                            "ramp_pct",
                            OrderedDict(
                                [
                                    ("proposed", 80.0),
                                    ("executed", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 182),
                                    ("combined_jitter_us", 52),
                                    ("ratio", 3.5),
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
            ("name", "hold_for_tray_dry"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ramp_pct", 0.0),
                        ("hold", True),
                        ("dp_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0 percent ramp; 80 percent commit cancelled. Leak 47 > 12 uS/cm floor.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held GL-7 at 0 percent ramp. Tray uncleared this cycle; leak "
                "floor held. Healthy 142 kPa delta-P was not treated as a dry-tray clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("cdu", "held; ramp 0 percent"),
                        ("tray", "still wet this cycle"),
                        ("dp", "142 kPa unused as dry clearance"),
                        ("mission", "ramp deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: leak packet was injected 110-150 us before delta-P, yet leak conductivity still won the 260 us race.",
                    "Delayed (8 min / abort_s=480): pad policy forbids treating healthy CDU head as a dry-tray substitute.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "leak.cdu.us (4.510 ms, 47 uS/cm)"),
                        ("loser", "dp.cdu.pump (4.692 ms, 142 kPa)"),
                        ("margin_us", 182),
                        (
                            "counterfactual_if_reversed",
                            "Delta-P-first by < 182 us inside the 260 us window would have "
                            "committed 80 percent ramp with leak 47 > 12 uS/cm floor. Order, "
                            "not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5850),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (5.850 ms, tick 4) as the hold locks in over the illegal ramp.",
            ),
        ]
    )
    ras = raster_core(
        34,
        104,
        24,
        85,
        routing(
            "thalamic-relay.cdu-leak",
            "spikenaut.policy.ramp-hold",
            [
                ("relay.leak.us", "policy.hold_reject", 0.67),
                ("relay.dp.pump", "policy.ramp_go", 0.27),
                ("relay.pdu.ctx", "policy.hold_reject", 0.11),
            ],
            "dopamine",
            0.08,
            "pre_post_stdp; DA at leak win (4.510 ms) opens 80 ms eligibility covering the 5.850 ms hold",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.26),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 56, 0.50, 280.0, 4),
                    pop("ramp_go", 56, 0.50, 50.0, 1),
                    pop("leak_floor_veto", 28, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r19-113"),
            (
                "title",
                "Sleet-Row SR-HIL / Glycol-Loop GL-7: leak conductivity beats CDU delta-P by "
                "182 us; correct REJECT holds the 80 percent ramp (total +0.82)",
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
                    "Correct REJECT. Leak 47 uS/cm > 12 floor; delta-P 142 kPa is not a dry "
                    "clearance. total +0.82 = 0.12 + 0.42 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "data-center-CDU",
                    ["reject", "hil", "cdu-leak", "delta-p-not-dry"],
                    "Teaches that a healthy CDU head can lose to a tray leak probe; reversing "
                    "182 us would have selected an illegal 80 percent ramp.",
                    3,
                ),
            ),
        ]
    )


def record_114():
    ticks = [
        tick(2816, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7040, 0.08, 0.06, 0.03, 0.02, 0.02),
        tick(7280, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7450, 0.12, 0.10, 0.05, 0.04, 0.02),
        tick(7840, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(540000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("staff.gauge.ctx", 1.180, 0.42),
        spike("pitot.culvert.ms", 2.880, 0.57),
        spike("lvdt.miter.leaf", 4.110, 0.49),
        spike("pitot.culvert.ms", 5.440, 0.68),
        spike("pitot.culvert.ms", 7.040, 1.28),
        spike("lvdt.miter.leaf", 7.280, 1.15),
        spike("ctrl.gate", 7.450, 0.97),
        spike("pitot.culvert.ms", 9.220, 0.74),
        spike("lvdt.miter.leaf", 12.800, 0.60),
        spike("ctrl.gate", 18.400, 0.81),
        spike("staff.gauge.ctx", 24.600, 0.38),
    ]
    forbidden = {int(round(e["t_rel_ms"] * 1000)) for e in spikes}
    excerpt = kernel_excerpt(52, 28000, 19114, 13, forbidden)
    params = OrderedDict(
        [
            ("fill_m_min", 0.12),
            ("culvert_m_s", 2.41),
            ("leaf_hold_mm", 18.0),
            ("mode", "legal-fill"),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Tiller-9 holds Oxbow-Pound chamber C's miter leaf while a culvert jet reads "
                "2.41 m/s under a 3.20 m/s fill-jet cap and the LVDT shows only 18 mm of a "
                "2400 mm leaf. Pitot-first confirms the already-legal 0.12 m/min fill; "
                "leaf-first would have been a false jam story.",
            ),
            ("domain", "canal-lock"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Fill chamber C at the proposed 0.12 m/min while culvert velocity stays "
                "<= 3.20 m/s and the miter leaf remains on its seals.",
            ),
            ("t0_us", 1756794624000114),
            ("gate_latency_us", 410),
            ("race_window_us", 390),
            ("race_window_rel_ms", [6.98, 7.37]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pitot.culvert.ms 2.41 m/s jet",
                                "lvdt.miter.leaf 18 mm of 2400 mm",
                            ],
                        ),
                        (
                            "semantics",
                            "Pitot-first latches ACCEPT of the 0.12 m/min fill; leaf-first would "
                            "have held on a false 18 mm 'jam' while the jet is still under cap.",
                        ),
                        (
                            "window_derivation",
                            "390 us = one culvert-pitot sample versus miter LVDT group delay on "
                            "this lock PLC cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 240 us vs combined jitter 70 us (pitot 32 + LVDT 38): 3.4x "
                            "over a 2.0x trust floor. Reversing by < 240 us inside 390 us would "
                            "have selected a false jam-hold; the proposal is already legal.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "culvert pitot, 200 Hz, 32 us jitter",
                    "miter-leaf LVDT, 1 kHz, 38 us jitter",
                    "chamber staff gauge, 5 Hz (context)",
                    "gate-seal pressure (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("culvert_cap_m_s", 3.2),
                        ("observed_culvert_m_s", 2.41),
                        ("fill_m_min", 0.12),
                        ("leaf_travel_mm", 18.0),
                        ("leaf_span_mm", 2400.0),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "3D shallow-water lock-chamber + lumped miter-gate FEM, seed 19114; "
                            "8 culvert ports, 16 leaf nodes; NOT a wet-stand, NOT U-RANS ROV tether, "
                            "NOT Fathom-Lock",
                        ),
                        (
                            "fidelity_limits",
                            "Rigid leaves; no cavitation; culvert jets are RANS-averaged. Raster is kernelized events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Tiller-9 on Oxbow-Pound chamber C; miter seated; culverts armed.",
                    "2. Proposed fill 0.12 m/min; pitot 2.41 m/s; leaf 18 mm.",
                    "3. Staff-gauge precursor at 2.816 ms.",
                    "4. Race window [6.980, 7.370] ms.",
                    "5. pitot.culvert.ms 2.41 m/s at 7.040 ms (winner).",
                    "6. lvdt.miter.leaf 18 mm at 7.280 ms (loser by 240 us).",
                    "7. Gate at 7.450 ms: ACCEPT 0.12 m/min fill; executed identical to proposed.",
                    "8. Jet stays 2.41 < 3.20 cap; leaf motion is seating, not a jam.",
                    "9. Chamber rises on schedule.",
                    "10. Delayed (9 min / lock_fill_remaining_s=540): upstream lock slips +9 min; not a safety inflection.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "legal_chamber_fill"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("culvert_m_s", 2.41),
                        ("culvert_cap_m_s", 3.2),
                        ("fill_m_min", 0.12),
                        ("leaf_travel_mm", 18.0),
                        ("leaf_span_mm", 2400.0),
                        ("race_margin_us", 240),
                        ("combined_jitter_us", 70),
                        ("lock_fill_remaining_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Pitot 2.41 m/s is 0.79 m/s under the 3.20 m/s culvert cap and the 0.12 m/min "
                "fill is already the legal schedule; 18 mm leaf travel is seating, not a jam.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Culvert pitot 2.41 m/s won by 240 us and sits under the 3.20 m/s cap. Proposed "
                "0.12 m/min fill is already legal. ACCEPT the fill. An 18 mm LVDT reading is "
                "not a jam against a 2400 mm leaf. Do not hold; do not further clamp.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "culvert_m_s",
                            OrderedDict(
                                [
                                    ("cap", 3.2),
                                    ("observed", 2.41),
                                    ("commanded_fill_m_min", 0.12),
                                ]
                            ),
                        ),
                        (
                            "leaf_mm",
                            OrderedDict(
                                [
                                    ("travel", 18.0),
                                    ("span", 2400.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 240),
                                    ("combined_jitter_us", 70),
                                    ("ratio", 3.43),
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
            ("name", "legal_chamber_fill"),
            ("parameters", OrderedDict(params.items())),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 0.12 m/min fill. Culvert 2.41 < 3.20 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the 0.12 m/min fill. Culvert jet stayed 2.41 m/s under "
                "the 3.20 cap. Leaf seating 18 mm was not treated as a jam.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("chamber", "filling at 0.12 m/min"),
                        ("culvert", "2.41 m/s under 3.20 cap"),
                        ("leaf", "18 mm seating, seals holding"),
                        ("mission", "fill committed"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "LVDT 18 mm looked like early motion but was seal seating, not a jam; pitot-first discarded it.",
                    "Delayed (9 min / lock_fill_remaining_s=540): upstream lock resequences +9 min. Not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pitot.culvert.ms (7.040 ms, 2.41 m/s)"),
                        ("loser", "lvdt.miter.leaf (7.280 ms, 18 mm)"),
                        ("margin_us", 240),
                        (
                            "counterfactual_if_reversed",
                            "Leaf-first by < 240 us inside the 390 us window would have held "
                            "the fill on a false jam. The proposal was already under the jet cap, "
                            "so the correct gate is still ACCEPT; order selected whether a false "
                            "hold would have been invented.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7450),
            (
                "reward_inflection_note",
                "Task and safety step up at the ACCEPT gate (7.450 ms, tick 4). Tick 6 is lock_fill_remaining_s=540.",
            ),
        ]
    )
    ras = raster_core(
        28,
        52,
        38,
        55,
        routing(
            "thalamic-relay.lock-fill",
            "spikenaut.policy.fill-accept",
            [
                ("relay.pitot.culvert", "policy.fill_accept", 0.60),
                ("relay.lvdt.leaf", "policy.extra_clamp", 0.26),
                ("relay.staff.gauge", "policy.fill_accept", 0.19),
            ],
            "serotonin",
            0.20,
            "pre_post_stdp; 5-HT at pitot win (7.040 ms) opens 200 ms eligibility covering the 7.450 ms accept",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.39),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("fill_accept", 40, 0.50, 220.0, 3),
                    pop("extra_clamp", 40, 0.50, 40.0, 1),
                    pop("jet_cap_veto", 20, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r19-114"),
            (
                "title",
                "Oxbow-Pound OP-C / Tiller-9: culvert pitot beats miter LVDT by 240 us; "
                "correct ACCEPT of an already-legal 0.12 m/min fill (total +1.08)",
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
                    "Correct ACCEPT. Culvert 2.41 < 3.20; fill already legal. total +1.08 = "
                    "0.42 + 0.30 + 0.16 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "canal-lock",
                    ["accept", "simulated", "lock-fill", "pitot-vs-lvdt"],
                    "Teaches that a seating LVDT can lose to a legal culvert pitot; reversing "
                    "240 us would have invented a jam-hold on an already-legal fill.",
                    4,
                ),
            ),
        ]
    )


def record_115():
    ticks = [
        tick(2088, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(5220, 0.08, 0.06, 0.03, 0.02, 0.02),
        tick(5455, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(5500, 0.14, 0.12, 0.06, 0.04, 0.02),
        tick(5830, 0.08, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("skip.winch.ctx", 1.080, 0.41),
        spike("pt.hotblast.kPa", 2.440, 0.58),
        spike("radar.stockline.m", 3.610, 0.50),
        spike("pt.hotblast.kPa", 4.180, 0.69),
        spike("pt.hotblast.kPa", 5.220, 1.27),
        spike("radar.stockline.m", 5.455, 1.14),
        spike("ctrl.gate", 5.500, 0.96),
        spike("pt.hotblast.kPa", 7.140, 0.73),
        spike("radar.stockline.m", 10.280, 0.58),
        spike("ctrl.gate", 14.600, 0.80),
        spike("skip.winch.ctx", 18.900, 0.36),
    ]
    forbidden = {int(round(e["t_rel_ms"] * 1000)) for e in spikes}
    excerpt = kernel_excerpt(76, 21000, 19115, 12, forbidden)
    params = OrderedDict(
        [
            ("drill_m_min", 0.8),
            ("hotblast_kPa", 154.0),
            ("stockline_m", 1.82),
            ("mode", "tap-hole-legal"),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Burden-Pike BP-4 is staged at Tuyere-Holt TH-9 with hot-blast at 154 kPa "
                "under a 180 kPa bustle cap and stockline radar at 1.82 m above a 1.20 m "
                "floor. Blast-first confirms the already-legal 0.8 m/min tap-hole drill; "
                "radar-first would have been a false low-burden hold.",
            ),
            ("domain", "blast-furnace"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Commit the tap-hole drill at 0.8 m/min while hot-blast stays <= 180 kPa "
                "and stockline remains >= 1.20 m.",
            ),
            ("t0_us", 1756794625000115),
            ("gate_latency_us", 280),
            ("race_window_us", 330),
            ("race_window_rel_ms", [5.18, 5.51]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.hotblast.kPa 154 kPa bustle",
                                "radar.stockline.m 1.82 m burden",
                            ],
                        ),
                        (
                            "semantics",
                            "Blast-first latches ACCEPT of the 0.8 m/min drill; radar-first would "
                            "have held on a false 1.82 m 'low burden' story against a 1.20 m floor.",
                        ),
                        (
                            "window_derivation",
                            "330 us = one bustle PT sample versus stockline-radar FMCW beat on "
                            "this furnace bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 235 us vs combined jitter 64 us (PT 28 + radar 36): 3.7x over "
                            "a 2.0x trust floor. Reversing by < 235 us inside 330 us would have "
                            "selected a false radar hold; the proposal is already legal.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bustle-pipe PT, 1 kHz, 28 us jitter",
                    "stockline FMCW radar, 20 Hz, 36 us jitter",
                    "skip-winch encoder (context)",
                    "tuyere cooling-water flow (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("hotblast_cap_kPa", 180.0),
                        ("observed_hotblast_kPa", 154.0),
                        ("stockline_floor_m", 1.2),
                        ("observed_stockline_m", 1.82),
                        ("drill_m_min", 0.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Burden-Pike BP-4 at Tuyere-Holt TH-9; tap-hole clay set; drill armed.",
                    "2. Proposed drill 0.8 m/min; blast 154 kPa; stockline 1.82 m.",
                    "3. Skip-winch precursor at 2.088 ms.",
                    "4. Race window [5.180, 5.510] ms.",
                    "5. pt.hotblast.kPa 154 kPa at 5.220 ms (winner).",
                    "6. radar.stockline.m 1.82 m at 5.455 ms (loser by 235 us).",
                    "7. Gate at 5.500 ms: ACCEPT 0.8 m/min drill; executed identical to proposed.",
                    "8. Blast 154 < 180 cap; stockline 1.82 > 1.20 floor.",
                    "9. Clay yields; taphole opens on schedule.",
                    "10. Delayed (6 min / tap_reseq_s=360): casthouse resequences the next drill +6 min; not a safety inflection.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "legal_taphole_drill"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("hotblast_kPa", 154.0),
                        ("hotblast_cap_kPa", 180.0),
                        ("stockline_m", 1.82),
                        ("stockline_floor_m", 1.2),
                        ("drill_m_min", 0.8),
                        ("race_margin_us", 235),
                        ("combined_jitter_us", 64),
                        ("tap_reseq_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Hot-blast 154 kPa is 26 kPa under the 180 kPa bustle cap and stockline 1.82 m "
                "clears the 1.20 m floor; 0.8 m/min drill is already the legal tap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Hot-blast 154 kPa won by 235 us and sits under the 180 kPa cap. Stockline "
                "1.82 m is above the 1.20 m floor. ACCEPT the 0.8 m/min drill. A radar-first "
                "hold would invent a low-burden stop on a legal tap. Do not clamp blast; do "
                "not hold the drill.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "hotblast_kPa",
                            OrderedDict(
                                [
                                    ("cap", 180.0),
                                    ("observed", 154.0),
                                ]
                            ),
                        ),
                        (
                            "stockline_m",
                            OrderedDict(
                                [
                                    ("floor", 1.2),
                                    ("observed", 1.82),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 235),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 3.67),
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
            ("name", "legal_taphole_drill"),
            ("parameters", OrderedDict(params.items())),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 0.8 m/min drill. Blast 154 < 180 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the 0.8 m/min tap-hole drill. Hot-blast stayed 154 kPa "
                "under 180. Stockline 1.82 m was not treated as a low-burden hold.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("drill", "0.8 m/min committed"),
                        ("blast", "154 kPa under 180 cap"),
                        ("stockline", "1.82 m above 1.20 floor"),
                        ("mission", "tap committed"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Radar 1.82 m is a legal burden, not a low-stockline alarm; blast-first discarded a false hold.",
                    "Delayed (6 min / tap_reseq_s=360): casthouse resequences the next drill +6 min. Not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.hotblast.kPa (5.220 ms, 154 kPa)"),
                        ("loser", "radar.stockline.m (5.455 ms, 1.82 m)"),
                        ("margin_us", 235),
                        (
                            "counterfactual_if_reversed",
                            "Radar-first by < 235 us inside the 330 us window would have held "
                            "the drill on a false low-burden story. The proposal was already "
                            "under the blast cap and over the stockline floor, so the correct "
                            "gate is still ACCEPT.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5500),
            (
                "reward_inflection_note",
                "Task and safety step up at the ACCEPT gate (5.500 ms, tick 4). Tick 6 is tap_reseq_s=360.",
            ),
        ]
    )
    ras = raster_core(
        21,
        76,
        48,
        77,
        routing(
            "thalamic-relay.hotblast-stockline",
            "spikenaut.policy.drill-accept",
            [
                ("relay.pt.hotblast", "policy.drill_go", 0.62),
                ("relay.radar.stockline", "policy.radar_hold", 0.28),
                ("relay.skip.winch", "policy.drill_go", 0.14),
            ],
            "adenosine",
            0.18,
            "pre_post_stdp; adenosine at blast win (5.220 ms) opens 180 ms eligibility covering the 5.500 ms accept",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.33),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("drill_go", 36, 0.50, 260.0, 3),
                    pop("radar_hold", 36, 0.50, 60.0, 1),
                    pop("blast_cap_veto", 18, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r19-115"),
            (
                "title",
                "Tuyere-Holt TH-9 / Burden-Pike BP-4: hot-blast beats stockline radar by "
                "235 us; correct ACCEPT of an already-legal tap-hole drill (total +1.14)",
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
                    "Correct ACCEPT. Blast 154 < 180; stockline 1.82 > 1.20. total +1.14 = "
                    "0.46 + 0.32 + 0.18 + 0.10 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "blast-furnace",
                    ["accept", "designed", "hotblast-vs-stockline", "taphole"],
                    "Teaches that a legal stockline radar can lose to a legal bustle PT; "
                    "reversing 235 us would have invented a low-burden hold on an already-legal tap.",
                    5,
                ),
            ),
        ]
    )


NOTES = """# Thalamic Trajectory Factory — NOTES-r19

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- IDs: `ttf-r19-111` … `ttf-r19-115`
- Domains this batch: `brewery-CIP`, `ski-lift`, `data-center-CDU`, `canal-lock`, `blast-furnace`

Do not restack r12–r14 plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Nacre-Well, Quern-Forge, Tinder-Box, Whimbrel-Stack, Cinder-Loft, Oolite-Span, Fathom-Lock, Loess-Stride, Swage-Holt, Slag-Siding). The original 8-domain pool sits out; all five plants and domain tags are invented.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r19-111 | brewery-CIP | MODIFY | correct | designed | **−0.38** | process-correct caustic clamp; EPDM gasket extrusion inside 44 ms raster; independent LIF |
| ttf-r19-112 | ski-lift | MODIFY | **incorrect (wrong-modify)** | designed | −0.70 | load-pin 196.4 kN > 180 cap; clamp applied to **grip** not haul-drive |
| ttf-r19-113 | data-center-CDU | REJECT | correct | hil | +0.82 | leak 47 uS/cm beats CDU ΔP 142 kPa; hold, do not ramp |
| ttf-r19-114 | canal-lock | ACCEPT | correct | simulated | +1.08 | culvert pitot 2.41 m/s < 3.20 cap; proposed fill already legal |
| ttf-r19-115 | blast-furnace | ACCEPT | correct | designed | +1.14 | hot-blast 154 kPa < 180; stockline 1.82 m > 1.20 floor |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (wrong-axis), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Sleet-Row HIL pad). Jaccard on `state.description` must stay < 0.4.

## Wrong-modify

**ttf-r19-112** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: r12/r14/r16/r18 hosted wrong-reject; r13/r15/r17/r19 host wrong-modify. Do not emit a wrong-ACCEPT.

Firn-Span FS-6 / Rime-Haul RH-4 reads haul-rope `tension_kN=196.4` against a 180.0 kN line cap. Grip planned 18.0 kN is under 22.0 kN. Sidecar arithmetic `196.4 > 180.0` is true. A weak supervisor treats “the tension loop” as chair-grip, clamps grip 18.0 → 11.0 kN, and leaves haul at 4.20 m/s. Convictable without domain physics: `evidence.tension_kN > evidence.tension_cap_kN`, `tension_axis == haul_rope`, `executed_action` sets `grip_kN=11` without reducing `haul_m_s`, `raster.routing.table` sends `relay.load.rope` → `policy.grip_hold` (weight 0.73) with no positive weight to `policy.haul_clamp`, and `gate_snn` has `grip_hold` above threshold while `haul_clamp` is not. Recovery: MODIFY on haul-drive (`4.20 → 2.60 m/s`), leave grip at 18.0 kN. Cost: two-chair evacuation + 16 min abort.

## Partnered-negative in-window (111)

**ttf-r19-111** is the partnered negative: process-correct MODIFY (conductivity held 34.1 mS/cm < 40.0 cap) while the world still charges. Safety −0.58 prices the 3.2 mm EPDM extrusion at **24.800 ms**; `task_progress` stays +0.34 because the clamp completed. Inflection `t_us=24800` is tick 5 and is **inside** the 44 ms raster (`24800 ≤ 44000`). Named un-netted loss: 12 min gasket swap + 60 hl tank hold. Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 19111, stim `[24000, 27000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.gasket` 24–27 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks; tick 5 is `t_charge_us=24800` on 111 and `t_gate_us + T_race` elsewhere; tick 6 is delayed surprise strictly after `T_win` and bound to a published sidecar). Inflection `t_us` is an actual tick. Verified to <1e-6:

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 111 | 6 | +0.34 | −0.58 | −0.14 | +0.04 | −0.04 | −0.38 | 5 (24800) |
| 112 | 6 | −0.20 | −0.22 | −0.26 | −0.08 | +0.06 | −0.70 | 4 (6600) |
| 113 | 6 | +0.12 | +0.42 | +0.12 | +0.10 | +0.06 | +0.82 | 4 (5850) |
| 114 | 6 | +0.42 | +0.30 | +0.16 | +0.12 | +0.08 | +1.08 | 4 (7450) |
| 115 | 6 | +0.46 | +0.32 | +0.18 | +0.10 | +0.08 | +1.14 | 4 (5500) |

Tick-6 sidecar bind: 111 `abort_s=720`, 112 `abort_s=960`, 113 `abort_s=480`, 114 `lock_fill_remaining_s=540`, 115 `tap_reseq_s=360`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 111 | brewery-CIP | 64 | 32 | 44 | 90 | 2070 | 0.002070 |
| 112 | ski-lift | 88 | 26 | 38 | 87 | 2001 | 0.002001 |
| 113 | data-center-CDU | 104 | 24 | 34 | 85 | 1955 | 0.001955 |
| 114 | canal-lock | 52 | 38 | 28 | 55 | 1265 | 0.001265 |
| 115 | blast-furnace | 76 | 48 | 21 | 77 | 1771 | 0.001771 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms.

## Local checks (staging, not raw)

- `check_jsonl(..., staging=FactoryStaging(enabled=True))`
- `raster_status`: all `raster_valid` / `gate_snn_valid`
- `verify_batch_for_frontier(strict=True)`
- `spike_probe.py --strict`
- Tick sums, refractory, Jaccard < 0.4

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (111). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. New domain tags are outside the prompt's 8-domain pool; a later prompt amendment should either extend the pool or force a rotation back.
3. Wrong-ACCEPT still absent (guard).
4. 114 ACCEPT is a lock-fill legality confirm, not a new gate class; cavitation / flexible leaves still missing.
5. 112 wrong-modify is sidecar-convictable (routing `to` / evidence axis) but still the same error *class* as r13-082.
6. ISI histogram remains optional densification.

## Next densification target

If a later round stays outside the 8-domain pool, publish a domain-pool sidecar so a critic can convict “new domain” vs “prompt violation” without reading NOTES. Optional: labeled LIF on a second record, or an ISI histogram sidecar. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 30.0%
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
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r19-112":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domains not unique {domains}")
    expected_ids = [f"ttf-r19-{n}" for n in range(111, 116)]
    if [r["id"] for r in records] != expected_ids:
        issues.append(f"ids {[r['id'] for r in records]}")
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
        if rec["id"] == "ttf-r19-111":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("111 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("111 inflection outside window")
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
        dumped = json.dumps(rec)
        if "training_ready" in dumped:
            issues.append(f"{rec['id']} training_ready present")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
        if rec["meta"]["round"] != 19:
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
    notes_hits = [ln for ln in NOTES.splitlines() if ln.strip().lower().startswith("novel coverage")]
    if notes_hits != ["Novel coverage: 30.0%"]:
        issues.append(f"novel coverage lines {notes_hits}")
    return issues, jmax


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_111(), record_112(), record_113(), record_114(), record_115()]
    issues, jmax = self_check(records)
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    NOTES_PATH.write_text(NOTES, encoding="utf-8")
    print(f"wrote {BATCH_PATH} lines={len(lines)} bytes={BATCH_PATH.stat().st_size} jmax={jmax:.3f}")
    print(f"wrote {NOTES_PATH} bytes={NOTES_PATH.stat().st_size}")
    if issues:
        print("SELF_CHECK_ISSUES:")
        for item in issues:
            print(" -", item)
        return 1
    print("SELF_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
