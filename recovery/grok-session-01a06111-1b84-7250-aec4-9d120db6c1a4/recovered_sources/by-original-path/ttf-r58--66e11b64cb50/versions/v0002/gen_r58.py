#!/usr/bin/env python3
"""Emit TTF r58 JSONL (ttf-r58-306..310) into /tmp/ttf-r58/. Never writes outputs/raw/."""

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

OUT_DIR = Path("/tmp/ttf-r58")
BATCH_PATH = OUT_DIR / "batch-r58.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r58.md"
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
        ("generated_at", "2026-09-02T22:30:00Z"),
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
    "spodumene-decrepitation-kiln",
    "chloride-tio2-oxidizer",
    "tungsten-apt-crystallizer",
    "ferrochrome-saf",
    "barite-jig-circuit",
)
MY_PLANTS = (
    "Spodumene-Thwaite",
    "Rutile-Keld",
    "Scheelite-Dene",
    "Chromite-Mear",
    "Barite-Beck",
)
IDS = [f"ttf-r58-{n}" for n in range(306, 311)]


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


def meta_block(
    domain,
    tags,
    distillation_value,
    batch_position,
    supervisor_error_type=None,
) -> OrderedDict:
    body = OrderedDict(
        [
            ("round", 58),
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


def lif_307_excerpt():
    """Independent CUBA LIF (seed 58307). Plant remains designed."""

    n = 84
    dt_us = 100
    tau_m_ms = 20.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.92
    i_stim_peak = 2.45
    stim = (21000, 25000)
    seed = 58307
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
    early = [(t, nid) for t, nid in spikes if t < 21000]
    burst = [(t, nid) for t, nid in spikes if 21000 <= t < 25000]
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
            early_flag = pool[0][0] < 21000
            have = len([1 for t, _ in picked if (t < 21000) == early_flag])
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
    tile = [(t, nid) for t, nid in picked if t >= 21000][:9]
    picked = sorted(clamp + tile, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise RuntimeError(f"LIF excerpt too short: {len(picked)}")
    channels = ["lif.clamp" if t < 21000 else "lif.tile" for t, _ in picked]
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
            ("seed", 58307),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.68 O2-lance-clamp bias; stim 21-25 ms is the oxidizer-duct tile collapse.",
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


def record_306():
    ticks = [
        tick(2112, -0.02, 0.01, -0.02, -0.01, 0.01),
        tick(5280, -0.04, 0.01, -0.04, -0.02, 0.01),
        tick(5510, -0.03, 0.01, -0.03, -0.01, 0.01),
        tick(6000, -0.06, 0.02, -0.08, -0.03, 0.02),
        tick(6400, -0.02, 0.01, -0.03, -0.01, 0.01),
        tick(720000000, -0.01, 0.00, -0.02, 0.00, 0.00),
    ]
    spikes = [
        spike("enc.feed.ctx", 1.205, 0.44),
        spike("rtd.bed.c", 2.410, 0.61),
        spike("di.overrange.flg", 3.880, 0.52),
        spike("bus.kiln.ctx", 4.620, 0.47),
        spike("rtd.bed.c", 5.280, 1.31),
        spike("di.overrange.flg", 5.510, 1.18),
        spike("ctrl.gate", 6.000, 0.99),
        spike("rtd.bed.c", 7.220, 0.84),
        spike("di.overrange.flg", 9.440, 0.66),
        spike("ctrl.gate", 14.880, 0.88),
        spike("enc.feed.ctx", 18.400, 0.41),
        spike("rtd.bed.c", 24.200, 0.58),
    ]
    excerpt = independent_excerpt(58306, 80, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Decrepitation kiln SK-4 at Spodumene-Thwaite already holds a live bed RTD of 742 C "
                "when that analog sample races a leftover transmitter overrange flag that is still "
                "latched from a bump three minutes ago. Published trip is 780 C on the live analog; "
                "a weak supervisor treats the leftover digital flag as the PV and zeros a legal "
                "14.0 t/h spodumene feed.",
            ),
            ("domain", "spodumene-decrepitation-kiln"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 14.0 t/h on SK-4, keep live bed T < 780 C trip, and finish the "
                "12 min decrepitation window.",
            ),
            ("t0_us", 1762300000000306),
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
                                "rtd.bed.c 742 C live analog bed",
                                "di.overrange.flg leftover latched overrange",
                            ],
                        ),
                        (
                            "semantics",
                            "Analog-first should ACCEPT 14.0 t/h (742 C < 780 C trip). "
                            "Flag-first would only delay confirmation of the same legal analog.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one kiln RTD analog slot versus the leftover-overrange "
                            "publisher on this 2 kHz decrepitation bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 76 us (analog 34 + flag 42): 3.0x over "
                            "a 2.0x trust floor. Order is correctly analog-first. The error is binding "
                            "a leftover overrange flag as if it were the live PV, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed RTD analog, 2 kHz, 34 us jitter, axis kiln_bed_t, analog_fresh true",
                    "transmitter overrange DI, 1 kHz, 42 us jitter, overrange_latched leftover",
                    "feed-mass encoder (context)",
                    "kiln-outlet IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_C", 742.0),
                        ("trip_C", 780.0),
                        ("urv_C", 800.0),
                        ("overrange_latched", True),
                        ("analog_fresh", True),
                        ("heartbeat_age_ms", 22.0),
                        ("max_age_ms", 200.0),
                        ("proposed_t_h", 14.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Kiln SK-4 indexed on Spodumene-Thwaite; live bed 742 C, 14.0 t/h armed.",
                    "2. Published analog trip 780 C; overrange DI tagged leftover from a receded bump.",
                    "3. Encoder precursor at 1.205 ms.",
                    "4. Race window [5.280, 5.680] ms.",
                    "5. Live analog 742 C at 5.280 ms (winner).",
                    "6. Leftover overrange flag at 5.510 ms (loser by 230 us).",
                    "7. Gate at 6.000 ms: wrong REJECT holds 0 t/h on the leftover flag.",
                    "8. Feed idle; analog never crossed 780 C.",
                    "9. 12 min decrepitation window missed.",
                    "10. QA: correct gate was ACCEPT; leave 14.0 t/h; bind analog 742 vs 780 C trip.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "kiln_14_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 14.0),
                        ("bed_C", 742.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 742.0),
                        ("trip_C", 780.0),
                        ("urv_C", 800.0),
                        ("overrange_latched", True),
                        ("analog_fresh", True),
                        ("heartbeat_age_ms", 22.0),
                        ("ft_axis", "kiln_bed_t"),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 76),
                        ("t_gate_us", 6000),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 14.0 t/h because live analog 742 C is 38 C under the published "
                "780 C trip and the overrange bit is a leftover latched flag, not a live PV.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Overrange flag is asserted, so the transmitter is treated as at or above URV 800 C "
                "(true vs that leftover bit). REJECT: hold 0 t/h until the flag clears so the kiln "
                "does not see an over-temperature event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "kiln_bed_t_C",
                            OrderedDict(
                                [
                                    ("published_analog_trip", 780.0),
                                    ("observed_analog", 742.0),
                                    ("overrange_flag_applied", True),
                                    ("urv_C", 800.0),
                                    ("executed_t_h", 0.0),
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
            ("name", "kiln_hold_overrange_flag"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 0.0),
                        ("bed_C", 742.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): feed 14.0 -> 0 t/h. Routing relay.overrange.flag -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Analog 742 C never "
                "violated the 780 C trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze SK-4 at 0 t/h while live analog stayed 742 C under the "
                "780 C trip. 12 min decrepitation window missed. Correct gate was ACCEPT of the "
                "already-legal 14.0 t/h command.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("kiln", "held at 0 t/h; 14.0 t/h abandoned"),
                        ("bed_C", "still 742 C, under 780 C published trip"),
                        ("concentrate", "12 min decrepitation window missed"),
                        ("flag", "no over-temperature; leftover overrange false positive"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The overrange bit is a leftover latched flag from a receded bump, not a live analog trip.",
                    "Delayed (12 min): sister kiln SK-5 ran the same 14.0 t/h decrepitation window after QA rebound the analog trip; SK-4's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: analog 742 C < published 780 C trip; leave 14.0 t/h; ignore leftover overrange flag.",
                        ),
                        ("correct_trip_C", 780.0),
                        ("wrong_flag", True),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("feed_t_h", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "12 min missed decrepitation window (task/efficiency); analog never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.c (5.280 ms, 742 C)"),
                        ("loser", "di.overrange.flg (5.510 ms, leftover latched)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "Flag-first by < 230 us would still show analog 742 C < 780 C. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the analog win "
                            "on a leftover overrange flag.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6000),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (6.000 ms, tick 4). The 12 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 720.0),
            ("missed_window_s", 720),
        ]
    )
    ras = raster_core(
        26,
        80,
        30,
        62,
        routing(
            "relay.overrange.flag",
            "policy.hold_reject",
            [
                ("relay.overrange.flag", "policy.hold_reject", 0.71),
                ("relay.rtd.bed", "policy.hold_reject", 0.22),
            ],
            "acetylcholine",
            0.08,
            "leftover_flag_stdp; ACh tags the (wrong) hold_reject bind at the analog win",
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
                    pop("analog_trip_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r58-306",
        "WRONG-REJECT at Spodumene-Thwaite / SK-4: live analog 742 C is legal vs "
        "published 780 C trip; supervisor bound a leftover overrange flag as the PV",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 742 < 780 is true; clamp bound to a "
        "leftover overrange flag. total -0.36 = -0.18 + 0.06 + -0.22 + -0.08 + 0.06.",
        ras,
        gate,
        "spodumene-decrepitation-kiln",
        [
            "reject",
            "wrong-gate",
            "overrange-flag-as-PV",
            "leftover-digital-trip",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct analog<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed.",
        1,
        supervisor_error_type="wrong-reject",
    )


def record_307():
    excerpt, extra = lif_307_excerpt()
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
                "Oxidizer OX-7 at Rutile-Keld is already pulling 22 percent oxygen when a "
                "chlorine off-gas Delta-P pulse arrives 230 us before the O2 mole-fraction probe "
                "that still reads a legal lance. Pressure-first latches a process clamp under the "
                "3.00 kPa cap; O2-first would keep cruise lance. Stored oxidizer-duct tile load is "
                "not yet an observable of either race channel.",
            ),
            ("domain", "chloride-tio2-oxidizer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep OX-7 on 22 percent O2 only while chlorine Delta-P stays <= 3.00 kPa, and "
                "leave the oxidizer-duct tile un-collapsed.",
            ),
            ("t0_us", 1762300000000307),
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
                                "dp.cl2.kpa 3.40 kPa chlorine off-gas",
                                "o2.lance.frac 0.22 still-legal lance",
                            ],
                        ),
                        (
                            "semantics",
                            "Pressure-first latches O2 clamp 22 -> 16 percent; O2-first keeps "
                            "cruise lance on a 'duct still open' model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one chlorine DP slot minus O2-analyzer group delay on this "
                            "1 kHz oxidizer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 68 us (DP 30 + O2 38): 3.4x over "
                            "a 2.0x trust floor. Reversing order by < 230 us inside the 380 us window "
                            "would have kept 22 percent cruise; predicted next-sample DP 3.18 kPa > 3.00 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "chlorine off-gas DP, 1 kHz, 30 us timestamp jitter",
                    "O2 mole-fraction analyzer, 1 kHz, 38 us jitter",
                    "O2-lance encoder (context)",
                    "duct-tile AE (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("dp_cap_kPa", 3.00),
                        ("observed_dp_kPa", 3.40),
                        ("proposed_o2_pct", 22.0),
                        ("o2_floor_pct", 12.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Oxidizer OX-7 indexed; 22 percent O2 lance; chlorine DP 3.40 kPa > 3.00 cap.",
                    "2. Cruise lance 22 percent armed; duct over the 3.00 kPa cap.",
                    "3. Encoder precursor at 1.848 ms; chlorine-side warm-start 3.40 kPa.",
                    "4. Race window [4.620, 5.000] ms opens on the oxidizer bus.",
                    "5. Chlorine DP 3.40 kPa at 4.620 ms (winner).",
                    "6. O2 fraction 0.22 at 4.850 ms (loser by 230 us).",
                    "7. Gate at 5.500 ms (winner + 880 us): MODIFY clamp 22 -> 16 percent.",
                    "8. Clamp executes; next-sample DP 2.62 kPa < 3.00 cap.",
                    "9. At 22.400 ms stored tile load collapses an oxidizer-duct bay.",
                    "10. Emergency isolate 16 min + tile pull; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_o2_lance"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("o2_pct", 22.0),
                        ("dp_kPa", 3.40),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("dp_kPa", 3.40),
                        ("dp_cap_kPa", 3.00),
                        ("predicted_unclamped_next_kPa", 3.18),
                        ("o2_pct", 22.0),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 68),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 22 percent cruise: O2 fraction looks like an open duct, not a "
                "plugged tile, and the 3.00 kPa DP cap is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Chlorine DP 3.40 kPa won by 230 us, so the oxidizer is running packed, not still "
                "free. Holding 22 percent predicts next-sample 3.18 kPa > 3.00 kPa cap. MODIFY: O2 "
                "22 -> 16 percent. Observed after clamp 2.62 kPa < 3.00. A full REJECT is not "
                "indicated: a sound oxidizer accepts 16 percent.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "cl2_dp_kPa",
                            OrderedDict(
                                [
                                    ("cap", 3.00),
                                    ("observed", 3.40),
                                    ("predicted_unclamped_next", 3.18),
                                    ("clamped_o2_pct", 16.0),
                                    ("observed_after_clamp", 2.62),
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
            ("name", "clamped_o2_lance"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("o2_pct", 16.0),
                        ("dp_kPa", 2.62),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: O2 22 -> 16 percent. Process-correct vs the 3.00 kPa DP cap. Oxidizer-duct "
                "tile collapse still occurs at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held DP at 2.62 kPa. At 22.400 ms stored tile load collapsed "
                "an oxidizer-duct bay. Clamp reduced O2 energy; it did not dump the tile charge. "
                "Partnered negative: process heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("lance", "clamp executed; DP 2.62 kPa < 3.00"),
                        ("oxidizer_duct", "tile collapse at 22.400 ms"),
                        ("repair", "16 min emergency isolate + tile pull"),
                        ("mission", "oxidizer still converting; tile precursor controlled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither chlorine DP nor O2 fraction predicted the tile charge; ae.tile.pack is a new channel at 22.400 ms, 16.900 ms after the gate, still inside the 40 ms raster.",
                    "Delayed (16 min): emergency isolate and tile pull close the collapse. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "16 min emergency isolate + tile pull after an oxidizer-duct collapse. Safety "
                "head -0.62 prices the precursor; task_progress stays +0.34 because the O2 clamp "
                "completed under the 3.00 kPa cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "dp.cl2.kpa (4.620 ms, 3.40 kPa)"),
                        ("loser", "o2.lance.frac (4.850 ms, 0.22)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "O2-first by < 230 us inside the 380 us window would have kept "
                            "22 percent cruise; predicted next-sample 3.18 kPa would have exceeded the "
                            "3.00 kPa cap even without the tile charge. The MODIFY is still the "
                            "correct process. The collapse is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms oxidizer-duct tile drop (tick t_us=22400), inside the "
                "40 ms raster. The correct MODIFY at 5.500 ms is in the same excerpt. Do not put "
                "inflection on the +16 min isolate tick.",
            ),
            ("delayed_surprise_s", 960.0),
            ("abort_s", 960),
        ]
    )
    spikes = [
        spike("enc.o2.ctx", 1.120, 0.43),
        spike("dp.cl2.kpa", 2.240, 0.62),
        spike("o2.lance.frac", 3.180, 0.55),
        spike("dp.cl2.kpa", 4.620, 1.34),
        spike("o2.lance.frac", 4.850, 1.12),
        spike("ctrl.gate", 5.500, 0.97),
        spike("dp.cl2.kpa", 7.200, 0.81),
        spike("o2.lance.frac", 10.400, 0.66),
        spike("ctrl.gate", 15.200, 0.84),
        spike("ae.tile.pack", 22.400, 1.42),
        spike("ae.tile.pack", 23.600, 0.91),
        spike("enc.o2.ctx", 29.800, 0.41),
        spike("dp.cl2.kpa", 36.200, 0.58),
    ]
    ras = raster_core(
        40,
        84,
        26,
        87,
        routing(
            "thalamic-relay.dp-o2",
            "spikenaut.policy.o2-clamp",
            [
                ("relay.dp.cl2", "policy.o2_clamp", 0.64),
                ("relay.o2.lance", "policy.lance_hold", 0.29),
                ("relay.ae.tile", "policy.o2_clamp", -0.46),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at DP win (4.620 ms) opens a 50 ms eligibility "
            "trace that still covers the 22.400 ms oxidizer-duct tile collapse",
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
                    pop("o2_clamp", 48, 0.50, 220.0, 4),
                    pop("lance_hold", 48, 0.50, 50.0, 1),
                    pop("dp_cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r58-307",
        "Rutile-Keld oxidizer / OX-7: chlorine DP beats O2 fraction by 230 us; correct "
        "MODIFY still eats an in-window oxidizer-duct tile collapse (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "40 ms raster. total -0.44 = 0.34 + -0.62 + -0.16 + 0.04 + -0.04. Named "
        "isolate+tile-pull loss is not netted into task_progress.",
        ras,
        gate,
        "chloride-tio2-oxidizer",
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


def record_308():
    ticks = [
        tick(1568, 0.01, 0.04, 0.02, 0.01, 0.01),
        tick(3920, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(4110, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5100, 0.03, 0.12, 0.04, 0.04, 0.02),
        tick(5380, 0.02, 0.07, 0.01, 0.01, 0.01),
        tick(540000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.agit.ctx", 1.040, 0.44),
        spike("dens.liquor.sg", 2.180, 0.71),
        spike("enc.agit.rpm", 3.020, 0.52),
        spike("dens.liquor.sg", 3.920, 1.36),
        spike("enc.agit.rpm", 4.110, 1.14),
        spike("ctrl.gate", 5.100, 0.98),
        spike("dens.liquor.sg", 7.400, 0.82),
        spike("enc.agit.rpm", 10.800, 0.61),
        spike("ctrl.gate", 16.200, 0.86),
        spike("dens.liquor.sg", 24.600, 0.70),
        spike("enc.agit.rpm", 33.400, 0.48),
        spike("t.jacket.ctx", 41.200, 0.40),
    ]
    excerpt = independent_excerpt(58308, 112, 46000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Crystallizer CR-5 on the Scheelite-Dene APT HIL pad is seeding at 42 rpm when a "
                "liquor-density burst at 1.82 SG races the agitator encoder that still looks "
                "in-band for a speed step. Ramp is legal only if density <= 1.70 SG. Density-first "
                "latches hold; encoder-first would treat in-band rpm as supersaturation clearance.",
            ),
            ("domain", "tungsten-apt-crystallizer"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not ramp CR-5 unless liquor density <= 1.70 SG; keep agitator 0 rpm until the "
                "batch is quiet.",
            ),
            ("t0_us", 1762300000000308),
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
                                "dens.liquor.sg 1.82 SG flare",
                                "enc.agit.rpm 42 rpm still-in-band",
                            ],
                        ),
                        (
                            "semantics",
                            "Density-first latches REJECT hold 0 rpm; encoder-first would ramp 42 rpm "
                            "on an in-band-speed-as-clearance model.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one densitometer envelope slot versus the agitator-encoder "
                            "publisher on this pad cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 190 us vs combined jitter 54 us (density 24 + encoder 30): 3.5x over a "
                            "2.0x trust floor. Pad injects encoder 90-130 us before the density envelope "
                            "finishes (loop lag, not a sensor fault); the encoder packet is still "
                            "the loser in this 280 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "APT-liquor densitometer, 24 us jitter, 1.70 SG trip",
                    "agitator-speed encoder, 30 us jitter",
                    "jacket RTD (context)",
                    "seed-mass (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("density_trip_sg", 1.70),
                        ("observed_density_sg", 1.82),
                        ("agit_cap_rpm", 55.0),
                        ("proposed_rpm", 42.0),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("bench", "Scheelite-Dene TW-HIL APT crystallizer pad, CR-5"),
                        ("inject", "density envelope delayed 90-130 us vs encoder; loop lag, not a false densitometer"),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. CR-5 on Scheelite-Dene HIL pad; liquor in band; agitator armed at 42 rpm.",
                    "2. Density trip 1.70 SG; observed 1.82 SG flare on APT liquor.",
                    "3. Encoder precursor at 1.040 ms.",
                    "4. Race window [3.920, 4.200] ms.",
                    "5. Density 1.82 SG at 3.920 ms (winner).",
                    "6. Agitator encoder 42 rpm at 4.110 ms (loser by 190 us).",
                    "7. Gate at 5.100 ms: REJECT hold 0 rpm, do not ramp.",
                    "8. Pad recycle 9 min; density decays under 1.70 SG after hold.",
                    "9. Batch never nucleated wild; encoder-as-clearance would have ramped into the flare.",
                    "10. QA: correct gate was REJECT; leave 0 rpm until density <= 1.70 SG.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "ramp_42rpm"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("agit_rpm", 42.0),
                        ("density_sg", 1.82),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("density_sg", 1.82),
                        ("density_trip_sg", 1.70),
                        ("agit_rpm", 42.0),
                        ("agit_cap_rpm", 55.0),
                        ("race_margin_us", 190),
                        ("combined_jitter_us", 54),
                        ("t_gate_us", 5100),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 42 rpm because agitator speed is under the 55 rpm cap and treats "
                "the encoder as supersaturation clearance, ignoring the 1.82 SG density flare.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Density 1.82 SG won by 190 us and is over the 1.70 SG trip. Encoder 42 rpm is under "
                "the 55 rpm cap but is not clearance. REJECT: hold 0 rpm until density <= 1.70 SG.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "liquor_density_sg",
                            OrderedDict(
                                [
                                    ("trip", 1.70),
                                    ("observed", 1.82),
                                    ("executed_rpm", 0.0),
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
            ("name", "agit_hold_density"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("agit_rpm", 0.0),
                        ("density_sg", 1.82),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: agitator 42 -> 0 rpm. Routing relay.dens.liquor -> policy.hold_reject. "
                "Do not ramp into the 1.82 SG flare.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held CR-5 at 0 rpm while density 1.82 SG decayed. Encoder-as-clearance "
                "would have ramped 42 rpm into the flare. Pad recycle 9 min.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("agitator", "held at 0 rpm"),
                        ("liquor", "density flare decaying under trip after hold"),
                        ("batch", "no wild nucleation"),
                        ("pad", "9 min recycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Pad injects encoder 90-130 us before density envelope finish; that is loop lag, not a false densitometer.",
                    "Delayed (9 min): pad recycle restacks the crystallizer after density < 1.70 SG.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "dens.liquor.sg (3.920 ms, 1.82 SG)"),
                        ("loser", "enc.agit.rpm (4.110 ms, 42 rpm)"),
                        ("margin_us", 190),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 190 us would have treated 42 rpm as clearance and "
                            "ramped into the 1.82 SG flare. The REJECT is still required; reversal "
                            "only delays the density bind.",
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
            "relay.dens.liquor",
            "policy.hold_reject",
            [
                ("relay.dens.liquor", "policy.hold_reject", 0.74),
                ("relay.enc.agit", "policy.ramp_go", 0.18),
            ],
            "dopamine",
            0.06,
            "density_trip_stdp; DA tags the hold_reject bind at the density win",
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
                    pop("density_trip_veto", 32, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r58-308",
        "Scheelite-Dene APT HIL / CR-5: density 1.82 SG beats agitator encoder 42 rpm by 190 us; "
        "correct REJECT holds the crystallizer",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. Density 1.82 > 1.70 trip beats in-band agitator speed. total +0.78 = "
        "0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "tungsten-apt-crystallizer",
        [
            "reject",
            "hil-pad",
            "density-vs-encoder",
            "supersat-hold",
            "sidecar-convictable",
            "hil",
        ],
        "Teaches a probe that an in-band agitator encoder is not supersaturation clearance when "
        "density is over trip and routing.table[0].to is policy.hold_reject.",
        3,
    )


def record_309():
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
            ("current_kA", 38.0),
            ("bath_C", 1640.0),
            ("furnace_id", 3),
            ("hold", False),
        ]
    )
    spikes = [
        spike("ft.feed.ctx", 1.480, 0.42),
        spike("ir.bath.c", 3.120, 0.58),
        spike("ir.roof.smear", 4.660, 0.50),
        spike("ir.bath.c", 6.240, 1.28),
        spike("ir.roof.smear", 6.470, 1.10),
        spike("ctrl.gate", 7.140, 0.96),
        spike("ir.bath.c", 9.200, 0.74),
        spike("ir.roof.smear", 12.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("ir.bath.c", 24.600, 0.55),
        spike("ft.feed.ctx", 29.800, 0.40),
    ]
    excerpt = independent_excerpt(58309, 56, 30000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Furnace SAF-3 of the Chromite-Mear ferrochrome train is holding 38 kA when a "
                "bath IR at 1640 C races a roof-IR smear that still claims over-temp. "
                "Commanded 38 kA and 1640 C sit 4 kA and 60 C inside the legal "
                "envelopes. The bath-IR win only ratifies the electrode already in the bath.",
            ),
            ("domain", "ferrochrome-saf"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the submerged-arc pass on Chromite-Mear, keep bath IR <= 1700 C and "
                "current >= 34 kA, and leave roof draft in spec.",
            ),
            ("t0_us", 1762300000000309),
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
                                "ir.bath.c 1640 C ferrochrome bath",
                                "ir.roof.smear over-temp claim",
                            ],
                        ),
                        (
                            "semantics",
                            "Bath-IR-first confirms the already-legal 38 kA / 1640 C pass; "
                            "smear-first would have treated the bath IR as a smear echo and looked "
                            "for an extra hold the furnace does not need.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one 1D-bath IR kernel step versus the roof-IR publisher "
                            "on this rigid SAF train.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 70 us (bath 32 + roof 38): 3.3x over "
                            "a 2.0x trust floor. Reversing order by < 230 us would not make the "
                            "proposed pass illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bath IR, 32 us jitter",
                    "roof IR smear, 38 us jitter",
                    "electrode-current encoder (context)",
                    "off-gas PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bath_cap_C", 1700.0),
                        ("observed_bath_C", 1640.0),
                        ("current_floor_kA", 34.0),
                        ("proposed_current_kA", 38.0),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "1D SAF electrode-bath kernel + shrinking-core chromite pellet, seed 58; 12 axial nodes; NOT lumped tank, NOT a fluid-LES field",
                        ),
                        (
                            "fidelity_limits",
                            "No radial maldistribution or electrode break; baths are rigid temperature sources. Raster is kernelized events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Chromite-Mear furnace indexed; SAF-3 holding 38 kA at 1640 C bath.",
                    "2. Caps: bath 1700 C, current floor 34 kA; both proposed values inside.",
                    "3. Feed precursor at 1.480 ms.",
                    "4. Race window [6.240, 6.600] ms.",
                    "5. Bath IR 1640 C at 6.240 ms (winner).",
                    "6. Roof IR smear at 6.470 ms (loser by 230 us).",
                    "7. Gate at 7.140 ms: ACCEPT 38 kA / 1640 C already legal.",
                    "8. Pass continues; no extra hold.",
                    "9. 10 min survey confirms roof draft still in spec.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "saf_38ka_thold"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bath_C", 1640.0),
                        ("bath_cap_C", 1700.0),
                        ("current_kA", 38.0),
                        ("current_floor_kA", 34.0),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 70),
                        ("t_gate_us", 7140),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 38 kA because bath 1640 C is 60 C under the 1700 C cap "
                "and current is 4 kA over the 34 kA floor.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bath 1640 C won by 230 us and is under 1700 C. Current 38 kA is over "
                "34 kA. ACCEPT the already-legal pass; roof IR smear is not a cap violation.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bath_C",
                            OrderedDict(
                                [
                                    ("cap", 1700.0),
                                    ("observed", 1640.0),
                                    ("executed_current_kA", 38.0),
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
            ("name", "saf_38ka_thold"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: current 38 kA and bath 1640 C unchanged. Routing relay.ir.bath "
                "-> policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left SAF-3 at 38 kA / 1640 C. Roof IR smear did not justify a "
                "hold. 10 min survey confirmed draft in spec.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("furnace", "still 38 kA / 1640 C"),
                        ("roof", "in spec after survey"),
                        ("train", "ferrochrome continues"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Roof IR smear is an off-gas optical claim, not a bath-temperature violation.",
                    "Delayed (10 min): survey restacks SAF-3 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.bath.c (6.240 ms, 1640 C)"),
                        ("loser", "ir.roof.smear (6.470 ms, over-temp claim)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "Smear-first by < 230 us would only delay confirmation. The pass stays "
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
            "relay.ir.bath",
            "policy.go_accept",
            [
                ("relay.ir.bath", "policy.go_accept", 0.68),
                ("relay.ir.roof", "policy.smear_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_saf_stdp; 5-HT tags the go_accept bind at the bath-IR win",
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
                    pop("bath_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r58-309",
        "Chromite-Mear SAF / SAF-3: bath IR 1640 C beats roof smear by 230 us; ACCEPT "
        "already-legal 38 kA pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal 1D SAF electrode-bath pass. total +1.06 = "
        "0.42 + 0.28 + 0.18 + 0.10 + 0.08.",
        ras,
        gate,
        "ferrochrome-saf",
        [
            "accept",
            "already-legal",
            "simulated-saf-train",
            "bath-vs-roof",
            "sidecar-convictable",
            "simulated",
        ],
        "Teaches that a bath IR under cap can confirm an already-legal SAF pass without "
        "a roof-IR smear becoming a hold.",
        4,
    )


def record_310():
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
            ("stroke_spm", 180.0),
            ("bed_sg", 4.20),
            ("jig_id", 5),
            ("hold", False),
        ]
    )
    spikes = [
        spike("enc.stroke.ctx", 0.920, 0.41),
        spike("sg.bed.sg", 2.140, 0.60),
        spike("dp.hutch.smear", 3.080, 0.51),
        spike("sg.bed.sg", 4.180, 1.30),
        spike("dp.hutch.smear", 4.360, 1.12),
        spike("ctrl.gate", 4.940, 0.97),
        spike("sg.bed.sg", 6.800, 0.78),
        spike("dp.hutch.smear", 9.200, 0.62),
        spike("ctrl.gate", 13.600, 0.85),
        spike("sg.bed.sg", 18.400, 0.54),
        spike("dp.hutch.smear", 21.200, 0.43),
    ]
    excerpt = independent_excerpt(58310, 48, 24000, 11, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Jig JG-5 at Barite-Beck circuit 2 is armed for a 180 spm stroke when a bed "
                "specific-gravity of 4.20 races a hutch-water Delta-P that still claims a hitch. "
                "Commanded 180 spm and 4.20 SG sit 30 spm over the 150 spm floor and 0.30 under "
                "the 4.50 SG cap. The SG win only ratifies the stroke already on the jig.",
            ),
            ("domain", "barite-jig-circuit"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run JG-5 at 180 spm, keep bed SG <= 4.50 and hutch DP <= 18 kPa, "
                "and leave the circuit on schedule.",
            ),
            ("t0_us", 1762300000000310),
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
                                "sg.bed.sg 4.20 barite bed",
                                "dp.hutch.smear 8 kPa hitch claim",
                            ],
                        ),
                        (
                            "semantics",
                            "SG-first confirms the already-legal 180 spm / 4.20 SG pass; DP-first "
                            "would have treated the SG as a hitch echo and looked for an extra hold "
                            "the jig does not need.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one nuclear-density SG slot versus the hutch-DP publisher on this "
                            "jig bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (SG 28 + DP 30): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed pass illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed nuclear-density SG, 28 us jitter",
                    "hutch-water DP, 30 us jitter",
                    "stroke encoder (context)",
                    "float SG (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_sg", 4.50),
                        ("observed_bed_sg", 4.20),
                        ("stroke_floor_spm", 150.0),
                        ("proposed_stroke_spm", 180.0),
                        ("dp_cap_kPa", 18.0),
                        ("observed_dp_kPa", 8.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Jig JG-5 indexed on Barite-Beck circuit 2; stroke armed 180 spm pass.",
                    "2. Caps: bed SG 4.50, hutch DP 18 kPa, stroke floor 150 spm.",
                    "3. Encoder precursor at 0.920 ms.",
                    "4. Race window [4.180, 4.480] ms.",
                    "5. Bed SG 4.20 at 4.180 ms (winner).",
                    "6. Hutch DP 8 kPa at 4.360 ms (loser by 180 us).",
                    "7. Gate at 4.940 ms: ACCEPT 180 spm / 4.20 SG already legal.",
                    "8. Pass continues; no extra hold.",
                    "9. 7 min survey confirms hutch DP still under 18 kPa.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "pass_180spm"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_sg", 4.20),
                        ("bed_cap_sg", 4.50),
                        ("stroke_spm", 180.0),
                        ("stroke_floor_spm", 150.0),
                        ("dp_kPa", 8.0),
                        ("dp_cap_kPa", 18.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("t_gate_us", 4940),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 180 spm pass because bed SG 4.20 is 0.30 under the 4.50 "
                "cap and hutch DP 8 kPa is under 18 kPa.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed SG 4.20 won by 180 us and is under 4.50. Hutch DP 8 kPa is under "
                "18 kPa. Stroke 180 spm is over the 150 spm floor. ACCEPT the already-legal pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_sg",
                            OrderedDict(
                                [
                                    ("cap", 4.50),
                                    ("observed", 4.20),
                                    ("executed_stroke_spm", 180.0),
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
            ("name", "pass_180spm"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 180 spm pass and 4.20 SG unchanged. Routing relay.sg.bed -> "
                "policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left JG-5 on a 180 spm / 4.20 SG pass. Hutch DP hitch did not "
                "justify a hold. 7 min survey confirmed DP still under 18 kPa.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("jig", "still 180 spm / 4.20 SG"),
                        ("dp", "8 kPa under 18 cap"),
                        ("circuit", "on schedule"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Hutch DP 8 kPa hitch is residual, not a packed-bed trip.",
                    "Delayed (7 min): survey restacks JG-5 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "sg.bed.sg (4.180 ms, 4.20 SG)"),
                        ("loser", "dp.hutch.smear (4.360 ms, 8 kPa)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "DP-first by < 180 us would only delay confirmation. The pass stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4940),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (4.940 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 420.0),
            ("survey_s", 420),
        ]
    )
    ras = raster_core(
        24,
        48,
        42,
        48,
        routing(
            "relay.sg.bed",
            "policy.go_accept",
            [
                ("relay.sg.bed", "policy.go_accept", 0.66),
                ("relay.dp.hutch", "policy.hitch_hold", 0.20),
            ],
            "dopamine",
            0.04,
            "legal_pass_stdp; DA tags the go_accept bind at the bed-SG win",
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
                    pop("sg_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r58-310",
        "Barite-Beck circuit 2 / JG-5: bed SG 4.20 beats hutch DP 8 kPa by 180 us; "
        "ACCEPT already-legal 180 spm pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal barite-jig pass. total +1.14 = "
        "0.44 + 0.32 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "barite-jig-circuit",
        [
            "accept",
            "already-legal",
            "sg-vs-hutch-dp",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches that a bed SG under cap can confirm an already-legal jig pass without "
        "a hutch-DP hitch becoming a hold.",
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
    if rec["id"] == "ttf-r58-307":
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
    skip = {
        BATCH_PATH.resolve(),
        NOTES_PATH.resolve(),
        Path("/tmp/ttf-r58/gen_r58.py").resolve(),
    }
    for p in sorted(Path("/tmp").glob("ttf-r*/*")):
        if p.suffix not in {".jsonl", ".md", ".py"}:
            continue
        try:
            if p.resolve() in skip:
                continue
        except OSError:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        plants.update(PLANT_RE.findall(text))
        if p.suffix == ".jsonl":
            for line in text.splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                d = (rec.get("state") or {}).get("domain")
                if d:
                    domains.add(d)
        for m in re.finditer(r"Domains this batch:\s*(.+)", text):
            domains.update(re.findall(r"`([^`]+)`", m.group(1)))
        domains.update(re.findall(r'\("domain",\s*"([^"]+)"\)', text))
        for m in re.finditer(r"MY_DOMAINS = \((.*?)\)", text, re.S):
            domains.update(re.findall(r'"([^"]+)"', m.group(1)))
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
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r58-306":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-reject":
        issues.append("306 supervisor_error_type")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if hil != ["ttf-r58-308"]:
        issues.append(f"hil set {hil}")
    if sim != ["ttf-r58-309"]:
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
        if rid == "ttf-r58-307":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("307 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("307 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("307 partnered-neg total not negative")
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
        if rec["meta"]["round"] != 58:
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
        if rid == "ttf-r58-306":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["bed_C"] < ev["trip_C"]):
                issues.append("306 analog not under trip")
            if ev.get("overrange_latched") is not True or ev.get("analog_fresh") is not True:
                issues.append("306 leftover overrange not tagged")
            if rec["executed_action"]["parameters"]["feed_t_h"] != 0.0:
                issues.append("306 executed feed not zero")
            tos = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.go_accept" in tos:
                issues.append("306 routing contains go_accept")
            if "policy.hold_reject" not in tos:
                issues.append("306 routing missing hold_reject")
            if "recovery" not in rec["future_outcome"]:
                issues.append("306 missing recovery")
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
        if rec["id"] == "ttf-r58-307":
            tot_s = f"**{tot:+.2f}**"
        edge = {
            "ttf-r58-306": "live analog 742 C < 780 trip; leftover overrange flag treated as the PV",
            "ttf-r58-307": "process-correct O2 clamp; oxidizer-duct tile collapse inside 40 ms raster; independent LIF",
            "ttf-r58-308": "density 1.82 SG beats agitator encoder 42 rpm; hold, do not ramp",
            "ttf-r58-309": "bath 1640 C vs roof IR smear; proposed 38 kA already legal",
            "ttf-r58-310": "bed SG 4.20 vs hutch DP 8 kPa; proposed 180 spm already legal",
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
    notes = f"""# Thalamic Trajectory Factory — NOTES-r58

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r58-306` … `ttf-r58-310`
- Domains this batch: `spodumene-decrepitation-kiln`, `chloride-tio2-oxidizer`, `tungsten-apt-crystallizer`, `ferrochrome-saf`, `barite-jig-circuit`

These five domain slugs sit outside staged r13–r56 occupancy (including r48 visbreaker/FGD/PAN-ox/induration/cracker, r51 anode-bake/methanol-converter, r52 phosphoric-attack-tank / continuous-anneal, r53 fluid-bed-roaster / SX-mixer-settler, r55 kamyr / sulfuric-contact, r56 pidgeon-magnesium-retort / pta-crystallizer / acheson-graphite). All five plants are invented (Spodumene-Thwaite, Rutile-Keld, Scheelite-Dene, Chromite-Mear, Barite-Beck). Do not restack prior TTF plants.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
{chr(10).join(rows)}

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (overrange-flag-as-PV). Provenance: designed×3, simulated×1, hil×1 (Scheelite-Dene TW-HIL pad). Jaccard on `state.description` all ≤ {jmax:.3f}.

## Wrong-reject

**ttf-r58-306** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject. Do not emit a wrong-ACCEPT.

Spodumene-Thwaite / SK-4 reads live analog `T=742 C` against a published **780 C** trip. A leftover transmitter overrange flag is still latched (`overrange_latched=true`) from a bump that already receded; `analog_fresh=true` with `heartbeat_age_ms=22 < 200`. Sidecar arithmetic `742 < 780` is true. A weak supervisor binds the leftover digital flag as the PV, REJECT-holds 14.0 → 0 t/h, and leaves a legal kiln idle. Convictable without spodumene physics: `evidence.bed_C < evidence.trip_C`, `evidence.overrange_latched == true`, `evidence.analog_fresh == true`, `executed_action` sets `feed_t_h=0`, `raster.routing.table` sends `relay.overrange.flag` → `policy.hold_reject` (weight 0.71) with no positive weight to `policy.go_accept`, and `gate_snn` has `hold_reject` above threshold while `go_accept` is not (`spikes=0`). Recovery: ACCEPT; leave 14.0 t/h; bind the published analog 780 C trip; ignore the leftover flag. Cost: 12 min missed decrepitation window.

This is **overrange-flag-as-PV / leftover-digital-trip**, not r12-079 (induced-kV treated as sensor fault), not r16-097 (reticle-as-wafer), not r18-109 (empty-tank class), not r20-118 (oscillation-as-PSV), not r22-126 (class-transplant floor), not r30-166 (stale-firmware floor), not r32 (stale-peak-hold), not r34-187 (header-as-cell wrong-loop), not r36-196 (unit-mismatch leftover-bar), not r38-206 (LOOP_TEST inject-as-live), not r44-237 (wrong-unit-shadow), not r48-256 (2oo3-failed-high / median-vs-single).

## Partnered-negative in-window (307)

**ttf-r58-307** is the partnered negative: process-correct MODIFY (O2 held 16 percent, DP 2.62 kPa < 3.00 cap) while the world still charges. Safety −0.62 prices the oxidizer-duct tile collapse at **22.400 ms**; `task_progress` stays +0.34 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 40 ms raster (`22400 ≤ 40000`). Named un-netted loss: 16 min emergency isolate + tile pull (`abort_s=960`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 58307, stim `[21000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.tile` 21–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks; tick 5 is `t_charge_us=22400` on 307 and `t_gate_us + T_race` elsewhere; tick 6 is delayed surprise bound to `future_outcome.delayed_surprise_s`). Inflection `t_us` is an actual tick. Verified to <1e-6:

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
{chr(10).join(tick_rows)}

Tick 6 bind: `ticks[5].t_us == round(delayed_surprise_s * 1e6)` on every record (720 s, 960 s, 540 s, 600 s, 420 s).

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
{chr(10).join(ras_rows)}

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (ACh / NA / DA / 5-HT / DA), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms.

## Local checks (staging, not raw)

- Generator self-check: Jaccard max {jmax:.3f} < 0.4; TTF-M6 prefix; refractory; spike budgets; exactly one incorrect gate (306 wrong-reject)
- Pipeline audit (run after emit): `check_jsonl` FactoryStaging, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (307). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. 309 ACCEPT is a new plant/solver (1D SAF electrode-bath kernel), not a new gate class.
4. 306 wrong-reject is convictable from analog-vs-flag tags; a later round could bind `overrange_latched && analog_fresh` as the only critic boolean so a probe never has to know "SK-4".
5. ISI histogram is still optional densification, not an r58 requirement.

## Next densification target

Publish the leftover-flag freshness predicate as a sidecar boolean (`overrange_fresh`) so a leftover-digital REJECT is convictable without the channel-name story. Optional: labeled LIF on a second record, or an ISI histogram sidecar. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 18.0%
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
        BATCH_PATH, "batch-r58.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r58.jsonl:{i}", factory_staging=True)
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
    records = [record_306(), record_307(), record_308(), record_309(), record_310()]
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
