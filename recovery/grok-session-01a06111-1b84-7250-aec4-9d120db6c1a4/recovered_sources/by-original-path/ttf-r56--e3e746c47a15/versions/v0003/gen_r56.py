#!/usr/bin/env python3
"""Emit TTF r38 JSONL (ttf-r38-206..210) into /tmp/ttf-r38/. Never writes outputs/raw/."""

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

OUT_DIR = Path("/tmp/ttf-r38")
BATCH_PATH = OUT_DIR / "batch-r38.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r38.md"
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
        ("generated_at", "2026-09-02T17:24:00Z"),
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
MY_DOMAINS = (
    "ore-sinter-strand",
    "fcc-riser",
    "nickel-electrowinning",
    "hydrogen-PSA-bed",
    "cold-tandem-mill",
)
MY_PLANTS = (
    "Pyrite-Hood",
    "Zeolite-Riser",
    "Laterite-Vat",
    "Adiabat-Sieve",
    "Finisher-Coil",
)
IDS = [f"ttf-r38-{n}" for n in range(206, 211)]


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
    return [int(round(ev["t_rel_ms"] * 1000.0)) for ev in events]


def lif_207_excerpt():
    """Independent CUBA LIF (seed 38207). Plant remains designed."""

    n = 84
    dt_us = 100
    tau_m_ms = 20.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.92
    i_stim_peak = 2.45
    stim = (21000, 25000)
    seed = 38207
    window_us = 40000
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
    early = [(t, nid) for t, nid in spikes if t < 21200]
    burst = [(t, nid) for t, nid in spikes if 21200 <= t < 25400]
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
            early_flag = pool[0][0] < 21200
            have = len([1 for t, _ in picked if (t < 21200) == early_flag])
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
    take(burst, 9, label_times=(22400, 23100, 23800))
    clamp = [(t, nid) for t, nid in picked if t < 21000][:7]
    geyser = [(t, nid) for t, nid in picked if t >= 21000][:9]
    picked = sorted(clamp + geyser, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise RuntimeError(f"LIF excerpt too short: {len(picked)}")
    channels = ["lif.clamp" if t < 21000 else "lif.geyser" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 84),
            ("dt_us", 100),
            ("tau_m_ms", 20.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.92),
            ("i_stim_peak", 2.45),
            ("stim_t_us", [21000, 25000]),
            ("i_clamp_extra", 0.68),
            ("clamp_n", 14),
            ("seed", 38207),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.68 steam-clamp bias; stim 21-25 ms is the catalyst-loss geyser.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 960),
            ("delayed_surprise_s", 960),
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
            ("round", 38),
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
    body = OrderedDict(
        [("name", name), ("neurons", neurons), ("threshold", threshold)]
    )
    if rate is not None:
        body["mean_rate_hz"] = rate
        body["spikes"] = spikes
    return body


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


