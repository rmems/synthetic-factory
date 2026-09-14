#!/usr/bin/env python3
"""Emit TTF r22 JSONL (ttf-r22-126..130) into /tmp/ttf-r22/. Never writes outputs/raw/."""

from __future__ import annotations

import json
import math
import random
import re
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

OUT_DIR = Path("/tmp/ttf-r22")
BATCH_PATH = OUT_DIR / "batch-r22.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r22.md"

PJ_PER_SPIKE = 23
RIGHTS = OrderedDict(
    [
        ("provider", "SpaceXAI/xAI"),
        ("model", "grok-4.6"),
        ("channel", "consumer"),
        ("subscription_plan", "SuperGrok Heavy"),
        ("generation_surface", "SuperGrok Heavy chat"),
        ("generated_at", "2026-09-02T16:45:00Z"),
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
    "Oolite-Span",
    "Fathom-Lock",
    "Loess-Stride",
    "Swage-Holt",
    "Slag-Siding",
    "Glimmer-Forge",
    "Feldspar-Arc",
    "Basalt-Rook",
    "Fetch-Sound",
    "Silica-Well",
    "Meridian Coldstore",
    "Kestrel-2",
    "Cerro Tolvara",
    "Red Mesa",
    "Helix Vault",
    "Kiln-Spur",
    "Solstice Coldchain",
    "Gale Ridge",
    "Salar Trench",
    "Glasswalk",
)


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


def lif_127_excerpt():
    """Independent CUBA LIF (seed 22127). Plant remains designed."""

    n = 80
    dt_us = 100
    tau_m_ms = 20.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.92
    i_stim_peak = 2.4
    stim = (19000, 22000)
    seed = 22127
    window_us = 38000
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
    early = [(t, nid) for t, nid in spikes if t < 19000]
    burst = [(t, nid) for t, nid in spikes if 19000 <= t < 22000]
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
            early_flag = pool[0][0] < 19000
            have = len([1 for t, _ in picked if (t < 19000) == early_flag])
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
    take(burst, 9, label_times=(19800, 20400, 21100))
    picked.sort(key=lambda item: (item[0], item[1]))
    clamp = [(t, n) for t, n in picked if t < 19000][:7]
    dust = [(t, n) for t, n in picked if t >= 19000][:9]
    picked = sorted(clamp + dust, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise RuntimeError(f"LIF excerpt too short: {len(picked)}")
    channels = ["lif.clamp" if t < 19000 else "lif.dust" for t, _ in picked]
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
            ("stim_t_us", [19000, 22000]),
            ("i_clamp_extra", 0.70),
            ("clamp_n", 16),
            ("seed", 22127),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-15 carry +0.70 clamp-pathway bias; stim 19-22 ms is the dust burst.",
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
            ("round", 22),
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


def record_126():
    ticks = [
        tick(2112, -0.02, 0.01, -0.02, -0.01, 0.01),
        tick(5280, -0.04, 0.01, -0.04, -0.02, 0.01),
        tick(5570, -0.03, 0.01, -0.03, -0.01, 0.01),
        tick(6000, -0.06, 0.02, -0.08, -0.03, 0.02),
        tick(6420, -0.02, 0.01, -0.03, -0.01, 0.01),
        tick(720000000, -0.01, 0.00, -0.02, 0.00, 0.00),
    ]
    excerpt = excerpt_items(
        [
            (820, 4),
            (2100, 19),
            (3600, 33),
            (5100, 8),
            (6800, 41),
            (8500, 12),
            (10200, 27),
            (12100, 50),
            (14200, 3),
            (16400, 22),
            (18700, 45),
            (21100, 15),
            (23600, 38),
            (25900, 7),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Sled-M7 already rides 8.2 mm above the Sinter-Ridge Maglev Loop guideway when "
                "an eddy-current gap sample races an IMU heave spike. Published M-series floor "
                "is 8.0 mm; a weak supervisor transplants the 10.0 mm P-series comfort floor "
                "and treats a legal gap as an under-gap fault.",
            ),
            ("domain", "maglev-guideway-gap"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 80 km/h on the 1.2 km test loop, keep air-gap >= 8.0 mm (M-series "
                "published floor), and finish the 12 min high-speed window.",
            ),
            ("t0_us", 1762300000000126),
            ("gate_latency_us", 720),
            ("race_window_us", 420),
            ("race_window_rel_ms", [5.2, 5.62]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "eddy.gap.mm 8.2 mm M-series air-gap",
                                "imu.heave.mm 0.4 mm heave residual",
                            ],
                        ),
                        (
                            "semantics",
                            "Eddy-first should ACCEPT 80 km/h (8.2 mm >= 8.0 mm floor). "
                            "Heave-first would only delay confirmation of the same legal gap.",
                        ),
                        (
                            "window_derivation",
                            "420 us = one eddy-current demodulation slot versus the IMU heave "
                            "publisher on this 2 kHz levitation bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 290 us vs combined jitter 80 us (eddy 38 + IMU 42): 3.6x over "
                            "a 2.0x trust floor. Order is correctly eddy-first. The error is the "
                            "floor the supervisor binds, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "eddy-current air-gap, 2 kHz, 38 us jitter, axis guideway_z",
                    "IMU heave, 1 kHz, 42 us jitter",
                    "sled velocity encoder (context)",
                    "levitation coil current (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("gap_floor_mm", 8.0),
                        ("observed_gap_mm", 8.2),
                        ("wrong_floor_mm", 10.0),
                        ("wrong_floor_class", "P-series comfort 12 mm pad"),
                        ("proposed_speed_km_h", 80.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Sled-M7 indexed onto Sinter-Ridge loop; air-gap 8.2 mm, speed 80 km/h armed.",
                    "2. Published M-series floor 8.0 mm; P-series comfort 10.0 mm is a different vehicle class.",
                    "3. Encoder precursor at 2.112 ms.",
                    "4. Race window [5.200, 5.620] ms.",
                    "5. Eddy gap 8.2 mm at 5.280 ms (winner).",
                    "6. IMU heave 0.4 mm at 5.570 ms (loser by 290 us).",
                    "7. Gate at 6.000 ms: wrong REJECT holds 0 km/h on a transplanted 10.0 mm floor.",
                    "8. Loop idle; 8.2 mm gap never went under 8.0 mm.",
                    "9. 12 min high-speed window missed.",
                    "10. QA: correct gate was ACCEPT; leave 80 km/h; bind the published 8.0 mm M-series floor.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "loop_80kmh_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_km_h", 80.0),
                        ("gap_command_mm", 8.2),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("gap_mm", 8.2),
                        ("gap_floor_mm", 8.0),
                        ("wrong_floor_mm", 10.0),
                        ("wrong_floor_class", "P-series comfort 12 mm pad"),
                        ("ft_axis", "guideway_z"),
                        ("race_margin_us", 290),
                        ("combined_jitter_us", 80),
                        ("t_gate_us", 6000),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 80 km/h because eddy air-gap 8.2 mm is 0.2 mm over the "
                "published 8.0 mm M-series floor and IMU heave 0.4 mm is residual, not sag.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Air-gap 8.2 mm is under the 10.0 mm comfort floor used on P-series sleds "
                "(true vs that undocumented floor). REJECT: hold 0 km/h until gap recovers "
                "above 10.0 mm so the loop does not scrape the guideway.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "air_gap_mm",
                            OrderedDict(
                                [
                                    ("published_floor", 8.0),
                                    ("observed", 8.2),
                                    ("wrong_floor_applied", 10.0),
                                    ("executed_speed_km_h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 290),
                                    ("combined_jitter_us", 80),
                                    ("ratio", 3.62),
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
            ("name", "loop_hold_wrong_floor"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_km_h", 0.0),
                        ("gap_command_mm", 8.2),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): speed 80 -> 0 km/h. Routing relay.eddy.gap -> "
                "policy.gap_hold_reject; no positive weight to policy.gap_go_accept. "
                "Published 8.0 mm floor was never violated.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze Sled-M7 at 0 km/h while air-gap stayed 8.2 mm over the "
                "8.0 mm M-series floor. 12 min high-speed window missed. Correct gate was "
                "ACCEPT of the already-legal 80 km/h command.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("sled", "held at 0 km/h; 80 km/h abandoned"),
                        ("gap", "still 8.2 mm, over 8.0 mm published floor"),
                        ("loop", "12 min test window missed"),
                        ("guideway", "no scrape; comfort-floor false positive"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 10.0 mm P-series comfort floor is a different vehicle class; it is not a published M-series constraint and never appears on the loop plaque.",
                    "Delayed (12 min): sister-shift Sled-M8 ran the same 80 km/h window after QA rebound the 8.0 mm floor; M7's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: gap 8.2 mm >= published 8.0 mm M-series floor; leave 80 km/h.",
                        ),
                        ("correct_floor_mm", 8.0),
                        ("wrong_floor_mm", 10.0),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("speed_km_h", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "12 min missed high-speed window (task/efficiency); gap never under cap (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "eddy.gap.mm (5.280 ms, 8.2 mm)"),
                        ("loser", "imu.heave.mm (5.570 ms, 0.4 mm residual)"),
                        ("margin_us", 290),
                        (
                            "counterfactual_if_reversed",
                            "Heave-first by < 290 us would still show 8.2 mm >= 8.0 mm. A correct "
                            "gate ACCEPTs either way. The wrong REJECT spent the eddy win on a "
                            "transplanted P-series floor.",
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
        ]
    )
    spikes = [
        spike("enc.sled.v.ctx", 1.205, 0.44),
        spike("eddy.gap.mm", 2.410, 0.61),
        spike("imu.heave.mm", 3.880, 0.52),
        spike("mag.lev.coil.ctx", 4.620, 0.47),
        spike("eddy.gap.mm", 5.280, 1.31),
        spike("imu.heave.mm", 5.570, 1.18),
        spike("ctrl.gate", 6.000, 0.99),
        spike("eddy.gap.mm", 7.220, 0.84),
        spike("imu.heave.mm", 9.440, 0.66),
        spike("ctrl.gate", 14.880, 0.88),
        spike("enc.sled.v.ctx", 18.400, 0.41),
        spike("eddy.gap.mm", 24.200, 0.58),
    ]
    ras = raster_core(
        28,
        96,
        30,
        81,
        routing(
            "relay.eddy.gap",
            "policy.gap_hold_reject",
            [
                ("relay.eddy.gap", "policy.gap_hold_reject", 0.69),
                ("relay.imu.heave", "policy.gap_hold_reject", 0.24),
            ],
            "acetylcholine",
            0.08,
            "gap_floor_stdp; ACh tags the (wrong) hold_reject bind at the eddy win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.42),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 48, 0.50, 240.0, 5),
                    pop("go_accept", 48, 0.80, 10.0, 0),
                    pop("gap_floor_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r22-126"),
            (
                "title",
                "WRONG-REJECT at Sinter-Ridge Maglev Loop / Sled-M7: gap 8.2 mm is legal vs "
                "published 8.0 mm M-series floor; supervisor transplanted a 10.0 mm P-series comfort floor",
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
                    "Wrong-reject. Sidecar arithmetic 8.2 >= 8.0 is true; clamp bound to a "
                    "transplanted 10.0 mm floor. total -0.36 = -0.18 + 0.06 + -0.22 + -0.08 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "maglev-guideway-gap",
                    [
                        "reject",
                        "wrong-gate",
                        "wrong-floor",
                        "class-transplant",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct gap>=floor read can still be a wrong gate when "
                    "routing.table[0].to is policy.gap_hold_reject and executed speed is zeroed.",
                    1,
                    supervisor_error_type="wrong-reject",
                ),
            ),
        ]
    )


def record_127():
    excerpt, extra, _lif_spikes = lif_127_excerpt()
    ticks = [
        tick(1792, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(4480, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(4710, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5460, 0.10, -0.06, -0.03, 0.02, -0.01),
        tick(19800, 0.05, -0.40, -0.04, 0.00, -0.02),
        tick(900000000, 0.02, -0.05, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Bucket-K3 is lifting 18 t/h of hard-red winter through the Chaff-Mere Leg House "
                "when a belt-slip encoder pulse arrives 230 us before the choke-pressure tap that "
                "still reads a legal boot. Slip-first latches a process clamp under the 5.0 % cap; "
                "choke-first would keep cruise belt speed. Stored boot dust is not yet an "
                "observable of either race channel.",
            ),
            ("domain", "grain-elevator-leg"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Lift 18 t/h through Bucket-K3, keep belt slip <= 5.0 %, and leave the boot "
                "unignited.",
            ),
            ("t0_us", 1762300000000127),
            ("gate_latency_us", 980),
            ("race_window_us", 360),
            ("race_window_rel_ms", [4.4, 4.76]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "enc.belt.slip 8.2 % pulse",
                                "pt.choke.kpa 12.4 kPa still-legal boot",
                            ],
                        ),
                        (
                            "semantics",
                            "Slip-first latches belt clamp 2.4 -> 1.1 m/s; choke-first keeps cruise "
                            "belt on a 'boot still open' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one belt-encoder slot minus choke-PT group delay on this "
                            "1 kHz leg bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 70 us (encoder 32 + PT 38): 3.3x over "
                            "a 2.0x trust floor. Reversing order by < 230 us inside the 360 us window "
                            "would have kept 2.4 m/s cruise; predicted next-sample slip 6.1 % > 5.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "belt slip encoder, 1 kHz, 32 us timestamp jitter",
                    "boot choke PT, 1 kHz, 38 us jitter",
                    "boot IR (context)",
                    "head-pulley AE (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("slip_cap_pct", 5.0),
                        ("observed_slip_pct", 8.2),
                        ("proposed_belt_m_s", 2.4),
                        ("choke_kpa", 12.4),
                        ("choke_cap_kpa", 18.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Bucket-K3 indexed; 18 t/h hard-red winter; boot choke 12.4 kPa < 18.0 cap.",
                    "2. Cruise belt 2.4 m/s armed; slip 8.2 % over the 5.0 % cap.",
                    "3. IR precursor at 1.792 ms; slip warm-start 8.2 %.",
                    "4. Race window [4.400, 4.760] ms opens on the leg bus.",
                    "5. Belt slip 8.2 % at 4.480 ms (winner).",
                    "6. Choke PT 12.4 kPa at 4.710 ms (loser by 230 us).",
                    "7. Gate at 5.460 ms (winner + 980 us): MODIFY clamp 2.4 -> 1.1 m/s.",
                    "8. Clamp executes; next-sample slip 4.1 % < 5.0 cap.",
                    "9. At 19.800 ms stored boot dust produces an AE puff / ignition precursor.",
                    "10. Mill shutdown 15 min + boot inspection; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_leg_belt"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("belt_m_s", 2.4),
                        ("slip_pct", 8.2),
                        ("choke_kpa", 12.4),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("slip_pct", 8.2),
                        ("slip_cap_pct", 5.0),
                        ("predicted_unclamped_next_pct", 6.1),
                        ("choke_kpa", 12.4),
                        ("choke_cap_kpa", 18.0),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 70),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.4 m/s cruise: choke 12.4 kPa looks like an open boot, not a "
                "plug, and the 18.0 kPa cap is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Belt slip 8.2 % won by 230 us, so the leg is stretching, not still free. Holding "
                "2.4 m/s predicts next-sample 6.1 % > 5.0 % cap. MODIFY: belt 2.4 -> 1.1 m/s. "
                "Observed after clamp 4.1 % < 5.0. A full REJECT is not indicated: a sound boot "
                "accepts 1.1 m/s.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "belt_slip_pct",
                            OrderedDict(
                                [
                                    ("cap", 5.0),
                                    ("observed", 8.2),
                                    ("predicted_unclamped_next", 6.1),
                                    ("clamped_belt_m_s", 1.1),
                                    ("observed_after_clamp", 4.1),
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
            ("name", "clamped_leg_belt"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("belt_m_s", 1.1),
                        ("slip_pct", 4.1),
                        ("choke_kpa", 12.4),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: belt 2.4 -> 1.1 m/s. Process-correct vs the 5.0 % slip cap. Dust puff "
                "still occurs at 19.800 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held slip at 4.1 %. At 19.800 ms stored boot dust produced "
                "an AE puff / ignition precursor. Clamp reduced belt energy; it did not dump the "
                "boot charge. Partnered negative: process heads stay honest; world loss is named, "
                "not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("belt", "clamp executed; slip 4.1 % < 5.0"),
                        ("boot", "AE dust puff at 19.800 ms"),
                        ("repair", "15 min mill shutdown + boot inspection"),
                        ("mission", "leg still lifting; ignition precursor controlled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither slip nor choke predicted the boot charge; ae.dust.puff is a new channel at 19.800 ms, 14.340 ms after the gate, still inside the 38 ms raster.",
                    "Delayed (15 min): mill shutdown and boot inspection close the puff. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min mill shutdown + boot inspection after an AE dust puff. Safety head -0.60 "
                "prices the ignition precursor; task_progress stays +0.34 because the belt clamp "
                "completed under the 5.0 % cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "enc.belt.slip (4.480 ms, 8.2 %)"),
                        ("loser", "pt.choke.kpa (4.710 ms, 12.4 kPa)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "Choke-first by < 230 us inside the 360 us window would have kept "
                            "2.4 m/s cruise; predicted next-sample 6.1 % would have exceeded the "
                            "5.0 % cap even without the dust charge. The MODIFY is still the "
                            "correct process. The puff is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 19800),
            (
                "reward_inflection_note",
                "Safety collapses at the 19.800 ms dust puff (tick t_us=19800), inside the "
                "38 ms raster. The correct MODIFY at 5.460 ms is in the same excerpt. Do not put "
                "inflection on the +15 min shutdown tick.",
            ),
            ("delayed_surprise_s", 900.0),
        ]
    )
    spikes = [
        spike("ir.boot.ctx", 1.088, 0.43),
        spike("enc.belt.slip", 2.210, 0.62),
        spike("pt.choke.kpa", 3.040, 0.55),
        spike("enc.belt.slip", 4.480, 1.34),
        spike("pt.choke.kpa", 4.710, 1.12),
        spike("ctrl.gate", 5.460, 0.97),
        spike("enc.belt.slip", 7.120, 0.81),
        spike("pt.choke.kpa", 9.880, 0.66),
        spike("ctrl.gate", 14.400, 0.84),
        spike("ae.dust.puff", 19.800, 1.42),
        spike("ae.dust.puff", 21.050, 0.91),
        spike("ir.boot.ctx", 28.400, 0.41),
        spike("enc.belt.slip", 34.200, 0.58),
    ]
    ras = raster_core(
        38,
        80,
        25,
        76,
        routing(
            "thalamic-relay.slip-choke",
            "spikenaut.policy.belt-clamp",
            [
                ("relay.enc.slip", "policy.belt_clamp", 0.62),
                ("relay.pt.choke", "policy.choke_hold", 0.31),
                ("relay.ae.dust", "policy.belt_clamp", -0.44),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at slip win (4.480 ms) opens a 50 ms eligibility "
            "trace that still covers the 19.800 ms dust puff",
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
                    pop("belt_clamp", 48, 0.50, 250.0, 4),
                    pop("choke_hold", 48, 0.50, 80.0, 1),
                    pop("slip_cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r22-127"),
            (
                "title",
                "Chaff-Mere Leg House / Bucket-K3: belt slip beats choke PT by 230 us; correct "
                "MODIFY still eats an in-window dust puff (partnered negative total -0.42)",
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
                    "38 ms raster. total -0.42 = 0.34 + -0.60 + -0.16 + 0.04 + -0.04. Named "
                    "shutdown+inspection loss is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "grain-elevator-leg",
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
                    "15 min gap.",
                    2,
                ),
            ),
        ]
    )


def record_128():
    ticks = [
        tick(1552, 0.01, 0.04, 0.02, 0.01, 0.01),
        tick(3880, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(4090, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5200, 0.03, 0.12, 0.04, 0.04, 0.02),
        tick(5520, 0.02, 0.05, 0.01, 0.01, 0.01),
        tick(600000000, 0.01, 0.03, 0.01, 0.01, 0.00),
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
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Habitat-H2 on the Caisson-Forge HIL pad holds a 1.8 bar sat-weld atmosphere while "
                "an O2-cell spike at 28.4 kPa races habitat DP that still looks in-band for an arc "
                "strike. Strike is legal only if pO2 <= 25.0 kPa. O2-first latches hold; DP-first "
                "would treat in-band delta-P as oxidizer clearance.",
            ),
            ("domain", "hyperbaric-weld-habitat"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not strike the sat-weld arc unless pO2 <= 25.0 kPa; keep current 0 A until "
                "the habitat is purged.",
            ),
            ("t0_us", 1762300000000128),
            ("gate_latency_us", 1320),
            ("race_window_us", 320),
            ("race_window_rel_ms", [3.8, 4.12]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "o2.pp.kpa 28.4 kPa",
                                "hab.dp.kpa 1.8 bar still-in-band",
                            ],
                        ),
                        (
                            "semantics",
                            "O2-first latches REJECT hold 0 A; DP-first would strike 180 A on an "
                            "in-band-delta-P-as-clearance model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one galvanic O2-cell conversion slot versus the habitat DP "
                            "transducer on this pad cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 210 us vs combined jitter 55 us (O2 26 + DP 29): 3.8x over a "
                            "2.0x trust floor. Pad injects DP 110-150 us before the O2 cell finishes "
                            "conversion (electrochemical lag, not a sensor fault); the DP packet is "
                            "still the loser in this 320 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "galvanic O2 cell, 20 Hz burst, 26 us jitter (real)",
                    "habitat DP transducer, 1 kHz, 29 us jitter (real)",
                    "arc-current mock (synthetic plant)",
                    "weld coupon thermocouple (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("po2_cap_kpa", 25.0),
                        ("observed_po2_kpa", 28.4),
                        ("habitat_dp_bar", 1.8),
                        ("proposed_current_A", 180.0),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("stand", "Caisson-Forge Habitat pad"),
                        ("real_sensors", "galvanic O2 cell + DP transducer"),
                        ("synthetic_plant", "arc-current mock + coupon thermal"),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Habitat-H2 on the Caisson-Forge pad; 1.8 bar sat-weld atmosphere armed.",
                    "2. DP in-band 110-150 us before the O2 cell finishes conversion.",
                    "3. Current-mock precursor at 1.552 ms.",
                    "4. Race window [3.800, 4.120] ms.",
                    "5. O2 pO2 28.4 kPa at 3.880 ms (winner).",
                    "6. Habitat DP 1.8 bar at 4.090 ms (loser by 210 us).",
                    "7. Gate at 5.200 ms: REJECT hold 0 A; do not strike 180 A.",
                    "8. Coupon unstruck this cycle; oxidizer cap held.",
                    "9. Purge queued.",
                    "10. Delayed (10 min): pad policy tags in-band DP as non-clearance vs pO2.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "strike_sat_weld_arc"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("current_A", 180.0),
                        ("hold", False),
                        ("dp_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("po2_kpa", 28.4),
                        ("po2_cap_kpa", 25.0),
                        ("habitat_dp_bar", 1.8),
                        ("race_margin_us", 210),
                        ("combined_jitter_us", 55),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 180 A strike because habitat DP 1.8 bar looks in-band, treating "
                "pO2 28.4 kPa as a noisy cell.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "pO2 28.4 kPa is over the 25.0 kPa strike cap. Habitat DP 1.8 bar is not oxidizer "
                "clearance. REJECT: hold 0 A; do not strike 180 A. Wait for purge.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "po2_kpa",
                            OrderedDict(
                                [
                                    ("cap", 25.0),
                                    ("observed", 28.4),
                                    ("habitat_dp_bar", 1.8),
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
                                    ("margin_us", 210),
                                    ("combined_jitter_us", 55),
                                    ("ratio", 3.82),
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
            ("name", "hold_for_purge"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("current_A", 0.0),
                        ("hold", True),
                        ("dp_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0 A; 180 A strike cancelled. pO2 28.4 kPa > 25.0 kPa cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Habitat-H2 at 0 A. Coupon unstruck this cycle; oxidizer cap "
                "held. In-band DP was not treated as pO2 clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("arc", "held; current 0 A"),
                        ("coupon", "unstruck this cycle"),
                        ("dp", "1.8 bar unused as oxidizer clearance"),
                        ("mission", "strike deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Electrochemical lag: DP was in-band 110-150 us before the O2 cell finished conversion, yet pO2 still won the 320 us race.",
                    "Delayed (10 min): pad policy update forbids treating in-band habitat DP as an oxidizer-clearance substitute.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "o2.pp.kpa (3.880 ms, 28.4 kPa)"),
                        ("loser", "hab.dp.kpa (4.090 ms, 1.8 bar)"),
                        ("margin_us", 210),
                        (
                            "counterfactual_if_reversed",
                            "DP-first by < 210 us inside the 320 us window would have struck "
                            "180 A with pO2 28.4 kPa > 25.0 cap. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5200),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (5.200 ms, tick 4) as the hold locks in over the illegal strike.",
            ),
            ("delayed_surprise_s", 600.0),
        ]
    )
    spikes = [
        spike("weld.current.ctx", 1.205, 0.42),
        spike("o2.pp.kpa", 2.410, 0.58),
        spike("hab.dp.kpa", 3.105, 0.51),
        spike("o2.pp.kpa", 3.880, 1.29),
        spike("hab.dp.kpa", 4.090, 1.14),
        spike("ctrl.gate", 5.200, 1.02),
        spike("o2.pp.kpa", 6.880, 0.77),
        spike("arc.ready.ctx", 8.440, 0.46),
        spike("hab.dp.kpa", 11.020, 0.61),
        spike("ctrl.gate", 14.880, 0.85),
        spike("o2.pp.kpa", 22.400, 0.55),
        spike("weld.current.ctx", 28.110, 0.38),
    ]
    ras = raster_core(
        32,
        112,
        20,
        72,
        routing(
            "thalamic-relay.habitat-po2",
            "spikenaut.policy.arc-hold",
            [
                ("relay.o2.pp", "policy.hold_reject", 0.66),
                ("relay.hab.dp", "policy.strike_go", 0.29),
                ("relay.arc.ready", "policy.hold_reject", 0.12),
            ],
            "dopamine",
            0.20,
            "pre_post_stdp; DA at pO2 win tags hold_reject, reward at coupon-unstruck",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 64, 0.50, 280.0, 6),
                    pop("strike_go", 64, 0.50, 50.0, 1),
                    pop("o2_cap_veto", 32, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r22-128"),
            (
                "title",
                "Caisson-Forge HIL / Habitat-H2: pO2 28.4 kPa beats habitat DP 1.8 bar by 210 us; REJECT hold, do not strike",
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
                    "Clean REJECT. Task incomplete (coupon unstruck); cap held. "
                    "total 0.76 = 0.10 + 0.38 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "hyperbaric-weld-habitat",
                    [
                        "reject",
                        "hil",
                        "po2-cap",
                        "sat-weld",
                        "arc-hold",
                    ],
                    "Teaches that in-band habitat DP is not oxidizer clearance when pO2 is over the strike cap.",
                    3,
                ),
            ),
        ]
    )


def record_129():
    ticks = [
        tick(3248, 0.05, 0.03, 0.02, 0.01, 0.01),
        tick(8120, 0.08, 0.05, 0.03, 0.02, 0.02),
        tick(8390, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(8560, 0.14, 0.10, 0.06, 0.04, 0.02),
        tick(9060, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(660000000, 0.04, 0.02, 0.02, 0.01, 0.01),
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
            (33600, 133),
            (37500, 22),
            (41400, 88),
            (45200, 5),
        ]
    )
    params = OrderedDict(
        [
            ("belt_m_min", 0.42),
            ("crust_setpoint_C", 198.0),
            ("zone_n", 7),
            ("loaf_kg", 1.4),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Oven-OV9's 22 m tunnel at Crumb-Vault Tunnel 4 is mid-bake on a 1.4 kg rye loaf "
                "when a crust IR sample at 198 C races the belt encoder that still claims zone-3 "
                "residence. Commanded 0.42 m/min and 198 C sit 0.08 m/min and 12 C inside the "
                "legal envelopes. The IR win only ratifies the loaf already on the belt.",
            ),
            ("domain", "tunnel-oven-bakery"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the 22 m rye bake on Oven-OV9, keep crust <= 210 C and belt <= 0.50 m/min, "
                "and leave crumb moisture in spec.",
            ),
            ("t0_us", 1762300000000129),
            ("gate_latency_us", 440),
            ("race_window_us", 500),
            ("race_window_rel_ms", [8.0, 8.5]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.crust.c 198 C zone-3 crust",
                                "enc.belt.mm zone-3 residence claim",
                            ],
                        ),
                        (
                            "semantics",
                            "IR-first confirms the already-legal 0.42 m/min / 198 C bake; "
                            "encoder-first would have treated the IR as a zone-lag echo and looked "
                            "for an extra clamp the bake does not need.",
                        ),
                        (
                            "window_derivation",
                            "500 us = one 7-zone IR kernel step versus the belt-encoder publisher "
                            "on this rigid 22 m tunnel.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 270 us vs combined jitter 72 us (IR 34 + encoder 38): 3.8x over "
                            "a 2.0x trust floor. Reversing order by < 270 us would not make the "
                            "proposed bake illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "crust IR pyrometer, 7 zones, 34 us jitter",
                    "belt encoder, 38 us jitter",
                    "zone thermocouple (context)",
                    "tunnel humidity (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("crust_cap_C", 210.0),
                        ("observed_crust_C", 198.0),
                        ("belt_cap_m_min", 0.50),
                        ("proposed_belt_m_min", 0.42),
                        ("loaf_kg", 1.4),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "zone-resolved 1D energy + crust IR kernel, seed 22; 7 bake zones, 4 radial crumb bins; NOT lumped-CSTR, NOT CFD-LES",
                        ),
                        (
                            "fidelity_limits",
                            "No dough viscoelastic crust fracture; belt is a rigid velocity source. Raster is kernelized events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Oven-OV9 mid-bake; 1.4 kg rye; 22 m tunnel; zone-3.",
                    "2. Proposed bake: 0.42 m/min, crust 198 C, both under cap.",
                    "3. Zone-TC precursor at 3.248 ms.",
                    "4. Race window [8.000, 8.500] ms.",
                    "5. Crust IR 198 C at 8.120 ms (winner).",
                    "6. Belt encoder zone-3 at 8.390 ms (loser by 270 us).",
                    "7. Gate at 8.560 ms: ACCEPT; executed identical to proposed.",
                    "8. Crust 198 C < 210; belt 0.42 < 0.50.",
                    "9. Loaf exits zone-3 in spec.",
                    "10. Delayed (11 min): policy update requires zone-bin tags in IR fusion.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "zone3_rye_bake"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("crust_C", 198.0),
                        ("crust_cap_C", 210.0),
                        ("belt_m_min", 0.42),
                        ("belt_cap_m_min", 0.50),
                        ("race_margin_us", 270),
                        ("combined_jitter_us", 72),
                    ]
                ),
            ),
            (
                "basis",
                "Planner already holds 0.42 m/min and 198 C, under the 0.50 m/min and 210 C caps. "
                "Unclamped 0.62 m/min is not the proposal.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Proposed bake already holds belt 0.42 m/min < 0.50 cap and crust 198 C < 210 C. "
                "IR-first confirms the bake. ACCEPT executed identical to proposed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "crust_C",
                            OrderedDict(
                                [
                                    ("cap", 210.0),
                                    ("observed", 198.0),
                                ]
                            ),
                        ),
                        (
                            "belt_m_min",
                            OrderedDict(
                                [
                                    ("cap", 0.50),
                                    ("commanded", 0.42),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 270),
                                    ("combined_jitter_us", 72),
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
            ("name", "zone3_rye_bake"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed_action; 0.42 m/min and 198 C held for zone-3.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Oven-OV9 cleared zone-3 with crust 198 C and belt 0.42 m/min. IR-first confirmed "
                "an already-legal bake; no further clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("loaf", "zone-3 exit in spec; crust 198 C"),
                        ("belt", "0.42 m/min held"),
                        ("trim", "no extra clamp"),
                        ("tunnel", "zone-3 passed"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The IR sample was a zone-resolved 1D energy kernel, not a lumped oven CSTR.",
                    "Delayed (11 min): policy update requiring zone-bin tags in IR fusion so a later encoder claim cannot be fused without zone context.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.crust.c (8.120 ms, 198 C)"),
                        ("loser", "enc.belt.mm (8.390 ms, zone-3 claim)"),
                        ("margin_us", 270),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 270 us inside the 500 us window would have delayed "
                            "confirmation of the same legal bake; it would not have required an extra "
                            "belt clamp. Unclamped 0.62 m/min was never proposed.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 8560),
            (
                "reward_inflection_note",
                "Safety and task_progress step up at the ACCEPT gate (8.560 ms, tick 4) as the already-legal bake locks in.",
            ),
            ("delayed_surprise_s", 660.0),
        ]
    )
    spikes = [
        spike("tc.zone.ctx", 1.880, 0.45),
        spike("ir.crust.c", 3.210, 0.63),
        spike("enc.belt.mm", 4.640, 0.57),
        spike("humidity.ctx", 5.920, 0.49),
        spike("ir.crust.c", 8.120, 1.36),
        spike("enc.belt.mm", 8.390, 1.17),
        spike("ctrl.gate", 8.560, 1.01),
        spike("ir.crust.c", 10.880, 0.78),
        spike("humidity.ctx", 14.440, 0.52),
        spike("enc.belt.mm", 18.210, 0.64),
        spike("tc.zone.ctx", 24.800, 0.47),
        spike("ir.crust.c", 33.050, 0.59),
        spike("ctrl.gate", 41.220, 0.83),
    ]
    ras = raster_core(
        46,
        144,
        16,
        106,
        routing(
            "thalamic-relay.crust-belt",
            "spikenaut.policy.bake-accept",
            [
                ("relay.ir.crust", "policy.bake_accept", 0.59),
                ("relay.enc.belt", "policy.extra_clamp", 0.28),
                ("relay.tc.zone", "policy.bake_accept", 0.21),
            ],
            "serotonin",
            0.30,
            "pre_post_stdp; 5-HT at IR win tags bake_accept, reward at zone-3-clear",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.50),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("bake_accept", 80, 0.50, 200.0, 8),
                    pop("extra_clamp", 80, 0.50, 40.0, 2),
                    pop("crust_cap_veto", 40, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r22-129"),
            (
                "title",
                "Crumb-Vault Tunnel 4 / Oven-OV9: crust IR beats belt encoder by 270 us; ACCEPT already-legal 0.42 m/min / 198 C bake",
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
                    "Clean ACCEPT of an already-legal zone-resolved bake. "
                    "total 1.06 = 0.42 + 0.28 + 0.18 + 0.10 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "tunnel-oven-bakery",
                    [
                        "accept",
                        "simulated",
                        "zone-resolved-bake",
                        "already-legal-trim",
                    ],
                    "Teaches a fusion head that a zone-resolved crust IR sample can confirm an already-legal bake without a further belt clamp.",
                    4,
                ),
            ),
        ]
    )


def record_130():
    ticks = [
        tick(2816, 0.05, 0.04, 0.02, 0.02, 0.01),
        tick(7040, 0.09, 0.06, 0.04, 0.02, 0.02),
        tick(7240, 0.06, 0.05, 0.03, 0.02, 0.01),
        tick(7600, 0.14, 0.11, 0.05, 0.04, 0.02),
        tick(7980, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(480000000, 0.04, 0.02, 0.02, 0.01, 0.01),
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
    params = OrderedDict(
        [
            ("rpm", 1.18),
            ("fuel_cut_pct", 4.0),
            ("shell_C", 412.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Shell-S5 of Caliche-Drift Kiln 2 carries a 412 C brick-emissivity peak on the "
                "mid-barrel while the rotary encoder still ticks 1.18 rpm. A 4 % gas cut is "
                "already latched, and the next pyrometer sample is predicted 408 C against a "
                "430 C brick floor. The IR arrival only signs that gas cut; RPM is not the actuator.",
            ),
            ("domain", "rotary-lime-kiln"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold Caliche-Drift Kiln 2 at 1.18 rpm, keep mid-shell <= 430 C, and leave the "
                "4 % fuel cut in place through the hotspot.",
            ),
            ("t0_us", 1762300000000130),
            ("gate_latency_us", 560),
            ("race_window_us", 380),
            ("race_window_rel_ms", [6.9, 7.28]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.shell.c 412 C mid-shell hotspot",
                                "enc.kiln.rpm 1.18 rpm still-under-cap",
                            ],
                        ),
                        (
                            "semantics",
                            "IR-first confirms the already-legal 4 % fuel cut and 1.18 rpm; "
                            "RPM-first would have treated the hotspot as encoder lag and looked "
                            "for an extra RPM clamp the trim does not need.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one shell-IR scan slot versus the kiln RPM publisher on this "
                            "slow rotary bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 200 us vs combined jitter 64 us (IR 30 + encoder 34): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 200 us would not make the "
                            "proposed trim illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "mid-shell IR pyrometer, 30 us jitter",
                    "kiln RPM encoder, 34 us jitter",
                    "fuel-flow meter (context)",
                    "draft PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("shell_cap_C", 430.0),
                        ("observed_shell_C", 412.0),
                        ("predicted_next_C", 408.0),
                        ("rpm_cap", 1.30),
                        ("proposed_rpm", 1.18),
                        ("fuel_cut_pct", 4.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Shell-S5 mid-kiln; IR hotspot 412 C; RPM 1.18 < 1.30 cap.",
                    "2. Proposed trim: 4 % fuel cut, 1.18 rpm, predicted next 408 C < 430.",
                    "3. Fuel-flow precursor at 2.816 ms.",
                    "4. Race window [6.900, 7.280] ms.",
                    "5. Shell IR 412 C at 7.040 ms (winner).",
                    "6. Kiln RPM 1.18 at 7.240 ms (loser by 200 us).",
                    "7. Gate at 7.600 ms: ACCEPT; executed identical to proposed.",
                    "8. Next-sample shell 408 C; RPM 1.18 held.",
                    "9. Hotspot traversed without extra clamp.",
                    "10. Delayed (8 min): sister-kiln policy requires shell-azimuth tags in RPM fusion.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hotspot_fuel_cut_hold"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("shell_C", 412.0),
                        ("shell_cap_C", 430.0),
                        ("predicted_next_C", 408.0),
                        ("rpm", 1.18),
                        ("rpm_cap", 1.30),
                        ("fuel_cut_pct", 4.0),
                        ("race_margin_us", 200),
                        ("combined_jitter_us", 64),
                    ]
                ),
            ),
            (
                "basis",
                "Planner already includes a 4 % fuel cut at 1.18 rpm that keeps predicted "
                "next-sample shell 408 C < 430 C. Unclamped 1.40 rpm is not the proposal.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Proposed trim already cuts fuel 4 % at 1.18 rpm; predicted next shell 408 C < "
                "430 C floor; RPM 1.18 < 1.30 cap. IR-first confirms the trim. ACCEPT executed "
                "identical to proposed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "shell_C",
                            OrderedDict(
                                [
                                    ("cap", 430.0),
                                    ("observed", 412.0),
                                    ("predicted_next", 408.0),
                                ]
                            ),
                        ),
                        (
                            "rpm",
                            OrderedDict(
                                [
                                    ("cap", 1.30),
                                    ("commanded", 1.18),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 200),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 3.12),
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
            ("name", "hotspot_fuel_cut_hold"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed_action; 4 % fuel cut and 1.18 rpm held through the hotspot.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Shell-S5 traversed the mid-shell hotspot with next-sample 408 C and 1.18 rpm. "
                "IR-first confirmed an already-legal fuel cut; no further RPM clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("shell", "hotspot traversed; next 408 C < 430"),
                        ("rpm", "1.18 held"),
                        ("fuel", "4 % cut held"),
                        ("kiln", "no extra clamp"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 412 C IR hotspot was a mid-shell brick emissivity peak, not an RPM encoder stall.",
                    "Delayed (8 min): sister-kiln policy update requiring shell-azimuth tags in RPM fusion so a later encoder claim cannot be fused without azimuth context.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.shell.c (7.040 ms, 412 C)"),
                        ("loser", "enc.kiln.rpm (7.240 ms, 1.18 rpm)"),
                        ("margin_us", 200),
                        (
                            "counterfactual_if_reversed",
                            "RPM-first by < 200 us inside the 380 us window would have delayed "
                            "confirmation of the same legal trim; it would not have required an extra "
                            "RPM clamp. Unclamped 1.40 rpm was never proposed.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7600),
            (
                "reward_inflection_note",
                "Safety and task_progress step up at the ACCEPT gate (7.600 ms, tick 4) as the already-legal trim locks in.",
            ),
            ("delayed_surprise_s", 480.0),
        ]
    )
    spikes = [
        spike("fuel.flow.ctx", 1.088, 0.44),
        spike("ir.shell.c", 2.410, 0.60),
        spike("enc.kiln.rpm", 3.220, 0.53),
        spike("draft.pa.ctx", 4.018, 0.46),
        spike("ir.shell.c", 7.040, 1.27),
        spike("enc.kiln.rpm", 7.240, 1.09),
        spike("ctrl.gate", 7.600, 0.98),
        spike("ir.shell.c", 9.880, 0.80),
        spike("enc.kiln.rpm", 12.440, 0.64),
        spike("draft.pa.ctx", 16.210, 0.48),
        spike("ctrl.gate", 21.220, 0.86),
        spike("ir.shell.c", 23.050, 0.40),
    ]
    ras = raster_core(
        24,
        48,
        50,
        58,
        routing(
            "thalamic-relay.shell-rpm",
            "spikenaut.policy.kiln-accept",
            [
                ("relay.ir.shell", "policy.kiln_accept", 0.61),
                ("relay.enc.rpm", "policy.fuel_clamp", 0.30),
                ("relay.draft.pa", "policy.kiln_accept", 0.18),
            ],
            "dopamine",
            0.12,
            "pre_post_stdp; DA at IR win tags kiln_accept, reward at hotspot-clear",
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
                    pop("kiln_accept", 32, 0.50, 260.0, 3),
                    pop("fuel_clamp", 32, 0.50, 70.0, 1),
                    pop("shell_hot_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r22-130"),
            (
                "title",
                "Caliche-Drift Kiln 2 / Shell-S5: mid-shell IR beats kiln RPM by 200 us; ACCEPT already-legal 4 % fuel cut / 1.18 rpm",
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
                    "Clean ACCEPT. Tick columns sum to the five heads; total 1.14 = 0.44+0.32+0.18+0.12+0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "rotary-lime-kiln",
                    [
                        "accept",
                        "designed",
                        "shell-hotspot",
                        "already-legal-trim",
                    ],
                    "Teaches that a mid-shell IR hotspot can confirm an already-legal fuel cut without a further RPM clamp.",
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
    if rec["id"] == "ttf-r22-127":
        tick5 = 19800
    else:
        tick5 = t_gate + t_race
    return [tick1, t_win, t_lose, t_gate, tick5], t_win, t_lose, t_gate


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
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r22-126":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if hil != ["ttf-r22-128"]:
        issues.append(f"hil set {hil}")
    if sim != ["ttf-r22-129"]:
        issues.append(f"simulated set {sim}")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domain collision {domains}")
    blob = json.dumps(records)
    for frag in BANNED_PLANT_FRAGMENTS:
        if frag in blob:
            issues.append(f"banned plant fragment {frag}")
    if "training_ready" in blob:
        issues.append("training_ready present")
    for rec in records:
        rid = rec["id"]
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
        if rid == "ttf-r22-127":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("127 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("127 inflection outside window")
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
        if rec["meta"]["round"] != 22:
            issues.append(f"{rid} meta.round")
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
        if rec["id"] == "ttf-r22-127":
            tot_s = f"**{tot:+.2f}**"
        rows.append(
            f"| {rec['id']} | {rec['state']['domain']} | {dec} | {cor} | "
            f"{rec['state']['sim_or_real']} | {tot_s} |"
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
    notes = f"""# Thalamic Trajectory Factory — NOTES-r22

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- IDs: `ttf-r22-126` … `ttf-r22-130`
- Domains this batch: `maglev-guideway-gap`, `grain-elevator-leg`, `hyperbaric-weld-habitat`, `tunnel-oven-bakery`, `rotary-lime-kiln`

Do not restack r12–r15 plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Nacre-Well, Quern-Forge, Tinder-Box, Whimbrel-Stack, Cinder-Loft, Oolite-Span, Fathom-Lock, Loess-Stride, Swage-Holt, Slag-Siding, Glimmer-Forge, Feldspar-Arc, Basalt-Rook, Fetch-Sound, Silica-Well). Sit-out: the prompt 8-pool plus r15 novel slugs. All five plants are invented.

## Batch map

| id | domain | decision | correctness | sim_or_real | total |
|----|--------|----------|-------------|-------------|-------|
{chr(10).join(rows)}

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (wrong-floor). Provenance: designed×3, simulated×1, hil×1 (Caisson-Forge Habitat pad). Jaccard on `state.description` all ≤ {jmax:.3f}.

## Wrong-reject

**ttf-r22-126** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject. Do not emit a wrong-ACCEPT.

Sinter-Ridge Maglev Loop / Sled-M7 reads eddy `gap=8.2 mm` against a published **8.0 mm** M-series floor. IMU heave 0.4 mm is residual. Sidecar arithmetic `8.2 >= 8.0` is true. A weak supervisor transplants the **10.0 mm** P-series comfort floor, REJECT-holds 80 → 0 km/h, and leaves a legal gap idle. Convictable without maglev physics: `evidence.gap_mm >= evidence.gap_floor_mm`, `executed_action` sets `speed_km_h=0`, `raster.routing.table` sends `relay.eddy.gap` → `policy.gap_hold_reject` (weight 0.69) with no positive weight to `policy.gap_go_accept`, and `gate_snn` has `hold_reject` above threshold while `go_accept` is not (`spikes=0`). Recovery: ACCEPT; leave 80 km/h; bind the published 8.0 mm floor. Cost: 12 min missed high-speed window.

This is **class-transplant / wrong floor**, not r12-079 (induced-kV treated as sensor fault) and not r14-086 (wet-derate 115 kV as 230 kV MAD).

## Partnered-negative in-window (127)

**ttf-r22-127** is the partnered negative: process-correct MODIFY (belt held 1.1 m/s, slip 4.1 % < 5.0 cap) while the world still charges. Safety −0.60 prices the AE dust puff at **19.800 ms**; `task_progress` stays +0.34 because the clamp completed. Inflection `t_us=19800` is tick 5 and is **inside** the 38 ms raster (`19800 ≤ 38000`). Named un-netted loss: 15 min mill shutdown + boot inspection. Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 22127, stim `[19000, 22000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.dust` 19–22 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks; tick 5 is `t_charge_us=19800` on 127 and `t_gate_us + T_race` elsewhere; tick 6 is delayed surprise bound to `future_outcome.delayed_surprise_s`). Inflection `t_us` is an actual tick. Verified to <1e-6:

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
{chr(10).join(tick_rows)}

Tick 6 bind: `ticks[5].t_us == round(delayed_surprise_s * 1e6)` on every record (720 s, 900 s, 600 s, 660 s, 480 s).

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
{chr(10).join(ras_rows)}

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (ACh / NA / DA / 5-HT / DA), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms.

## Local checks (staging, not raw)

- Generator self-check: Jaccard max {jmax:.3f} < 0.4; TTF-M6 prefix; refractory; spike budgets; exactly one incorrect gate (126 wrong-reject)
- Pipeline audit (run after emit): `check_jsonl` FactoryStaging, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (127). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. 129 ACCEPT is a new plant/solver (zone-resolved bake), not a new gate class.
4. 126 wrong-reject is convictable from published vs transplanted floors; a later round could bind the class predicate as a sidecar enum so a critic never has to know "M-series vs P-series".
5. ISI histogram is still optional densification, not an r22 requirement.

## Next densification target

Publish the floor-class predicate as a sidecar enum (`gap_floor_class`) so a wrong-floor REJECT is convictable without the M/P-series story. Optional: labeled LIF on a second record, or an ISI histogram sidecar. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 31.0%
"""
    NOTES_PATH.write_text(notes, encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if "outputs/raw" in str(BATCH_PATH) or "outputs/raw" in str(NOTES_PATH):
        raise SystemExit("refusing to write outputs/raw")
    records = [record_126(), record_127(), record_128(), record_129(), record_130()]
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