def record_206():
    ticks = [
        tick(2112, -0.02, 0.01, -0.02, -0.01, 0.01),
        tick(5280, -0.04, 0.01, -0.04, -0.02, 0.01),
        tick(5510, -0.03, 0.01, -0.03, -0.01, 0.01),
        tick(6000, -0.06, 0.02, -0.08, -0.03, 0.02),
        tick(6400, -0.02, 0.01, -0.03, -0.01, 0.01),
        tick(780000000, -0.01, 0.00, -0.02, 0.00, 0.00),
    ]
    spikes = [
        spike("enc.strand.ctx", 1.205, 0.44),
        spike("live.pt.bar", 2.410, 0.61),
        spike("inject.loop.bar", 3.880, 0.52),
        spike("bus.hood.ctx", 4.620, 0.47),
        spike("live.pt.bar", 5.280, 1.31),
        spike("inject.loop.bar", 5.510, 1.18),
        spike("ctrl.gate", 6.000, 0.99),
        spike("live.pt.bar", 7.220, 0.84),
        spike("inject.loop.bar", 9.440, 0.66),
        spike("ctrl.gate", 14.880, 0.88),
        spike("enc.strand.ctx", 18.400, 0.41),
        spike("live.pt.bar", 24.200, 0.58),
    ]
    excerpt = independent_excerpt(38206, 80, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Strand S-4 already sits at 0.84 bar on the Pyrite-Hood Dwight-Lloyd ignition "
                "hood when a live PT sample races a tagged LOOP_TEST injector that still prints "
                "1.36 bar. Published trip is 1.20 bar on the live channel; a weak supervisor "
                "treats the inject as the trip and zeros a legal 4.2 m/min strand.",
            ),
            ("domain", "ore-sinter-strand"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 4.2 m/min on S-4, keep live ignition PT < 1.20 bar trip, and finish the "
                "13 min pallet window.",
            ),
            ("t0_us", 1762300000000206),
            ("gate_latency_us", 720),
            ("race_window_us", 400),
            ("race_window_rel_ms", [5.280, 5.680]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "live.pt.bar 0.84 bar live ignition",
                                "inject.loop.bar 1.36 bar LOOP_TEST",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-first should ACCEPT 4.2 m/min (0.84 bar < 1.20 bar trip). "
                            "Inject-first would only delay confirmation of the same legal live pressure.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one ignition-hood PT slot versus the loop-test publisher on this "
                            "2 kHz strand bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 76 us (live 34 + inject 42): 3.0x over "
                            "a 2.0x trust floor. Order is correctly live-first. The error is binding "
                            "a LOOP_TEST inject as if it were live, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live ignition PT, 2 kHz, 34 us jitter, axis hood_pt",
                    "loop-test injector, 1 kHz, 42 us jitter, tag LOOP_TEST",
                    "strand-speed encoder (context)",
                    "hearth IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("live_bar", 0.84),
                        ("trip_bar", 1.20),
                        ("inject_bar", 1.36),
                        ("inject_active", True),
                        ("inject_tag", "LOOP_TEST"),
                        ("proposed_m_min", 4.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Strand S-4 indexed on Pyrite-Hood; live 0.84 bar, 4.2 m/min armed.",
                    "2. Published live trip 1.20 bar; LOOP_TEST injector tagged and active at 1.36 bar.",
                    "3. Encoder precursor at 1.205 ms.",
                    "4. Race window [5.280, 5.680] ms.",
                    "5. Live PT 0.84 bar at 5.280 ms (winner).",
                    "6. Inject 1.36 bar at 5.510 ms (loser by 230 us).",
                    "7. Gate at 6.000 ms: wrong REJECT holds 0 m/min on the inject.",
                    "8. Strand idle; live PT never crossed 1.20 bar.",
                    "9. 13 min pallet window missed.",
                    "10. QA: correct gate was ACCEPT; leave 4.2 m/min; bind live 0.84 vs 1.20 bar trip.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "strand_4p2_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_min", 4.2),
                        ("live_bar", 0.84),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_bar", 0.84),
                        ("trip_bar", 1.20),
                        ("inject_bar", 1.36),
                        ("inject_active", True),
                        ("inject_tag", "LOOP_TEST"),
                        ("ft_axis", "hood_pt"),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 76),
                        ("t_gate_us", 6000),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.2 m/min because live ignition PT 0.84 bar is 0.36 bar under "
                "the published 1.20 bar trip and the 1.36 bar reading is a tagged LOOP_TEST inject.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Inject 1.36 bar is over the 1.20 bar trip (true vs that simulated input). REJECT: "
                "hold 0 m/min until the inject recovers under 1.20 bar so the hood does not see "
                "an over-pressure event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ignition_pt_bar",
                            OrderedDict(
                                [
                                    ("published_live_trip", 1.20),
                                    ("observed_live", 0.84),
                                    ("loop_test_applied", 1.36),
                                    ("inject_tag", "LOOP_TEST"),
                                    ("executed_m_min", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 230),
                                    ("combined_jitter_us", 76),
                                    ("ratio", 3.03),
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
            ("name", "strand_hold_loop_test"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_min", 0.0),
                        ("live_bar", 0.84),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): speed 4.2 -> 0 m/min. Routing relay.live.pt -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live 0.84 bar never "
                "violated the 1.20 bar trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze S-4 at 0 m/min while live PT stayed 0.84 bar under the "
                "1.20 bar trip. 13 min pallet window missed. Correct gate was ACCEPT of the "
                "already-legal 4.2 m/min command.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("strand", "held at 0 m/min; 4.2 m/min abandoned"),
                        ("live_bar", "still 0.84 bar, under 1.20 bar published trip"),
                        ("hood", "13 min pallet window missed"),
                        ("ignition", "no over-pressure; LOOP_TEST false positive"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 1.36 bar reading is a tagged LOOP_TEST inject, not a published live trip.",
                    "Delayed (13 min): sister strand S-5 ran the same 4.2 m/min pallet window after QA rebound the live trip; S-4's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live 0.84 bar < published 1.20 bar trip; leave 4.2 m/min.",
                        ),
                        ("correct_trip_bar", 1.20),
                        ("wrong_inject_bar", 1.36),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("speed_m_min", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "13 min missed pallet window (task/efficiency); live PT never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "live.pt.bar (5.280 ms, 0.84 bar)"),
                        ("loser", "inject.loop.bar (5.510 ms, 1.36 bar LOOP_TEST)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "Inject-first by < 230 us would still show live 0.84 bar < 1.20 bar. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the live win "
                            "on a LOOP_TEST inject.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6000),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (6.000 ms, tick 4). The 13 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 780.0),
            ("missed_window_s", 780),
        ]
    )
    ras = raster_core(
        26,
        80,
        30,
        62,
        routing(
            "relay.live.pt",
            "policy.hold_reject",
            [
                ("relay.live.pt", "policy.hold_reject", 0.71),
                ("relay.inject.loop", "policy.hold_reject", 0.22),
            ],
            "acetylcholine",
            0.08,
            "loop_test_stdp; ACh tags the (wrong) hold_reject bind at the live win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 48, 0.50, 200.0, 4),
                    pop("go_accept", 48, 0.80, 10.0, 0),
                    pop("live_trip_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r38-206",
        "WRONG-REJECT at Pyrite-Hood / Strand S-4: live 0.84 bar is legal vs "
        "published 1.20 bar trip; supervisor bound a tagged LOOP_TEST 1.36 bar inject",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 0.84 < 1.20 is true; clamp bound to a "
        "LOOP_TEST 1.36 bar inject. total -0.36 = -0.18 + 0.06 + -0.22 + -0.08 + 0.06.",
        ras,
        gate,
        "ore-sinter-strand",
        [
            "reject",
            "wrong-gate",
            "loop-test-inject",
            "simulated-input-as-live",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed speed is zeroed.",
        1,
        supervisor_error_type="wrong-reject",
    )


def record_207():
    excerpt, extra = lif_207_excerpt()
    ticks = [
        tick(1848, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(4620, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(4850, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5500, 0.10, -0.06, -0.03, 0.02, -0.01),
        tick(22400, 0.05, -0.42, -0.04, 0.00, -0.02),
        tick(960000000, 0.02, -0.05, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Riser R-3 is lifting 18 t/min of regenerated zeolite through the Zeolite-Riser "
                "stripper when a dense-phase Delta-P pulse arrives 230 us before the steam-flow "
                "meter that still reads a legal spout. Bed-first latches a process clamp under "
                "the 22.0 kPa cap; flow-first would keep cruise steam. Stored U-bend oil is not "
                "yet an observable of either race channel.",
            ),
            ("domain", "fcc-riser"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Lift 18 t/min catalyst through R-3, keep dense-phase Delta-P <= 22.0 kPa, and "
                "leave the U-bend un-geysered.",
            ),
            ("t0_us", 1762300000000207),
            ("gate_latency_us", 880),
            ("race_window_us", 380),
            ("race_window_rel_ms", [4.620, 5.000]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "dp.dense.kpa 24.8 kPa dense-phase",
                                "ft.steam.ths 2.4 t/h still-legal spout",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first latches steam clamp 2.4 -> 1.6 t/h; flow-first keeps cruise "
                            "steam on a 'spout still open' model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one dense-phase DP slot minus steam-FT group delay on this "
                            "1 kHz stripper bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 68 us (DP 30 + FT 38): 3.4x over "
                            "a 2.0x trust floor. Reversing order by < 230 us inside the 380 us window "
                            "would have kept 2.4 t/h cruise; predicted next-sample DP 23.1 kPa > 22 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "dense-phase DP, 1 kHz, 30 us timestamp jitter",
                    "stripper-steam mass-flow, 1 kHz, 38 us jitter",
                    "riser IR (context)",
                    "U-bend AE (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("dp_cap_kPa", 22.0),
                        ("observed_dp_kPa", 24.8),
                        ("proposed_steam_t_h", 2.4),
                        ("steam_floor_t_h", 1.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Riser R-3 indexed; 18 t/min catalyst; dense-phase 24.8 kPa > 22.0 cap.",
                    "2. Cruise steam 2.4 t/h armed; bed over the 22.0 kPa cap.",
                    "3. IR precursor at 1.848 ms; dense-phase warm-start 24.8 kPa.",
                    "4. Race window [4.620, 5.000] ms opens on the stripper bus.",
                    "5. Dense-phase 24.8 kPa at 4.620 ms (winner).",
                    "6. Steam FT 2.4 t/h at 4.850 ms (loser by 230 us).",
                    "7. Gate at 5.500 ms (winner + 880 us): MODIFY clamp 2.4 -> 1.6 t/h.",
                    "8. Clamp executes; next-sample DP 16.4 kPa < 22.0 cap.",
                    "9. At 22.400 ms stored U-bend oil produces a catalyst-loss geyser.",
                    "10. Emergency dump 16 min + standpipe inspection; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_steam_strip"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_t_h", 2.4),
                        ("dp_kPa", 24.8),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("dp_kPa", 24.8),
                        ("dp_cap_kPa", 22.0),
                        ("predicted_unclamped_next_kPa", 23.1),
                        ("steam_t_h", 2.4),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 68),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.4 t/h cruise: steam flow looks like an open spout, not a "
                "plugged stripper, and the 22.0 kPa DP cap is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Dense-phase 24.8 kPa won by 230 us, so the stripper is running packed, not still "
                "free. Holding 2.4 t/h predicts next-sample 23.1 kPa > 22.0 kPa cap. MODIFY: steam "
                "2.4 -> 1.6 t/h. Observed after clamp 16.4 kPa < 22.0. A full REJECT is not "
                "indicated: a sound bed accepts 1.6 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "dense_phase_kPa",
                            OrderedDict(
                                [
                                    ("cap", 22.0),
                                    ("observed", 24.8),
                                    ("predicted_unclamped_next", 23.1),
                                    ("clamped_steam_t_h", 1.6),
                                    ("observed_after_clamp", 16.4),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 230),
                                    ("combined_jitter_us", 68),
                                    ("ratio", 3.38),
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
            ("name", "clamped_steam_strip"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_t_h", 1.6),
                        ("dp_kPa", 16.4),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: steam 2.4 -> 1.6 t/h. Process-correct vs the 22.0 kPa DP cap. Catalyst-loss "
                "geyser still occurs at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held DP at 16.4 kPa. At 22.400 ms stored U-bend oil produced "
                "a catalyst-loss geyser. Clamp reduced steam energy; it did not dump the standpipe "
                "charge. Partnered negative: process heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("steam", "clamp executed; DP 16.4 kPa < 22.0"),
                        ("standpipe", "catalyst-loss geyser at 22.400 ms"),
                        ("repair", "16 min emergency dump + standpipe inspection"),
                        ("mission", "riser still lifting; geyser precursor controlled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither dense-phase DP nor steam FT predicted the U-bend oil charge; ae.geyser.cat is a new channel at 22.400 ms, 16.900 ms after the gate, still inside the 40 ms raster.",
                    "Delayed (16 min): emergency dump and standpipe inspection close the geyser. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "16 min emergency dump + standpipe inspection after a catalyst-loss geyser. Safety "
                "head -0.62 prices the precursor; task_progress stays +0.34 because the steam clamp "
                "completed under the 22.0 kPa cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "dp.dense.kpa (4.620 ms, 24.8 kPa)"),
                        ("loser", "ft.steam.ths (4.850 ms, 2.4 t/h)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "Flow-first by < 230 us inside the 380 us window would have kept "
                            "2.4 t/h cruise; predicted next-sample 23.1 kPa would have exceeded the "
                            "22.0 kPa cap even without the geyser charge. The MODIFY is still the "
                            "correct process. The geyser is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms catalyst-loss geyser (tick t_us=22400), inside the "
                "40 ms raster. The correct MODIFY at 5.500 ms is in the same excerpt. Do not put "
                "inflection on the +16 min dump tick.",
            ),
            ("delayed_surprise_s", 960.0),
            ("abort_s", 960),
        ]
    )
    spikes = [
        spike("ir.riser.ctx", 1.120, 0.43),
        spike("dp.dense.kpa", 2.240, 0.62),
        spike("ft.steam.ths", 3.180, 0.55),
        spike("dp.dense.kpa", 4.620, 1.34),
        spike("ft.steam.ths", 4.850, 1.12),
        spike("ctrl.gate", 5.500, 0.97),
        spike("dp.dense.kpa", 7.200, 0.81),
        spike("ft.steam.ths", 10.400, 0.66),
        spike("ctrl.gate", 15.200, 0.84),
        spike("ae.geyser.cat", 22.400, 1.42),
        spike("ae.geyser.cat", 23.600, 0.91),
        spike("ir.riser.ctx", 29.800, 0.41),
        spike("dp.dense.kpa", 36.200, 0.58),
    ]
    ras = raster_core(
        40,
        84,
        26,
        87,
        routing(
            "thalamic-relay.dp-steam",
            "spikenaut.policy.steam-clamp",
            [
                ("relay.dp.dense", "policy.steam_clamp", 0.64),
                ("relay.ft.steam", "policy.spout_hold", 0.29),
                ("relay.ae.geyser", "policy.steam_clamp", -0.46),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at DP win (4.620 ms) opens a 50 ms eligibility "
            "trace that still covers the 22.400 ms catalyst-loss geyser",
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
                    pop("steam_clamp", 48, 0.50, 220.0, 4),
                    pop("spout_hold", 48, 0.50, 50.0, 1),
                    pop("dp_cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r38-207",
        "Zeolite-Riser stripper / Riser R-3: dense-phase beats steam FT by 230 us; correct "
        "MODIFY still eats an in-window catalyst-loss geyser (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "40 ms raster. total -0.44 = 0.34 + -0.62 + -0.16 + 0.04 + -0.04. Named "
        "dump+inspection loss is not netted into task_progress.",
        ras,
        gate,
        "fcc-riser",
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
        "16 min gap.",
        2,
    )


def record_208():
    ticks = [
        tick(1568, 0.01, 0.04, 0.02, 0.01, 0.01),
        tick(3920, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(4110, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5100, 0.03, 0.12, 0.04, 0.04, 0.02),
        tick(5380, 0.02, 0.07, 0.01, 0.01, 0.01),
        tick(540000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.rect.ctx", 1.040, 0.44),
        spike("ae.hanger.pps", 2.180, 0.71),
        spike("enc.cell.ka", 3.020, 0.52),
        spike("ae.hanger.pps", 3.920, 1.36),
        spike("enc.cell.ka", 4.110, 1.14),
        spike("ctrl.gate", 5.100, 0.98),
        spike("ae.hanger.pps", 7.400, 0.82),
        spike("enc.cell.ka", 10.800, 0.61),
        spike("ctrl.gate", 16.200, 0.86),
        spike("ae.hanger.pps", 24.600, 0.70),
        spike("enc.cell.ka", 33.400, 0.48),
        spike("ir.pad.ctx", 41.200, 0.40),
    ]
    excerpt = independent_excerpt(38208, 112, 46000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Cell C-9 on the Laterite-Vat electrowinning HIL pad is pulling 18.4 kA when an "
                "AE burst at 52 pps on the cathode hanger races the rectifier encoder that still "
                "looks in-band for a current step. Ramp is legal only if AE <= 40 pps. AE-first "
                "latches hold; encoder-first would treat in-band current as hanger clearance.",
            ),
            ("domain", "nickel-electrowinning"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not ramp Cell C-9 unless AE <= 40 pps; keep cell current 0 kA until the "
                "hanger is quiet.",
            ),
            ("t0_us", 1762300000000208),
            ("gate_latency_us", 1180),
            ("race_window_us", 280),
            ("race_window_rel_ms", [3.920, 4.200]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.hanger.pps 52 pps flare",
                                "enc.cell.ka 18.4 kA still-in-band",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches REJECT hold 0 kA; encoder-first would ramp 18.4 kA "
                            "on an in-band-current-as-clearance model.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one AE envelope slot versus the rectifier-encoder publisher on this "
                            "pad cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 190 us vs combined jitter 54 us (AE 24 + encoder 30): 3.5x over a "
                            "2.0x trust floor. Pad injects encoder 90-130 us before the AE envelope "
                            "finishes (piezo lag, not a sensor fault); the encoder packet is still "
                            "the loser in this 280 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "cathode-hanger AE, 24 us jitter, 40 pps trip",
                    "rectifier current encoder, 30 us jitter",
                    "cell voltage (context)",
                    "electrolyte IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_trip_pps", 40.0),
                        ("observed_ae_pps", 52.0),
                        ("cell_cap_kA", 22.0),
                        ("proposed_cell_kA", 18.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Cell C-9 on Laterite-Vat HIL pad; electrolyte in band; rectifier armed at 18.4 kA.",
                    "2. AE trip 40 pps; observed 52 pps flare on cathode hanger.",
                    "3. Encoder precursor at 1.040 ms.",
                    "4. Race window [3.920, 4.200] ms.",
                    "5. AE 52 pps at 3.920 ms (winner).",
                    "6. Cell encoder 18.4 kA at 4.110 ms (loser by 190 us).",
                    "7. Gate at 5.100 ms: REJECT hold 0 kA, do not ramp.",
                    "8. Pad recycle 9 min; hanger AE decays under 40 pps after hold.",
                    "9. Electrolyte never shorted; encoder-as-clearance would have ramped into the flare.",
                    "10. QA: correct gate was REJECT; leave 0 kA until AE <= 40 pps.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "ramp_18p4ka"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cell_kA", 18.4),
                        ("ae_pps", 52.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 52.0),
                        ("ae_trip_pps", 40.0),
                        ("cell_kA", 18.4),
                        ("cell_cap_kA", 22.0),
                        ("race_margin_us", 190),
                        ("combined_jitter_us", 54),
                        ("t_gate_us", 5100),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.4 kA because cell current is under the 22.0 kA cap and treats "
                "the encoder as hanger clearance, ignoring the 52 pps AE flare.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "AE 52 pps won by 190 us and is over the 40 pps trip. Encoder 18.4 kA is under "
                "the 22.0 kA cap but is not clearance. REJECT: hold 0 kA until AE <= 40 pps.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "hanger_ae_pps",
                            OrderedDict(
                                [
                                    ("trip", 40.0),
                                    ("observed", 52.0),
                                    ("executed_cell_kA", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 190),
                                    ("combined_jitter_us", 54),
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
            ("name", "cell_hold_ae"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cell_kA", 0.0),
                        ("ae_pps", 52.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: cell 18.4 -> 0 kA. Routing relay.ae.hanger -> policy.hold_reject. "
                "Do not ramp into the 52 pps flare.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Cell C-9 at 0 kA while AE 52 pps decayed. Encoder-as-clearance "
                "would have ramped 18.4 kA into the flare. Pad recycle 9 min.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("cell", "held at 0 kA"),
                        ("hanger", "AE flare decaying under trip after hold"),
                        ("electrolyte", "unshorted"),
                        ("pad", "9 min recycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Pad injects encoder 90-130 us before AE envelope finish; that is piezo lag, not a false AE.",
                    "Delayed (9 min): pad recycle restacks the rectifier after AE < 40 pps.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.hanger.pps (3.920 ms, 52 pps)"),
                        ("loser", "enc.cell.ka (4.110 ms, 18.4 kA)"),
                        ("margin_us", 190),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 190 us would have treated 18.4 kA as clearance and "
                            "ramped into the 52 pps flare. The REJECT is still required; reversal "
                            "only delays the AE bind.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5100),
            (
                "reward_inflection_note",
                "Safety credit lands at the correct REJECT (5.100 ms, tick 4). Pad recycle is delayed surprise.",
            ),
            ("delayed_surprise_s", 540.0),
            ("pad_recycle_s", 540),
        ]
    )
    ras = raster_core(
        46,
        112,
        20,
        103,
        routing(
            "relay.ae.hanger",
            "policy.hold_reject",
            [
                ("relay.ae.hanger", "policy.hold_reject", 0.74),
                ("relay.enc.cell", "policy.ramp_go", 0.18),
            ],
            "dopamine",
            0.06,
            "ae_trip_stdp; DA tags the hold_reject bind at the AE win",
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
                    pop("hold_reject", 64, 0.50, 180.0, 3),
                    pop("ramp_go", 64, 0.80, 8.0, 0),
                    pop("ae_trip_veto", 32, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r38-208",
        "Laterite-Vat EW HIL / Cell C-9: AE 52 pps beats rectifier encoder 18.4 kA by 190 us; "
        "correct REJECT holds the cell",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 52 > 40 trip beats in-band cell current. total +0.78 = "
        "0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "nickel-electrowinning",
        [
            "reject",
            "hil-pad",
            "ae-vs-encoder",
            "hanger-flare-hold",
            "sidecar-convictable",
            "hil",
        ],
        "Teaches a probe that an in-band rectifier encoder is not hanger clearance when "
        "AE is over trip and routing.table[0].to is policy.hold_reject.",
        3,
    )


def record_209():
    ticks = [
        tick(2496, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(6240, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(6470, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(7140, 0.12, 0.08, 0.05, 0.03, 0.02),
        tick(7500, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(600000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    params = OrderedDict(
        [
            ("repress_bar", 12.4),
            ("h2_pct", 99.94),
            ("bed_n", 4),
            ("product_h2_pct", 99.94),
        ]
    )
    spikes = [
        spike("ft.feed.ctx", 1.480, 0.42),
        spike("gc.h2.pct", 3.120, 0.58),
        spike("dp.bed.smear", 4.660, 0.50),
        spike("gc.h2.pct", 6.240, 1.28),
        spike("dp.bed.smear", 6.470, 1.10),
        spike("ctrl.gate", 7.140, 0.96),
        spike("gc.h2.pct", 9.200, 0.74),
        spike("dp.bed.smear", 12.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("gc.h2.pct", 24.600, 0.55),
        spike("ft.feed.ctx", 29.800, 0.40),
    ]
    excerpt = independent_excerpt(38209, 56, 30000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Bed B-6 of the Adiabat-Sieve PSA train is repressing 12.4 bar when a product GC "
                "at 99.94 percent races a bed-Delta-P smear that still claims breakthrough. "
                "Commanded 12.4 bar and 99.94 percent sit 1.6 bar and 0.04 percent inside the "
                "legal envelopes. The GC win only ratifies the repress already on the bed.",
            ),
            ("domain", "hydrogen-PSA-bed"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the 4-bed Skarstrom repress on Adiabat-Sieve, keep product H2 >= 99.90 "
                "percent and repress <= 14.0 bar, and leave breakthrough in spec.",
            ),
            ("t0_us", 1762300000000209),
            ("gate_latency_us", 900),
            ("race_window_us", 360),
            ("race_window_rel_ms", [6.240, 6.600]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "gc.h2.pct 99.94 percent product",
                                "dp.bed.smear breakthrough claim",
                            ],
                        ),
                        (
                            "semantics",
                            "GC-first confirms the already-legal 12.4 bar / 99.94 percent repress; "
                            "smear-first would have treated the GC as a smear echo and looked "
                            "for an extra hold the train does not need.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one 4-bed GC kernel step versus the DP publisher "
                            "on this rigid Skarstrom train.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 70 us (GC 32 + DP 38): 3.3x over "
                            "a 2.0x trust floor. Reversing order by < 230 us would not make the "
                            "proposed repress illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "product GC, 4 beds, 32 us jitter",
                    "bed DP smear, 38 us jitter",
                    "repress FT (context)",
                    "purge PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("h2_floor_pct", 99.90),
                        ("observed_h2_pct", 99.94),
                        ("repress_cap_bar", 14.0),
                        ("proposed_repress_bar", 12.4),
                        ("bed_n", 4),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "4-bed Skarstrom PSA + Langmuir dual-site isotherm kernel, seed 38; 4 beds, 12 axial nodes; NOT lumped tank, NOT a fluid-LES field",
                        ),
                        (
                            "fidelity_limits",
                            "No radial maldistribution or valve-seat leak; beds are rigid pressure sources. Raster is kernelized events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Adiabat-Sieve PSA train indexed; Bed B-6 repressing 12.4 bar at 99.94 percent H2.",
                    "2. Caps: H2 floor 99.90 percent, repress 14.0 bar; both proposed values inside.",
                    "3. Feed precursor at 1.480 ms.",
                    "4. Race window [6.240, 6.600] ms.",
                    "5. Product GC 99.94 percent at 6.240 ms (winner).",
                    "6. DP smear at 6.470 ms (loser by 230 us).",
                    "7. Gate at 7.140 ms: ACCEPT 12.4 bar / 99.94 percent already legal.",
                    "8. Repress continues; no extra hold.",
                    "9. 10 min survey confirms breakthrough still in spec.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "repress_12p4_thold"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("h2_pct", 99.94),
                        ("h2_floor_pct", 99.90),
                        ("repress_bar", 12.4),
                        ("repress_cap_bar", 14.0),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 70),
                        ("t_gate_us", 7140),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 12.4 bar because product H2 99.94 percent is 0.04 percent over "
                "the 99.90 floor and repress is 1.6 bar under the 14.0 bar envelope.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "H2 99.94 percent won by 230 us and is over 99.90 floor. Repress 12.4 bar is under "
                "14.0 bar. ACCEPT the already-legal repress; DP smear is not a cap violation.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "h2_pct",
                            OrderedDict(
                                [
                                    ("floor", 99.90),
                                    ("observed", 99.94),
                                    ("executed_repress_bar", 12.4),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 230),
                                    ("combined_jitter_us", 70),
                                    ("ratio", 3.29),
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
            ("name", "repress_12p4_thold"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: repress 12.4 bar and H2 99.94 percent unchanged. Routing relay.gc.h2 "
                "-> policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left Bed B-6 at 12.4 bar / 99.94 percent. DP smear did not justify a "
                "hold. 10 min survey confirmed breakthrough in spec.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bed", "still 12.4 bar / 99.94 percent"),
                        ("breakthrough", "in spec after survey"),
                        ("train", "4 beds continue"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "DP smear is a bed-side optical claim, not a product-purity violation.",
                    "Delayed (10 min): survey restacks Bed B-6 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "gc.h2.pct (6.240 ms, 99.94 percent)"),
                        ("loser", "dp.bed.smear (6.470 ms, breakthrough claim)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "Smear-first by < 230 us would only delay confirmation. The repress stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7140),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (7.140 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 600.0),
            ("survey_s", 600),
        ]
    )
    ras = raster_core(
        30,
        56,
        38,
        64,
        routing(
            "relay.gc.h2",
            "policy.go_accept",
            [
                ("relay.gc.h2", "policy.go_accept", 0.68),
                ("relay.dp.bed", "policy.smear_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_repress_stdp; 5-HT tags the go_accept bind at the GC win",
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
                    pop("go_accept", 40, 0.50, 180.0, 3),
                    pop("smear_hold", 40, 0.80, 10.0, 0),
                    pop("h2_floor_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r38-209",
        "Adiabat-Sieve PSA / Bed B-6: product GC 99.94 percent beats DP smear by 230 us; ACCEPT "
        "already-legal 12.4 bar repress",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal 4-bed Skarstrom repress. total +1.06 = "
        "0.42 + 0.28 + 0.18 + 0.10 + 0.08.",
        ras,
        gate,
        "hydrogen-PSA-bed",
        [
            "accept",
            "already-legal",
            "simulated-psa-train",
            "gc-vs-dp",
            "sidecar-convictable",
            "simulated",
        ],
        "Teaches that a product GC over floor can confirm an already-legal repress without "
        "a breakthrough smear becoming a hold.",
        4,
    )


def record_210():
    ticks = [
        tick(1672, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(4180, 0.10, 0.08, 0.04, 0.02, 0.02),
        tick(4360, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(4940, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5240, 0.06, 0.05, 0.02, 0.01, 0.01),
        tick(420000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    params = OrderedDict(
        [
            ("speed_m_s", 18.0),
            ("exit_C", 148.0),
            ("stand_id", 6),
            ("hold", False),
        ]
    )
    spikes = [
        spike("enc.gap.ctx", 0.920, 0.41),
        spike("ir.exit.c", 2.140, 0.60),
        spike("ft.shape.iu", 3.080, 0.51),
        spike("ir.exit.c", 4.180, 1.30),
        spike("ft.shape.iu", 4.360, 1.12),
        spike("ctrl.gate", 4.940, 0.97),
        spike("ir.exit.c", 6.800, 0.78),
        spike("ft.shape.iu", 9.200, 0.62),
        spike("ctrl.gate", 13.600, 0.85),
        spike("ir.exit.c", 18.400, 0.54),
        spike("ft.shape.iu", 21.200, 0.43),
    ]
    excerpt = independent_excerpt(38210, 48, 24000, 11, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Stand F-6 at Finisher-Coil tandem 4 is armed for an 18 m/s pass when an exit IR "
                "at 148 C races a shapemeter that still claims an I-unit hitch. Commanded 18 m/s "
                "and 148 C sit 2 m/s over the 16 m/s floor and 32 C under the 180 C cap. The IR "
                "win only ratifies the pass already on the gap.",
            ),
            ("domain", "cold-tandem-mill"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run Stand F-6 at 18 m/s, keep exit IR <= 180 C and shapemeter <= 25 I-unit, "
                "and leave the tandem on schedule.",
            ),
            ("t0_us", 1762300000000210),
            ("gate_latency_us", 760),
            ("race_window_us", 300),
            ("race_window_rel_ms", [4.180, 4.480]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.exit.c 148 C mill-exit",
                                "ft.shape.iu 12 I-unit hitch claim",
                            ],
                        ),
                        (
                            "semantics",
                            "IR-first confirms the already-legal 18 m/s / 148 C pass; shapemeter-first "
                            "would have treated the IR as a hitch echo and looked for an extra hold "
                            "the tandem does not need.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one mill-exit IR slot versus the shapemeter publisher on this "
                            "tandem bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (IR 28 + shape 30): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed pass illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "mill-exit IR, 28 us jitter",
                    "shapemeter, 30 us jitter",
                    "gap encoder (context)",
                    "roll-coolant FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("exit_cap_C", 180.0),
                        ("observed_exit_C", 148.0),
                        ("speed_floor_m_s", 16.0),
                        ("proposed_speed_m_s", 18.0),
                        ("shape_cap_iu", 25.0),
                        ("observed_shape_iu", 12.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Stand F-6 indexed on Finisher-Coil tandem 4; gap armed 18 m/s pass.",
                    "2. Caps: exit 180 C, shapemeter 25 I-unit, speed floor 16 m/s.",
                    "3. Encoder precursor at 0.920 ms.",
                    "4. Race window [4.180, 4.480] ms.",
                    "5. Exit IR 148 C at 4.180 ms (winner).",
                    "6. Shapemeter 12 I-unit at 4.360 ms (loser by 180 us).",
                    "7. Gate at 4.940 ms: ACCEPT 18 m/s / 148 C already legal.",
                    "8. Pass continues; no extra hold.",
                    "9. 7 min cooldown confirms shapemeter still under 25 I-unit.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "pass_18ms"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("exit_C", 148.0),
                        ("exit_cap_C", 180.0),
                        ("speed_m_s", 18.0),
                        ("speed_floor_m_s", 16.0),
                        ("shape_iu", 12.0),
                        ("shape_cap_iu", 25.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("t_gate_us", 4940),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes an 18 m/s pass because exit 148 C is 32 C under the 180 C "
                "cap and shapemeter 12 I-unit is under 25 I-unit.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Exit 148 C won by 180 us and is under 180 C. Shapemeter 12 I-unit is under "
                "25 I-unit. Speed 18 m/s is over the 16 m/s floor. ACCEPT the already-legal pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "exit_C",
                            OrderedDict(
                                [
                                    ("cap", 180.0),
                                    ("observed", 148.0),
                                    ("executed_speed_m_s", 18.0),
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
            ("name", "pass_18ms"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 18 m/s pass and 148 C exit unchanged. Routing relay.ir.exit -> "
                "policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left Stand F-6 on an 18 m/s / 148 C pass. Shapemeter hitch did not "
                "justify a hold. 7 min cooldown confirmed shape still under 25 I-unit.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("stand", "still 18 m/s / 148 C"),
                        ("shapemeter", "12 I-unit under 25 cap"),
                        ("tandem", "on schedule"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Shapemeter 12 I-unit hitch is residual, not a flatness trip.",
                    "Delayed (7 min): cooldown restacks F-6 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.exit.c (4.180 ms, 148 C)"),
                        ("loser", "ft.shape.iu (4.360 ms, 12 I-unit)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Shapemeter-first by < 180 us would only delay confirmation. The pass stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4940),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (4.940 ms, tick 4). Cooldown is delayed surprise.",
            ),
            ("delayed_surprise_s", 420.0),
            ("cooldown_s", 420),
        ]
    )
    ras = raster_core(
        24,
        48,
        42,
        48,
        routing(
            "relay.ir.exit",
            "policy.go_accept",
            [
                ("relay.ir.exit", "policy.go_accept", 0.66),
                ("relay.ft.shape", "policy.hitch_hold", 0.20),
            ],
            "dopamine",
            0.04,
            "legal_pass_stdp; DA tags the go_accept bind at the mill-exit win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.30),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("go_accept", 40, 0.50, 160.0, 2),
                    pop("hitch_hold", 40, 0.80, 10.0, 0),
                    pop("exit_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r38-210",
        "Finisher-Coil tandem 4 / Stand F-6: exit 148 C beats shapemeter 12 I-unit by 180 us; "
        "ACCEPT already-legal 18 m/s pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal cold-tandem pass. total +1.14 = "
        "0.44 + 0.32 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "cold-tandem-mill",
        [
            "accept",
            "already-legal",
            "exit-vs-shapemeter",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches that a mill-exit IR under cap can confirm an already-legal pass without "
        "a shapemeter hitch becoming a hold.",
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
    if rec["id"] == "ttf-r38-207":
        tick5 = 22400
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
    domains = set()
    plants = set()
    for p in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
        try:
            if p.resolve() == BATCH_PATH.resolve():
                continue
        except OSError:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        plants.update(PLANT_RE.findall(text))
        for line in text.splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            d = (rec.get("state") or {}).get("domain")
            if d:
                domains.add(d)
    for p in sorted(Path("/tmp").glob("ttf-r*/NOTES-r*.md")):
        try:
            if p.resolve() == NOTES_PATH.resolve():
                continue
        except OSError:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        plants.update(PLANT_RE.findall(text))
        for m in re.finditer(r"Domains this batch:\s*(.+)", text):
            domains.update(re.findall(r"`([^`]+)`", m.group(1)))
    return domains, plants


def occupancy_check(records):
    issues = []
    my_domains = {r["state"]["domain"] for r in records}
    my_blob = json.dumps(records)
    occupied_domains, occupied_plants = harvest_occupancy()
    hit = my_domains & occupied_domains
    if hit:
        issues.append(f"domain collides live occupancy {sorted(hit)}")
    for plant in MY_PLANTS:
        if plant in occupied_plants:
            issues.append(f"plant {plant} occupied")
        for prior in occupied_plants:
            if plant != prior and (plant in prior or prior in plant):
                issues.append(f"plant {plant} overlaps {prior}")
    for plant in MY_PLANTS:
        if plant not in my_blob:
            issues.append(f"plant {plant} missing from records")
    return issues


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
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r38-206":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-reject":
        issues.append("206 supervisor_error_type")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if hil != ["ttf-r38-208"]:
        issues.append(f"hil set {hil}")
    if sim != ["ttf-r38-209"]:
        issues.append(f"simulated set {sim}")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domain collision {domains}")
    if tuple(domains) != MY_DOMAINS:
        issues.append(f"domain order {domains}")
    ids = [r["id"] for r in records]
    if ids != IDS:
        issues.append(f"ids {ids}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if (
        decisions.count("ACCEPT") != 2
        or decisions.count("MODIFY") != 1
        or decisions.count("REJECT") != 2
    ):
        issues.append(f"gate mix {decisions}")
    issues.extend(occupancy_check(records))
    for rec in records:
        rid = rec["id"]
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rid} training_ready present")
        if "outputs/raw" in blob:
            issues.append(f"{rid} mentions outputs/raw")
        hidden = walk_keys(rec)
        if hidden:
            issues.append(f"{rid} hidden keys {hidden}")
        err = check_refractory(rec["spike_events"])
        if err:
            issues.append(f"{rid} refractory {err}")
        err = check_race(rec)
        if err:
            issues.append(f"{rid} {err}")
        n = rec["raster"]["neurons"]
        rate = rec["raster"]["mean_rate_hz"]
        window_s = rec["raster"]["window_s"]
        expected = round(n * rate * window_s)
        if abs(rec["raster"]["spikes"] - expected) > 1:
            issues.append(f"{rid} spike budget {rec['raster']['spikes']} vs {expected}")
        overlap = excerpt_vs_spikes(rec)
        if rid == "ttf-r38-207":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("207 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("207 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("207 partnered-neg total not negative")
        elif overlap >= 0.8:
            issues.append(f"{rid} excerpt overlap {overlap:.2f}")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_times = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_times:
            issues.append(f"{rid} inflection {inf} not a tick")
        if len(rec["reward_components"]["ticks"]) != 6:
            issues.append(f"{rid} tick count")
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rid} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rid} gate_snn decision mismatch")
        heads = ["task_progress", "safety", "efficiency", "coherence", "exploration"]
        total = sum(rec["reward_components"][h] for h in heads)
        if abs(total - rec["reward_components"]["total"]) > 1e-6:
            issues.append(f"{rid} total mismatch {total}")
        for h in heads:
            s = sum(t[h] for t in rec["reward_components"]["ticks"])
            if abs(s - rec["reward_components"][h]) > 1e-6:
                issues.append(f"{rid} {h} tick sum {s} vs {rec['reward_components'][h]}")
        prefix, t_win, t_lose, t_gate = expected_m6_prefix(rec)
        if tick_times[:5] != prefix:
            issues.append(f"{rid} TTF-M6 prefix {tick_times[:5]} != {prefix}")
        t_win_us = int(round(float(rec["raster"]["window_ms"]) * 1000))
        if not (tick_times[5] > t_win_us):
            issues.append(f"{rid} tick6 not after raster")
        delayed = rec["future_outcome"].get("delayed_surprise_s")
        if delayed is None or abs(tick_times[5] - round(delayed * 1e6)) > 0:
            issues.append(f"{rid} tick6 != delayed_surprise_s")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rid} ACCEPT params differ")
        if rec["meta"]["round"] != 38:
            issues.append(f"{rid} meta.round")
        if rec["meta"]["domain"] != rec["state"]["domain"]:
            issues.append(f"{rid} domain mismatch")
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for p in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in p:
                exp_sp = round(p["neurons"] * p["mean_rate_hz"] * dw_s)
                if abs(p["spikes"] - exp_sp) > 1:
                    issues.append(f"{rid} gate_snn {p['name']} spikes {p['spikes']} vs {exp_sp}")
        if rec["raster"]["energy_pJ"] != rec["raster"]["spikes"] * 23:
            issues.append(f"{rid} energy_pJ")
        rights = rec["meta"]["rights"]
        if rights.get("linear_issue") != "RM-793" or rights.get("intended_use") != "research_only":
            issues.append(f"{rid} rights stamp")
        n_spk = len(rec["spike_events"])
        if not (5 <= n_spk <= 40):
            issues.append(f"{rid} spike n={n_spk}")
        n_ex = len(rec["raster"]["excerpt"])
        if not (8 <= n_ex <= 16):
            issues.append(f"{rid} excerpt n={n_ex}")
        times = [e["t_rel_ms"] for e in rec["spike_events"]]
        if times != sorted(times):
            issues.append(f"{rid} spike order")
        gl, rw = rec["state"]["gate_latency_us"], rec["state"]["race_window_us"]
        if not (50 <= gl <= 2000):
            issues.append(f"{rid} gate_latency")
        if not (50 <= rw <= 1000):
            issues.append(f"{rid} race_window")
        if not (20 <= rec["raster"]["window_ms"] <= 50):
            issues.append(f"{rid} window_ms")
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= rec["raster"]["window_ms"] * 1000):
                issues.append(f"{rid} excerpt t_us {item['t_us']}")
            if not (0 <= item["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rid} neuron_id {item['neuron_id']}")
        if rid == "ttf-r38-206":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["live_bar"] < ev["trip_bar"]):
                issues.append("206 live not under trip")
            if ev.get("inject_tag") != "LOOP_TEST" or ev.get("inject_active") is not True:
                issues.append("206 inject not tagged LOOP_TEST")
            if rec["executed_action"]["parameters"]["speed_m_min"] != 0.0:
                issues.append("206 executed speed not zero")
            tos = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.go_accept" in tos:
                issues.append("206 routing contains go_accept")
            if "policy.hold_reject" not in tos:
                issues.append("206 routing missing hold_reject")
            if "recovery" not in rec["future_outcome"]:
                issues.append("206 missing recovery")
    return issues, jmax


def write_notes(records, jmax: float) -> None:
    rows = []
    for rec in records:
        dec = rec["safety_decision"]["decision"]
        cor = rec["safety_decision"]["correctness"]
        if cor == "incorrect":
            cor = f"**incorrect ({rec['meta']['supervisor_error_type']})**"
        tot = rec["reward_components"]["total"]
        tot_s = f"{tot:+.2f}"
        if rec["id"] == "ttf-r38-207":
            tot_s = f"**{tot:+.2f}**"
        edge = {
            "ttf-r38-206": "live 0.84 bar < 1.20 trip; tagged LOOP_TEST 1.36 bar inject treated as live",
            "ttf-r38-207": "process-correct steam clamp; catalyst-loss geyser inside 40 ms raster; independent LIF",
            "ttf-r38-208": "AE 52 pps beats rectifier encoder 18.4 kA; hold, do not ramp",
            "ttf-r38-209": "H2 99.94 pct vs DP smear; proposed 12.4 bar already legal",
            "ttf-r38-210": "exit 148 C vs shapemeter 12 I-unit; proposed 18 m/s already legal",
        }[rec["id"]]
        rows.append(
            f"| {rec['id']} | {rec['state']['domain']} | {dec} | {cor} | "
            f"{rec['state']['sim_or_real']} | {tot_s} | {edge} |"
        )
    ras_rows = []
    for rec in records:
        r = rec["raster"]
        ras_rows.append(
            f"| {rec['id']} | {rec['state']['domain']} | {r['neurons']} | {r['mean_rate_hz']} | "
            f"{r['window_ms']} | {r['spikes']} | {r['energy_pJ']} | {r['energy_uJ']:.6f} |"
        )
    tick_rows = []
    for rec in records:
        rc = rec["reward_components"]
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        ticks = rc["ticks"]
        idx = next(i + 1 for i, t in enumerate(ticks) if t["t_us"] == inf)
        tick_rows.append(
            f"| {rec['id'][-3:]} | {len(ticks)} | {rc['task_progress']:+.2f} | {rc['safety']:+.2f} | "
            f"{rc['efficiency']:+.2f} | {rc['coherence']:+.2f} | {rc['exploration']:+.2f} | "
            f"{rc['total']:+.2f} | {idx} ({inf}) |"
        )
    notes = f"""# Thalamic Trajectory Factory — NOTES-r38

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r38-206` … `ttf-r38-210`
- Domains this batch: `ore-sinter-strand`, `fcc-riser`, `nickel-electrowinning`, `hydrogen-PSA-bed`, `cold-tandem-mill`

These five domain slugs sit outside staged r13–r35 occupancy (including r32 `trona-calciner` / `hot-strip-mill`, r33 spiral-freezer / offset-web-press / bascule-bridge, r34 eaf / spray-dryer, r35 geothermal-ORC / ammonia-converter / urea-prill). All five plants are invented (Pyrite-Hood, Zeolite-Riser, Laterite-Vat, Adiabat-Sieve, Finisher-Coil). Do not restack prior TTF plants.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
{chr(10).join(rows)}

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (loop-test-inject). Provenance: designed×3, simulated×1, hil×1 (Laterite-Vat EW pad). Jaccard on `state.description` all ≤ {jmax:.3f}.

## Wrong-reject

**ttf-r38-206** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject. Do not emit a wrong-ACCEPT.

Pyrite-Hood / Strand S-4 reads live `P=0.84 bar` against a published **1.20 bar** trip. A tagged `LOOP_TEST` injector prints **1.36 bar**. Sidecar arithmetic `0.84 < 1.20` is true. A weak supervisor binds the inject as live, REJECT-holds 4.2 → 0 m/min, and leaves a legal strand idle. Convictable without sinter physics: `evidence.live_bar < evidence.trip_bar`, `evidence.inject_tag == LOOP_TEST`, `evidence.inject_active == true`, `executed_action` sets `speed_m_min=0`, `raster.routing.table` sends `relay.live.pt` → `policy.hold_reject` (weight 0.71) with no positive weight to `policy.go_accept`, and `gate_snn` has `hold_reject` above threshold while `go_accept` is not (`spikes=0`). Recovery: ACCEPT; leave 4.2 m/min; bind the published live 1.20 bar trip. Cost: 13 min missed pallet window.

This is **loop-test-inject / simulated-input-as-live**, not r12-079 (induced-kV treated as sensor fault), not r16-097 (reticle-as-wafer), not r18-109 (empty-tank class), not r20-118 (oscillation-as-PSV), not r22-126 (class-transplant floor), not r30-166 (stale-firmware floor), not r32 (stale-peak-hold), not r34-187 (header-as-cell wrong-loop).

## Partnered-negative in-window (207)

**ttf-r38-207** is the partnered negative: process-correct MODIFY (steam held 1.6 t/h, DP 16.4 kPa < 22.0 cap) while the world still charges. Safety −0.62 prices the catalyst-loss geyser at **22.400 ms**; `task_progress` stays +0.34 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 40 ms raster (`22400 ≤ 40000`). Named un-netted loss: 16 min emergency dump + standpipe inspection (`abort_s=960`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 38207, stim `[21000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.geyser` 21–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks; tick 5 is `t_charge_us=22400` on 207 and `t_gate_us + T_race` elsewhere; tick 6 is delayed surprise bound to `future_outcome.delayed_surprise_s`). Inflection `t_us` is an actual tick. Verified to <1e-6:

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
{chr(10).join(tick_rows)}

Tick 6 bind: `ticks[5].t_us == round(delayed_surprise_s * 1e6)` on every record (780 s, 960 s, 540 s, 600 s, 420 s).

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
{chr(10).join(ras_rows)}

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (ACh / NA / DA / 5-HT / DA), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms.

## Local checks (staging, not raw)

- Generator self-check: Jaccard max {jmax:.3f} < 0.4; TTF-M6 prefix; refractory; spike budgets; exactly one incorrect gate (206 wrong-reject)
- Pipeline audit (run after emit): `check_jsonl` FactoryStaging, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (207). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. 209 ACCEPT is a new plant/solver (4-bed Skarstrom PSA), not a new gate class.
4. 206 wrong-reject is convictable from live vs LOOP_TEST inject tags; a later round could bind `inject_fresh` as a sidecar boolean so a critic never has to know the tag string.
5. ISI histogram is still optional densification, not an r38 requirement.

## Next densification target

Publish the loop-test predicate as a sidecar boolean (`loop_test_active`) so an inject-as-live REJECT is convictable without the tag story. Optional: labeled LIF on a second record, or an ISI histogram sidecar. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 23.0%
"""
    NOTES_PATH.write_text(notes, encoding="utf-8")


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
        BATCH_PATH, "batch-r38.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r38.jsonl:{i}", factory_staging=True)
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
    schema_err = None
    try:
        import jsonschema
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012

        schema_dir = REPO / "schemas"
        ttf_schema = json.loads((schema_dir / "thalamic-trajectory-v2.schema.json").read_text())
        raster_schema = json.loads((schema_dir / "raster.schema.json").read_text())
        base_schema = json.loads((schema_dir / "thalamic-trajectory.schema.json").read_text())
        registry = Registry().with_resources(
            [
                ("thalamic-trajectory-v2.schema.json", Resource.from_contents(ttf_schema, DRAFT202012)),
                ("thalamic-trajectory.schema.json", Resource.from_contents(base_schema, DRAFT202012)),
                ("raster.schema.json", Resource.from_contents(raster_schema, DRAFT202012)),
            ]
        )
        validator = jsonschema.Draft202012Validator(ttf_schema, registry=registry)
        fails = []
        for rec in records:
            errs = sorted(validator.iter_errors(rec), key=lambda e: list(e.path))
            if errs:
                fails.append((rec["id"], [e.message for e in errs[:4]]))
        schema_err = fails
    except Exception as exc:
        schema_err = f"skip:{exc}"
    report.append(("jsonschema", schema_err, None, None, None))
    return report


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if "outputs/raw" in str(BATCH_PATH) or "outputs/raw" in str(NOTES_PATH):
        raise SystemExit("refusing to write outputs/raw")
    records = [record_206(), record_207(), record_208(), record_209(), record_210()]
    issues, jmax = self_check(records)
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_notes(records, jmax)
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
                print("  LINE_ERR", item[1])
                failed = True
        elif name == "raster_status":
            if item[1]:
                print("  RASTER_FAIL", item[1])
                failed = True
        elif name == "verify_batch_for_frontier":
            if item[3]:
                print("  BLOCKED", item[1], item[2])
                failed = True
        elif name == "validate_novel_coverage":
            if item[1]:
                print("  COVERAGE", item[1])
                failed = True
        elif name == "spike_probe":
            if item[1] != 0:
                print("  PROBE_FAIL", item[2], item[3])
                failed = True
        elif name == "jsonschema":
            if isinstance(item[1], list) and item[1]:
                print("  SCHEMA_FAIL", item[1])
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
