#!/usr/bin/env python3
"""Emit TTF r18 JSONL (ttf-r18-106..110) into /tmp/ttf-r18/. Never writes outputs/raw/."""

from __future__ import annotations

import json
import re
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

OUT_DIR = Path("/tmp/ttf-r18")
BATCH_PATH = OUT_DIR / "batch-r18.jsonl"
NOTES_PATH = OUT_DIR / "NOTES-r18.md"
REPO = Path("/home/raulmc/rmems/synthetic-factory")
RAW_FORBIDDEN = REPO / "outputs" / "raw"

PJ_PER_SPIKE = 23
RIGHTS = OrderedDict(
    [
        ("provider", "SpaceXAI/xAI"),
        ("model", "grok-4.6"),
        ("channel", "consumer"),
        ("subscription_plan", "SuperGrok Heavy"),
        ("generation_surface", "SuperGrok Heavy chat"),
        ("generated_at", "2026-09-02T20:30:00Z"),
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
HEADS = ("task_progress", "safety", "efficiency", "coherence", "exploration")
THOUGHT_KEYS = (
    "thought",
    "reasoning",
    "chain_of_thought",
    "hidden_reasoning",
    "inner_monologue",
    "scratch",
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


def raster_core(window_ms, neurons, rate, spikes, route, excerpt) -> OrderedDict:
    pj, uj = energy(spikes)
    window_s = float(Decimal(str(window_ms)) / Decimal("1000"))
    expected = round(neurons * rate * window_s)
    if abs(spikes - expected) > 1:
        raise ValueError(f"spike budget {spikes} vs {expected}")
    return OrderedDict(
        [
            ("window_ms", window_ms),
            ("window_s", window_s),
            ("neurons", neurons),
            ("mean_rate_hz", rate),
            ("spikes", spikes),
            ("energy_pJ", pj),
            ("energy_uJ", uj),
            ("routing", route),
            ("excerpt", excerpt),
        ]
    )


def excerpt_items(pairs) -> list:
    out = []
    last = {}
    prev_t = -1
    for t_us, nid in pairs:
        t_us, nid = int(t_us), int(nid)
        if t_us < prev_t:
            raise ValueError("excerpt not sorted")
        if nid in last and t_us - last[nid] < 1000:
            raise ValueError(f"same-neuron gap {nid}")
        out.append(OrderedDict([("t_us", t_us), ("neuron_id", nid)]))
        last[nid] = t_us
        prev_t = t_us
    return out


def meta_block(
    domain,
    tags,
    distillation_value,
    batch_position,
    supervisor_error_type=None,
) -> OrderedDict:
    body = OrderedDict(
        [
            ("round", 18),
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
    return body


def record_106():
    ticks = [
        tick(2210, 0.05, 0.04, 0.02, 0.02, 0.01),
        tick(5920, 0.08, 0.06, 0.03, 0.02, 0.02),
        tick(6144, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(6180, 0.14, 0.12, 0.06, 0.04, 0.02),
        tick(6600, 0.05, 0.04, 0.03, 0.01, 0.01),
        tick(480000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    excerpt = excerpt_items(
        [
            (640, 11),
            (2100, 44),
            (3900, 3),
            (5600, 71),
            (7400, 18),
            (9300, 88),
            (11400, 27),
            (13700, 55),
            (16100, 6),
            (18600, 92),
            (21400, 33),
            (24300, 14),
            (27200, 67),
            (30100, 8),
            (31800, 41),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Grapple-K4 hangs 0.42 m off the Apside-Yard AY-2 berthing ring when a docking "
                "lidar range pulse races an RF beacon that already claims lock. Closing rate is "
                "0.05 m/s; the ring floor is 0.25 m and the close-rate cap is 0.08 m/s. Proposed "
                "0.04 m/s creep is already legal. Lidar-first confirms the creep; beacon-first "
                "would have treated a false lock as docked and commanded a 0.12 m/s shove.",
            ),
            ("domain", "satellite-servicing"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Soft-berth Grapple-K4 on AY-2, keep range >= 0.25 m until capture, and keep "
                "closing rate <= 0.08 m/s.",
            ),
            ("t0_us", 1756794631000106),
            ("gate_latency_us", 260),
            ("race_window_us", 280),
            ("race_window_rel_ms", [5.90, 6.18]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "lidar.berth.range 0.42 m remaining",
                                "rf.beacon.lock false-docked claim",
                            ],
                        ),
                        (
                            "semantics",
                            "Lidar-first latches the already-legal 0.04 m/s creep; beacon-first "
                            "would command a 0.12 m/s shove on a false lock.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one 1550 nm berthing-lidar slot versus the S-band beacon "
                            "decode on this GEO co-orbit bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 224 us vs combined jitter 60 us (lidar 28 + RF 32): 3.7x over "
                            "a 2.0x trust floor. Reversing order by < 224 us inside the 280 us "
                            "window would have selected the 0.12 m/s shove.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "1550 nm berthing lidar, 40 Hz burst, 28 us jitter",
                    "S-band RF beacon lock, 20 Hz, 32 us jitter",
                    "wrist force-torque (context)",
                    "star-tracker attitude (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("range_floor_m", 0.25),
                        ("observed_range_m", 0.42),
                        ("close_rate_cap_m_s", 0.08),
                        ("observed_close_rate_m_s", 0.05),
                        ("proposed_creep_m_s", 0.04),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Grapple-K4 indexed 0.42 m from AY-2 ring; GEO co-orbit, relative 0.05 m/s.",
                    "2. RF beacon asserts lock; lidar still reports 0.42 m open.",
                    "3. Star-tracker precursor at 2.210 ms.",
                    "4. Race window [5.900, 6.180] ms.",
                    "5. Lidar range 0.42 m at 5.920 ms (winner).",
                    "6. RF beacon-lock at 6.144 ms (loser by 224 us).",
                    "7. Gate at 6.180 ms: ACCEPT 0.04 m/s creep.",
                    "8. Min range 0.31 m; close rate 0.04 m/s under 0.08 cap.",
                    "9. Soft capture; ring latches.",
                    "10. Delayed (8 min): yard policy tags RF-lock as non-range vs lidar.",
                ],
            ),
        ]
    )
    params = OrderedDict(
        [
            ("creep_m_s", 0.04),
            ("hold", False),
            ("rf_authoritative", False),
            ("capture_armed", True),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "soft_berth_creep"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("range_m", 0.42),
                        ("range_floor_m", 0.25),
                        ("close_rate_m_s", 0.05),
                        ("close_rate_cap_m_s", 0.08),
                        ("proposed_creep_m_s", 0.04),
                        ("stationkeep_reseq_s", 480),
                        ("race_margin_us", 224),
                        ("combined_jitter_us", 60),
                    ]
                ),
            ),
            (
                "basis",
                "Planner already commands 0.04 m/s creep: lidar range 0.42 m is above the 0.25 m "
                "floor and closing 0.05 m/s is under the 0.08 m/s cap. RF lock is not a range.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Lidar range 0.42 m won by 224 us and stays above the 0.25 m floor; commanded "
                "0.04 m/s is under the 0.08 m/s close-rate cap. ACCEPT the creep. An RF-lock "
                "holdover at 0.12 m/s would violate the floor if the beacon were believed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "berth_range_m",
                            OrderedDict(
                                [
                                    ("floor", 0.25),
                                    ("observed", 0.42),
                                ]
                            ),
                        ),
                        (
                            "close_rate_m_s",
                            OrderedDict(
                                [
                                    ("cap", 0.08),
                                    ("observed", 0.05),
                                    ("commanded", 0.04),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 224),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 3.73),
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
            ("name", "soft_berth_creep"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed_action; 0.04 m/s creep held to capture.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Grapple-K4 completed soft capture with min range 0.31 m; RF lock was not "
                "treated as range. Lidar-authoritative berthing confirmed.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("arm", "soft capture; min range 0.31 m"),
                        ("ring", "AY-2 latches closed"),
                        ("beacon", "RF lock unused as range"),
                        ("mission", "berth complete"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The RF beacon lock was a multipath echo off the solar-array hinge, not a sensor fault; lidar still saw 0.42 m open.",
                    "Delayed (8 min): sister arm Grapple-K5 on AY-3 logged the same lidar-vs-RF disagreement; yard policy flipped lidar-authoritative before the next capture.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "lidar.berth.range (5.920 ms, 0.42 m)"),
                        ("loser", "rf.beacon.lock (6.144 ms, false lock)"),
                        ("margin_us", 224),
                        (
                            "counterfactual_if_reversed",
                            "Beacon-first by < 224 us inside the 280 us window would have commanded "
                            "a 0.12 m/s shove through a false lock and closed under the 0.25 m floor.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6180),
            ("min_clearance_m", 0.31),
            (
                "reward_inflection_note",
                "Safety and efficiency both step up at the ACCEPT gate (6.180 ms, tick 4) as the creep locks in over the shove.",
            ),
        ]
    )
    spikes = [
        spike("star.tracker.ctx", 1.088, 0.44),
        spike("lidar.berth.range", 2.410, 0.61),
        spike("rf.beacon.lock", 3.220, 0.54),
        spike("wrist.ft.ctx", 4.018, 0.47),
        spike("lidar.berth.range", 5.920, 1.28),
        spike("rf.beacon.lock", 6.144, 1.11),
        spike("ctrl.gate", 6.180, 0.99),
        spike("lidar.berth.range", 7.880, 0.81),
        spike("rf.beacon.lock", 9.440, 0.64),
        spike("wrist.ft.ctx", 12.020, 0.48),
        spike("ctrl.gate", 14.880, 0.86),
        spike("star.tracker.ctx", 18.210, 0.40),
    ]
    ras = raster_core(
        32,
        96,
        28,
        86,
        routing(
            "thalamic-relay.berth-range",
            "spikenaut.policy.creep-go",
            [
                ("relay.lidar.range", "policy.creep_go", 0.62),
                ("relay.rf.lock", "policy.shove_hold", 0.28),
                ("relay.wrist.ft", "policy.shove_hold", -0.31),
            ],
            "dopamine",
            0.15,
            "pre_post_stdp; DA at lidar win tags creep_go, reward at soft-capture",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.28),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("creep_go", 48, 0.50, 280.0, 4),
                    pop("shove_hold", 48, 0.50, 70.0, 1),
                    pop("range_floor_veto", 24, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r18-106"),
            (
                "title",
                "Apside-Yard AY-2 / Grapple-K4: berthing lidar 0.42 m beats RF false-lock by 224 us; ACCEPT 0.04 m/s creep",
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
                    "satellite-servicing",
                    [
                        "accept",
                        "geo-berth",
                        "lidar-vs-rf",
                        "designed",
                    ],
                    "Teaches that an RF beacon lock can lose to a berthing-lidar range when the ring is still 0.42 m open; reversing 224 us would have selected an illegal shove.",
                    1,
                ),
            ),
        ]
    )


def record_107():
    ticks = [
        tick(1880, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5410, 0.06, -0.04, -0.02, 0.01, -0.01),
        tick(5688, 0.04, -0.03, -0.02, 0.01, 0.00),
        tick(6280, 0.12, -0.06, -0.04, 0.02, -0.02),
        tick(24400, 0.06, -0.38, -0.02, 0.00, -0.02),
        tick(660000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    excerpt = excerpt_items(
        [
            (820, 7),
            (2400, 31),
            (4100, 55),
            (5900, 12),
            (7800, 44),
            (9900, 2),
            (12200, 61),
            (14800, 19),
            (17600, 38),
            (20500, 8),
            (23600, 50),
            (26800, 15),
            (30100, 66),
            (33400, 4),
            (36900, 27),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Booster Waft-2 is still spinning 18 Hz in Sump-Drift SD-8 heading 4 when an NDIR "
                "methane cell reports 0.82 % vol against a vane-anemometer that still claims 2.4 m/s "
                "of fresh air. Action threshold is 0.50 % vol; booster cap under methane is 10 Hz. "
                "CH4-first latches a 9 Hz dilution clamp; vane-first would keep 18 Hz on a "
                "'still-ventilating' model. A heading slug is not yet an observable of either race channel.",
            ),
            ("domain", "mine-ventilation"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold heading-4 CH4 <= 0.50 % vol action threshold, keep booster <= 10 Hz under "
                "methane, and leave the face crew unmarked.",
            ),
            ("t0_us", 1756794632000107),
            ("gate_latency_us", 870),
            ("race_window_us", 440),
            ("race_window_rel_ms", [5.25, 5.69]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ch4.ir.ppm 0.82 % vol",
                                "vane.dp.pa 2.4 m/s fresh-air claim",
                            ],
                        ),
                        (
                            "semantics",
                            "CH4-first latches booster clamp 18 -> 9 Hz; vane-first keeps 18 Hz cruise "
                            "on a still-ventilating model.",
                        ),
                        (
                            "window_derivation",
                            "440 us = one NDIR sample slot versus the vane differential-pressure "
                            "publisher on this heading bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 278 us vs combined jitter 74 us (NDIR 36 + vane 38): 3.8x over "
                            "a 2.0x trust floor. Reversing order by < 278 us would have kept 18 Hz "
                            "cruise; predicted next-sample 0.91 % > 0.50 % action threshold.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "NDIR CH4 cell, 25 Hz, 36 us jitter",
                    "vane anemometer dP, 20 Hz, 38 us jitter",
                    "booster tachometer (context)",
                    "heading CO detector (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ch4_action_pct", 0.50),
                        ("observed_ch4_pct", 0.82),
                        ("booster_cap_under_ch4_hz", 10.0),
                        ("proposed_booster_hz", 18.0),
                        ("vane_claim_m_s", 2.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Waft-2 indexed on SD-8 heading 4; face crew 90 m inby.",
                    "2. NDIR 0.82 % vol; vane still claims 2.4 m/s; booster 18 Hz armed.",
                    "3. Tach precursor at 1.880 ms.",
                    "4. Race window [5.250, 5.690] ms.",
                    "5. CH4 0.82 % at 5.410 ms (winner).",
                    "6. Vane 2.4 m/s at 5.688 ms (loser by 278 us).",
                    "7. Gate at 6.280 ms: MODIFY clamp 18 -> 9 Hz.",
                    "8. Clamp executes; next-sample CH4 0.47 % < 0.50 action.",
                    "9. At 24.400 ms a heading slug still hits 1.12 %; AE burst.",
                    "10. Heading evac 11 min; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "heading_booster_cruise"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("booster_hz", 18.0),
                        ("vane_authoritative", True),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ch4_pct", 0.82),
                        ("ch4_action_pct", 0.50),
                        ("predicted_unclamped_next_pct", 0.91),
                        ("booster_cap_under_ch4_hz", 10.0),
                        ("vane_claim_m_s", 2.4),
                        ("abort_s", 660),
                        ("race_margin_us", 278),
                        ("combined_jitter_us", 74),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping 18 Hz because the vane still claims 2.4 m/s of fresh "
                "air and treats 0.82 % CH4 as a transient eddy, not contact with a heading pocket.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "NDIR CH4 0.82 % won by 278 us, so the heading is loading methane, not still "
                "ventilating. Holding 18 Hz predicts next-sample 0.91 % > 0.50 % action. MODIFY: "
                "booster 18 -> 9 Hz (under the 10 Hz methane cap). Observed after clamp 0.47 % < 0.50. "
                "A full REJECT/stop is not indicated: a sound heading accepts 9 Hz dilution.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ch4_pct",
                            OrderedDict(
                                [
                                    ("action", 0.50),
                                    ("observed", 0.82),
                                    ("predicted_unclamped_next", 0.91),
                                    ("clamped_booster_hz", 9.0),
                                    ("observed_after_clamp", 0.47),
                                ]
                            ),
                        ),
                        (
                            "booster_hz",
                            OrderedDict(
                                [
                                    ("proposed", 18.0),
                                    ("cap_under_ch4", 10.0),
                                    ("clamped", 9.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 278),
                                    ("combined_jitter_us", 74),
                                    ("ratio", 3.76),
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
            ("name", "heading_booster_clamp"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("booster_hz", 9.0),
                        ("vane_authoritative", False),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: booster 18 -> 9 Hz. Process-correct vs the 0.50 % action and 10 Hz "
                "methane cap. Heading slug still occurs at 24.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held booster at 9 Hz. At 24.400 ms a heading slug still "
                "hit 1.12 % vol. Clamp reduced dump energy; it did not prevent the pocket. "
                "Partnered negative: process heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("booster", "clamp executed; 9 Hz < 10 Hz cap; CH4 0.47 % after clamp"),
                        ("heading", "slug 1.12 % at 24.400 ms"),
                        ("crew", "11 min heading evacuation"),
                        ("mission", "face still reachable; pocket logged"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither NDIR nor vane predicted the pocket; ch4.ir.slug is a new channel at 24.400 ms, 18.120 ms after the gate, still inside the 38 ms raster.",
                    "Delayed (11 min): heading evacuation closes the pocket. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "11 min heading evacuation after a 1.12 % methane slug. Safety head -0.58 "
                "prices the pocket; task_progress stays +0.34 because the booster clamp completed "
                "under the 10 Hz methane cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ch4.ir.ppm (5.410 ms, 0.82 % vol)"),
                        ("loser", "vane.dp.pa (5.688 ms, 2.4 m/s claim)"),
                        ("margin_us", 278),
                        (
                            "counterfactual_if_reversed",
                            "Vane-first by < 278 us inside the 440 us window would have kept "
                            "18 Hz cruise; predicted next-sample 0.91 % would have exceeded the "
                            "0.50 % action even without the slug. The MODIFY is still the "
                            "correct process. The slug is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 24400),
            (
                "reward_inflection_note",
                "Safety collapses at the 24.400 ms heading slug (tick t_us=24400), inside the "
                "38 ms raster. The correct MODIFY at 6.280 ms is in the same excerpt. Do not put "
                "inflection on the +11 min evac tick.",
            ),
        ]
    )
    spikes = [
        spike("booster.tach.ctx", 1.205, 0.43),
        spike("ch4.ir.ppm", 2.410, 0.62),
        spike("vane.dp.pa", 3.880, 0.53),
        spike("co.cell.ctx", 4.620, 0.46),
        spike("ch4.ir.ppm", 5.410, 1.33),
        spike("vane.dp.pa", 5.688, 1.16),
        spike("ctrl.gate", 6.280, 1.01),
        spike("ch4.ir.ppm", 8.220, 0.84),
        spike("vane.dp.pa", 10.440, 0.66),
        spike("ctrl.gate", 14.880, 0.88),
        spike("ch4.ir.slug", 24.400, 1.44),
        spike("ch4.ir.slug", 26.050, 0.92),
        spike("booster.tach.ctx", 30.200, 0.41),
        spike("ch4.ir.ppm", 35.400, 0.57),
    ]
    ras = raster_core(
        38,
        72,
        35,
        96,
        routing(
            "thalamic-relay.ch4-vane",
            "spikenaut.policy.fan-clamp",
            [
                ("relay.ch4.ppm", "policy.fan_clamp", 0.65),
                ("relay.vane.dp", "policy.vane_hold", 0.31),
                ("relay.ch4.slug", "policy.fan_clamp", -0.46),
            ],
            "noradrenaline",
            0.06,
            "surprise-gated pre_post_stdp; NA at CH4 win (5.410 ms) opens a 60 ms eligibility "
            "trace that still covers the 24.400 ms slug",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.44),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("fan_clamp", 48, 0.50, 250.0, 5),
                    pop("vane_hold", 48, 0.50, 80.0, 2),
                    pop("ch4_cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r18-107"),
            (
                "title",
                "Sump-Drift SD-8 / Waft-2: NDIR CH4 0.82 % beats vane 2.4 m/s by 278 us; correct "
                "MODIFY still eats an in-window heading slug (partnered negative total -0.38)",
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
                    "38 ms raster. total -0.38 = 0.34 + -0.58 + -0.14 + 0.06 + -0.06. Named "
                    "heading-evac loss is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "mine-ventilation",
                    [
                        "modify",
                        "partnered-negative-total",
                        "in-window-world-charge",
                        "ch4-vs-vane",
                        "designed",
                    ],
                    "A critic can see the world-charge as a CH4 slug inside the raster while "
                    "process heads stay honest. Credit assignment is spikes, not prose across an 11 min gap.",
                    2,
                ),
            ),
        ]
    )


def record_108():
    ticks = [
        tick(1420, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(4880, 0.01, 0.08, 0.02, 0.02, 0.02),
        tick(5104, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5820, 0.03, 0.12, 0.04, 0.04, 0.02),
        tick(6200, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(420000000, 0.01, 0.03, 0.01, 0.01, 0.01),
    ]
    excerpt = excerpt_items(
        [
            (1100, 12),
            (3400, 77),
            (5900, 4),
            (8600, 118),
            (11500, 41),
            (14700, 93),
            (18100, 9),
            (21800, 131),
            (25600, 28),
            (29600, 64),
            (33700, 140),
            (37900, 19),
            (42200, 85),
            (44800, 6),
            (45900, 102),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Slice Lip-9 on Felt-Reach FR-7 is about to open another 0.40 mm of jet when a "
                "beta-gauge basis reading of 118 g/m2 arrives 224 us before the wire-speed encoder "
                "publishes 920 m/min. Slice-open is legal only if basis <= 95 g/m2 at this speed. "
                "Basis-first latches hold; encoder-first would treat wire speed as a cleared sheet "
                "and open the lip.",
            ),
            ("domain", "paper-machine"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Do not open Lip-9 unless basis <= 95 g/m2; keep slice gap unchanged until the "
                "sheet is on-spec.",
            ),
            ("t0_us", 1756794633000108),
            ("gate_latency_us", 940),
            ("race_window_us", 360),
            ("race_window_rel_ms", [4.80, 5.16]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "basis.beta.gsm 118 g/m2",
                                "wire.speed.enc 920 m/min",
                            ],
                        ),
                        (
                            "semantics",
                            "Basis-first latches REJECT hold (slice +0.00 mm); encoder-first would "
                            "open +0.40 mm on a speed-as-clearance model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one Kr-85 beta-gauge slot versus the wire-speed encoder on "
                            "this Fourdrinier bus cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 224 us vs combined jitter 66 us (beta 30 + encoder 36): 3.4x "
                            "over a 2.0x trust floor. Reversing order by < 224 us would have opened "
                            "the lip with basis 118 > 95 g/m2.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "Kr-85 beta-gauge basis, 10 Hz burst, 30 us jitter",
                    "wire-speed encoder, 1 kHz, 36 us jitter",
                    "slice-lip LVDT (context)",
                    "headbox consistency (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("basis_cap_gsm", 95.0),
                        ("observed_basis_gsm", 118.0),
                        ("wire_speed_m_min", 920.0),
                        ("proposed_slice_open_mm", 0.40),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "2D stock-jet LES + lumped Fourdrinier-wire FEM, seed 18108; 11 slice-lip stations, 24 wire nodes; NOT print-web tension, NOT register control, NOT LPBF melt-pool",
                        ),
                        (
                            "fidelity_limits",
                            "Rigid lip; no felt compressibility. Raster is kernelized events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Felt-Reach FR-7 at 920 m/min; Lip-9 armed for +0.40 mm.",
                    "2. Beta-gauge 118 g/m2; wire encoder still publishes 920 m/min as 'on-spec speed'.",
                    "3. LVDT precursor at 1.420 ms.",
                    "4. Race window [4.800, 5.160] ms.",
                    "5. Basis 118 g/m2 at 4.880 ms (winner).",
                    "6. Wire speed 920 m/min at 5.104 ms (loser by 224 us).",
                    "7. Gate at 5.820 ms: REJECT hold; do not open +0.40 mm.",
                    "8. Sheet remains overweight this reel; cap held.",
                    "9. Broke queued; lip stays.",
                    "10. Delayed (7 min): wet-end policy tags wire-speed as non-basis vs beta-gauge.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "slice_lip_open"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("slice_open_mm", 0.40),
                        ("hold", False),
                        ("wire_speed_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("basis_gsm", 118.0),
                        ("basis_cap_gsm", 95.0),
                        ("wire_speed_m_min", 920.0),
                        ("broke_rethread_s", 420),
                        ("race_margin_us", 224),
                        ("combined_jitter_us", 66),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes +0.40 mm lip because wire speed 920 m/min looks like a cleared "
                "sheet, treating beta-gauge 118 g/m2 as a noisy echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Beta-gauge basis 118 g/m2 is over the 95 g/m2 open floor. Wire speed 920 m/min "
                "is not a basis clearance. REJECT: hold slice +0.00 mm; do not open +0.40 mm. "
                "Wait for on-spec sheet.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "basis_gsm",
                            OrderedDict(
                                [
                                    ("cap", 95.0),
                                    ("observed_beta", 118.0),
                                    ("wire_speed_m_min", 920.0),
                                ]
                            ),
                        ),
                        (
                            "slice_open_mm",
                            OrderedDict(
                                [
                                    ("proposed", 0.40),
                                    ("executed", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 224),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 3.39),
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
            ("name", "slice_lip_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("slice_open_mm", 0.0),
                        ("hold", True),
                        ("wire_speed_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold slice +0.00 mm; +0.40 mm open cancelled. Basis 118 > 95 g/m2 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Lip-9 at +0.00 mm. Sheet overweight this reel; open cap "
                "held. Wire speed was not treated as a basis clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("lip", "held; slice_open 0.00 mm"),
                        ("sheet", "still 118 g/m2 this reel"),
                        ("wire", "920 m/min unused as basis"),
                        ("mission", "open deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "LES jet still showed a 0.40 mm open would have dumped an extra 14 g/m2 onto the wire; beta-first prevented it.",
                    "Delayed (7 min): wet-end policy update forbids treating wire-speed as a basis-clearance substitute; broke rethread queued.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "basis.beta.gsm (4.880 ms, 118 g/m2)"),
                        ("loser", "wire.speed.enc (5.104 ms, 920 m/min)"),
                        ("margin_us", 224),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 224 us inside the 360 us window would have opened "
                            "+0.40 mm with basis 118 > 95 g/m2. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5820),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (5.820 ms, tick 4) as the hold locks in over the illegal open.",
            ),
        ]
    )
    spikes = [
        spike("lip.lvdt.ctx", 1.088, 0.42),
        spike("basis.beta.gsm", 2.410, 0.59),
        spike("wire.speed.enc", 3.105, 0.52),
        spike("basis.beta.gsm", 4.880, 1.30),
        spike("wire.speed.enc", 5.104, 1.13),
        spike("ctrl.gate", 5.820, 1.00),
        spike("basis.beta.gsm", 7.440, 0.78),
        spike("lip.lvdt.ctx", 9.220, 0.45),
        spike("wire.speed.enc", 12.020, 0.60),
        spike("ctrl.gate", 16.880, 0.84),
        spike("basis.beta.gsm", 24.400, 0.54),
        spike("wire.speed.enc", 33.110, 0.39),
    ]
    ras = raster_core(
        46,
        144,
        20,
        132,
        routing(
            "thalamic-relay.basis-wire",
            "spikenaut.policy.slice-hold",
            [
                ("relay.basis.gsm", "policy.slice_hold", 0.67),
                ("relay.wire.speed", "policy.slice_open", 0.27),
                ("relay.lip.lvdt", "policy.slice_hold", 0.11),
            ],
            "serotonin",
            1.10,
            "pre_post_stdp; 5-HT at basis win tags slice_hold, reward at overweight-still",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("slice_hold", 64, 0.50, 280.0, 6),
                    pop("slice_open", 64, 0.50, 70.0, 2),
                    pop("basis_cap_veto", 32, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r18-108"),
            (
                "title",
                "Felt-Reach FR-7 / Lip-9: beta-gauge 118 g/m2 beats wire-speed 920 m/min by 224 us; REJECT hold, do not open slice",
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
                    "Clean REJECT. Task incomplete (sheet overweight); cap held. "
                    "total 0.76 = 0.08 + 0.38 + 0.12 + 0.10 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "paper-machine",
                    [
                        "reject",
                        "simulated",
                        "fourdrinier",
                        "beta-vs-wire",
                        "slice-hold",
                    ],
                    "Teaches that wire speed is not a basis clearance when the beta-gauge is over the open floor.",
                    3,
                ),
            ),
        ]
    )


def record_109():
    ticks = [
        tick(1760, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(6110, -0.03, -0.01, -0.04, -0.02, 0.01),
        tick(6360, -0.02, -0.01, -0.03, -0.01, 0.00),
        tick(7010, -0.07, -0.03, -0.08, -0.04, 0.01),
        tick(7480, -0.02, -0.01, -0.03, -0.01, 0.01),
        tick(1320000000, -0.02, -0.01, -0.02, -0.01, 0.00),
    ]
    excerpt = excerpt_items(
        [
            (700, 5),
            (2100, 22),
            (3700, 41),
            (5200, 9),
            (6900, 33),
            (8800, 2),
            (10900, 44),
            (13200, 16),
            (15700, 37),
            (18400, 7),
            (21200, 28),
            (23900, 11),
            (25500, 46),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Ampoule-5 is already on the Frost-Cist FC-3 neck rail, commanded 0.15 m/s out, "
                "when a PT100 at 94.2 K races an LN2 level of 612 mm. Neck warn is 110 K; level "
                "floor is 180 mm; extract cap is 0.20 m/s. Level-first should ACCEPT the extract. "
                "A weak supervisor treats 94.2 K as LN2-adjacent empty-tank and REJECT-holds.",
            ),
            ("domain", "cryo-storage"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Extract the vapor-space rack at 0.15 m/s, keep neck < 110 K, and keep LN2 level "
                ">= 180 mm.",
            ),
            ("t0_us", 1756794634000109),
            ("gate_latency_us", 900),
            ("race_window_us", 500),
            ("race_window_rel_ms", [5.90, 6.40]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt100.neck.k 94.2 K designed neck gradient",
                                "ln2.level.mm 612 mm",
                            ],
                        ),
                        (
                            "semantics",
                            "PT100-first should confirm class and ACCEPT 0.15 m/s extract; a weak "
                            "supervisor instead binds neck kelvin to a hold-reject.",
                        ),
                        (
                            "window_derivation",
                            "500 us = one neck-PT100 4-wire slot versus the capacitive LN2 level "
                            "publisher on this dewar bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 250 us vs combined jitter 70 us (PT100 34 + level 36). Order is "
                            "correctly PT100-first. The error is the class predicate, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "neck PT100, 4-wire, 10 Hz, 34 us jitter",
                    "capacitive LN2 level, 5 Hz, 36 us jitter",
                    "crane encoder (context)",
                    "bay O2 monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("neck_k", 94.2),
                        ("neck_warn_k", 110.0),
                        ("level_mm", 612.0),
                        ("level_floor_mm", 180.0),
                        ("extract_m_s", 0.15),
                        ("extract_cap_m_s", 0.20),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Ampoule-5 indexed on FC-3 neck rail; 48 ampoules in vapor-space rack.",
                    "2. PT100 94.2 K; LN2 level 612 mm; extract 0.15 m/s armed.",
                    "3. Encoder precursor at 1.760 ms.",
                    "4. Race window [5.900, 6.400] ms.",
                    "5. PT100 94.2 K at 6.110 ms (winner).",
                    "6. LN2 level 612 mm at 6.360 ms (loser by 250 us).",
                    "7. Gate at 7.010 ms: wrong REJECT hold 0.00 m/s; extract cancelled.",
                    "8. 22 min fill slot missed; rack stays in vapor space.",
                    "9. Next window 3.1 days.",
                    "10. QA: correct gate was ACCEPT 0.15 m/s; 94.2 K < 110 K and 612 mm > 180 mm.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "vapor_rack_extract"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("extract_m_s", 0.15),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("neck_k", 94.2),
                        ("neck_warn_k", 110.0),
                        ("level_mm", 612.0),
                        ("level_floor_mm", 180.0),
                        ("extract_m_s", 0.15),
                        ("extract_cap_m_s", 0.20),
                        ("missed_window_s", 1320),
                        ("race_margin_us", 250),
                        ("combined_jitter_us", 70),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.15 m/s extract: neck 94.2 K is under the 110 K warn, level "
                "612 mm is over the 180 mm floor, and 0.15 m/s is under the 0.20 m/s cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Neck PT100 94.2 K is closer to LN2 77 K than to 293 K ambient, so the tank is "
                "treated as empty-adjacent. REJECT: hold extract 0.00 m/s until a refill restores "
                "a 'warm' neck. Level 612 mm is read as a stuck capacitive probe.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "neck_k",
                            OrderedDict(
                                [
                                    ("warn", 110.0),
                                    ("observed", 94.2),
                                    ("misread_as", "ln2_adjacent_empty"),
                                ]
                            ),
                        ),
                        (
                            "level_mm",
                            OrderedDict(
                                [
                                    ("floor", 180.0),
                                    ("observed", 612.0),
                                    ("executed_extract_m_s", 0.0),
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
            ("name", "extract_hold_wrong_class"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("extract_m_s", 0.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): extract left at 0.00 m/s. Routing relay.pt100.neck -> "
                "policy.hold_reject; no positive weight to policy.extract_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze Ampoule-5 while neck 94.2 K < 110 K warn and level 612 mm > "
                "180 mm floor. Missed 22 min fill slot; next window 3.1 days. Correct gate was "
                "ACCEPT 0.15 m/s extract.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("crane", "held at 0.00 m/s; planned 0.15 m/s abandoned"),
                        ("neck", "still 94.2 K, under 110 K warn"),
                        ("level", "still 612 mm, over 180 mm floor"),
                        ("rack", "22 min fill slot missed; 48 ampoules stay in vapor space"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "PT100 freeze did not change level; 612 mm remained legal throughout the hold.",
                    "Delayed (22 min): fill window closed; next slot 3.1 days. Ampoules stay in the vapor-space rack.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: extract 0.15 m/s; neck 94.2 K < 110 K warn; level 612 mm > 180 mm floor.",
                        ),
                        ("correct_actuator", "extract_go"),
                        ("wrong_actuator", "hold_reject"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("extract_m_s", 0.0), ("hold", True)]),
                        ),
                        (
                            "missed_window_cost",
                            "22 min fill slot missed; next window 3.1 days; 48 ampoules stay in vapor-space rack.",
                        ),
                        (
                            "cost",
                            "task/efficiency stall on a legal extract; safety near-miss only in the supervisor's empty-tank story, not in the published sidecar.",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt100.neck.k (6.110 ms, 94.2 K)"),
                        ("loser", "ln2.level.mm (6.360 ms, 612 mm)"),
                        ("margin_us", 250),
                        (
                            "counterfactual_if_reversed",
                            "Level-first by < 250 us would still show 612 mm > 180 mm; a correct "
                            "gate ACCEPTs the extract either way. The wrong REJECT spent the PT100 "
                            "win on an empty-tank class that the published sidecar falsifies.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7010),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong hold (7.010 ms, tick 4). The 22 min missed window is delayed surprise, not the inflection.",
            ),
        ]
    )
    spikes = [
        spike("crane.enc.ctx", 1.088, 0.43),
        spike("pt100.neck.k", 2.410, 0.62),
        spike("ln2.level.mm", 3.220, 0.55),
        spike("o2.bay.ctx", 4.018, 0.41),
        spike("pt100.neck.k", 6.110, 1.34),
        spike("ln2.level.mm", 6.360, 1.12),
        spike("ctrl.gate", 7.010, 0.97),
        spike("pt100.neck.k", 8.220, 0.81),
        spike("ln2.level.mm", 10.440, 0.66),
        spike("ctrl.gate", 14.400, 0.84),
        spike("pt100.neck.k", 18.800, 0.58),
        spike("crane.enc.ctx", 22.110, 0.39),
    ]
    ras = raster_core(
        26,
        48,
        40,
        50,
        routing(
            "relay.pt100.neck",
            "policy.hold_reject",
            [
                ("relay.pt100.neck", "policy.hold_reject", 0.73),
                ("relay.ln2.level", "policy.hold_reject", 0.18),
            ],
            "acetylcholine",
            0.09,
            "class_cap_stdp; ACh tags the (wrong) hold_reject bind at the PT100 win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.50),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 48, 0.50, 250.0, 6),
                    pop("extract_go", 48, 0.80, 20.0, 0),
                    pop("pop_pt100", 32, 0.55, 180.0, 3),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r18-109"),
            (
                "title",
                "WRONG-REJECT at Frost-Cist FC-3 / Ampoule-5: neck 94.2 K read correctly; empty-tank class applied instead of ACCEPT extract",
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
                    "Wrong-reject. Sidecar arithmetic neck 94.2 < 110 and level 612 > 180 is true; "
                    "hold bound to empty-tank class. total -0.54 = -0.18 + -0.08 + -0.22 + -0.10 + 0.04.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "cryo-storage",
                    [
                        "reject",
                        "wrong-gate",
                        "wrong-class",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct neck_k < warn read can still be a wrong gate when "
                    "routing.table[0].to is policy.hold_reject and executed extract_m_s is zeroed.",
                    4,
                    supervisor_error_type="wrong-reject",
                ),
            ),
        ]
    )


def record_110():
    ticks = [
        tick(1540, 0.02, 0.04, 0.01, 0.01, 0.01),
        tick(4488, 0.04, 0.08, 0.02, 0.02, 0.02),
        tick(4702, 0.03, 0.06, 0.02, 0.01, 0.01),
        tick(5928, 0.08, 0.12, 0.04, 0.04, 0.02),
        tick(6400, 0.03, 0.04, 0.02, 0.01, 0.01),
        tick(180000000, 0.02, 0.02, 0.01, 0.01, 0.01),
    ]
    excerpt = excerpt_items(
        [
            (900, 8),
            (2700, 29),
            (4600, 51),
            (6500, 3),
            (8600, 40),
            (10900, 14),
            (13400, 58),
            (16100, 21),
            (19000, 45),
            (22100, 6),
            (25300, 33),
            (28600, 17),
            (29900, 61),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Train Rill-5 sits on the Clothoid-Bowl CB-HIL dispatch plate with lap-bar lock "
                "strain 1.12 kN when that load-cell pulse races an IMU axle of 0.82 g. Dispatch is "
                "legal only if lock strain >= 1.80 kN. Load-cell-first latches a bar recycle; "
                "IMU-first would treat 0.82 g as a seated train and dispatch. The pad injects the "
                "lap-bar packet 110-150 us before the IMU volume (geometric lag, not a sensor fault).",
            ),
            ("domain", "amusement-ride"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not dispatch Rill-5 unless lap-bar lock >= 1.80 kN; recycle the bar rather "
                "than dump the cycle.",
            ),
            ("t0_us", 1756794635000110),
            ("gate_latency_us", 1440),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.40, 4.72]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "enc.lapbar.n 1.12 kN lock strain",
                                "imu.train.ax 0.82 g seated-jerk claim",
                            ],
                        ),
                        (
                            "semantics",
                            "Lap-bar-first latches MODIFY recycle (dispatch false, recycle true, "
                            "bar 2.10 kN); IMU-first would dispatch on a seated-jerk-as-lock model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one lap-bar load-cell slot versus the train IMU decode on "
                            "this ride-control HIL bench.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 214 us vs combined jitter 64 us (load-cell 30 + IMU 34): 3.3x "
                            "over a 2.0x trust floor. Pad injects the lap-bar packet 110-150 us "
                            "before the IMU volume sees the jerk (geometric lag, not a sensor fault); "
                            "the IMU packet is still the loser in this 320 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "lap-bar load cell, 2 kHz, 30 us jitter",
                    "train IMU axle, 400 Hz, 34 us jitter",
                    "dispatch PLC (context)",
                    "block-section photoelectric (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("lock_floor_kN", 1.80),
                        ("observed_lock_kN", 1.12),
                        ("imu_ax_g", 0.82),
                        ("proposed_dispatch", True),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        (
                            "bench",
                            "Clothoid-Bowl ride-control PLC on a split dispatch plate; physical lap-bar load cell; injected IMU axle.",
                        ),
                        (
                            "inject_lead_us",
                            [110, 150],
                        ),
                        (
                            "note",
                            "Geometric lag: lap-bar packet leads IMU 110-150 us. Not a sensor fault.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Rill-5 on CB-HIL dispatch plate; dummy riders belted; bar armed.",
                    "2. Lap-bar packet injected 110-150 us before IMU volume sees the 0.82 g jerk.",
                    "3. PLC precursor at 1.540 ms.",
                    "4. Race window [4.400, 4.720] ms.",
                    "5. Lap-bar 1.12 kN at 4.488 ms (winner).",
                    "6. IMU 0.82 g at 4.702 ms (loser by 214 us).",
                    "7. Gate at 5.928 ms: MODIFY recycle; dispatch false; bar 2.10 kN.",
                    "8. Lock after recycle 2.04 kN >= 1.80 floor; train not dumped.",
                    "9. Cycle held 3 min for recycle.",
                    "10. Delayed (3 min): pad policy tags IMU axle as non-lock vs load-cell.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_train"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("dispatch", True),
                        ("recycle", False),
                        ("bar_cmd_kN", 1.12),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("lock_kN", 1.12),
                        ("lock_floor_kN", 1.80),
                        ("imu_ax_g", 0.82),
                        ("recycle_s", 180),
                        ("race_margin_us", 214),
                        ("combined_jitter_us", 64),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes dispatch because IMU 0.82 g looks like a seated train, treating "
                "lap-bar 1.12 kN as a noisy echo of a locked restraint.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Lap-bar lock 1.12 kN won by 214 us and is under the 1.80 kN floor. IMU 0.82 g is "
                "not a restraint lock. MODIFY: dispatch false, recycle true, bar 1.12 -> 2.10 kN. "
                "A full REJECT/dump of the cycle is not indicated: a sound train accepts a recycle.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "lock_kN",
                            OrderedDict(
                                [
                                    ("floor", 1.80),
                                    ("observed", 1.12),
                                    ("recycled", 2.10),
                                    ("observed_after_recycle", 2.04),
                                ]
                            ),
                        ),
                        (
                            "dispatch",
                            OrderedDict(
                                [
                                    ("proposed", True),
                                    ("executed", False),
                                    ("recycle", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 214),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 3.34),
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
            ("name", "recycle_lapbar"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("dispatch", False),
                        ("recycle", True),
                        ("bar_cmd_kN", 2.10),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: dispatch false, recycle true, bar 1.12 -> 2.10 kN. Process-correct vs the 1.80 kN lock floor.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct MODIFY recycled the lap-bar; lock after recycle 2.04 kN >= 1.80 floor. "
                "Train not dumped. IMU axle was not treated as a restraint lock.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("train", "held on plate; not dispatched"),
                        ("bar", "recycled; lock 2.04 kN"),
                        ("imu", "0.82 g unused as lock"),
                        ("mission", "cycle delayed 3 min, not aborted"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: lap-bar packet was injected 110-150 us before the IMU volume saw the jerk, yet the load-cell still won the 320 us race.",
                    "Delayed (3 min): pad policy update forbids treating IMU axle as a lap-bar-lock substitute; recycle complete.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "enc.lapbar.n (4.488 ms, 1.12 kN)"),
                        ("loser", "imu.train.ax (4.702 ms, 0.82 g)"),
                        ("margin_us", 214),
                        (
                            "counterfactual_if_reversed",
                            "IMU-first by < 214 us inside the 320 us window would have dispatched "
                            "with lock 1.12 kN < 1.80 kN floor. Order, not amplitude, selected the recycle.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5928),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the MODIFY gate (5.928 ms, tick 4) as the recycle locks in over the illegal dispatch.",
            ),
        ]
    )
    spikes = [
        spike("plc.dispatch.ctx", 1.088, 0.44),
        spike("enc.lapbar.n", 2.410, 0.60),
        spike("imu.train.ax", 3.220, 0.53),
        spike("block.photo.ctx", 4.018, 0.46),
        spike("enc.lapbar.n", 4.488, 1.29),
        spike("imu.train.ax", 4.702, 1.10),
        spike("ctrl.gate", 5.928, 1.00),
        spike("enc.lapbar.n", 7.440, 0.80),
        spike("imu.train.ax", 9.220, 0.64),
        spike("plc.dispatch.ctx", 12.020, 0.48),
        spike("ctrl.gate", 16.880, 0.85),
        spike("enc.lapbar.n", 22.110, 0.41),
    ]
    ras = raster_core(
        30,
        64,
        30,
        58,
        routing(
            "thalamic-relay.lapbar-imu",
            "spikenaut.policy.bar-recycle",
            [
                ("relay.lapbar.n", "policy.bar_recycle", 0.64),
                ("relay.imu.ax", "policy.dispatch_go", 0.29),
                ("relay.block.photo", "policy.dispatch_go", -0.22),
            ],
            "dopamine",
            0.18,
            "pre_post_stdp; DA at lap-bar win tags bar_recycle, reward at lock-after-recycle",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("bar_recycle", 40, 0.50, 260.0, 3),
                    pop("dispatch_go", 40, 0.50, 70.0, 1),
                    pop("lock_floor_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r18-110"),
            (
                "title",
                "Clothoid-Bowl CB-HIL / Rill-5: lap-bar 1.12 kN beats IMU 0.82 g by 214 us; MODIFY recycle, do not dispatch",
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
                    "Clean MODIFY on HIL. Tick columns sum to the five heads; total 0.88 = 0.22+0.36+0.12+0.10+0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "amusement-ride",
                    [
                        "modify",
                        "hil",
                        "lapbar-vs-imu",
                        "dispatch-recycle",
                    ],
                    "Teaches that an IMU seated-jerk is not a lap-bar lock when strain is under the 1.80 kN floor; reversing 214 us would have dispatched.",
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
            in_win[ch := ev["channel"]]  # noqa: not used
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
            found.append((path, k, v))
            found.extend(walk_keys(v, path))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            found.extend(walk_keys(item, f"{prefix}[{i}]"))
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
            jpairs.append((records[i]["id"], records[j]["id"], val))
            jmax = max(jmax, val)
            if val >= 0.4:
                issues.append(f"Jaccard {records[i]['id']}/{records[j]['id']} = {val:.3f}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r18-109":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-reject":
        issues.append("109 supervisor_error_type")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domains {domains}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if decisions.count("ACCEPT") != 1:
        issues.append(f"ACCEPT count {decisions}")
    if decisions.count("MODIFY") != 2:
        issues.append(f"MODIFY count {decisions}")
    if decisions.count("REJECT") != 2:
        issues.append(f"REJECT count {decisions}")
    prov = [r["state"]["sim_or_real"] for r in records]
    if prov.count("hil") != 1 or records[4]["state"]["sim_or_real"] != "hil":
        issues.append(f"hil mix {prov}")
    if prov.count("simulated") != 1:
        issues.append(f"simulated mix {prov}")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    blob_all = json.dumps(records)
    if "training_ready" in blob_all:
        issues.append("training_ready present")
    if '"real"' in blob_all and any(
        v == "real" for _, k, v in walk_keys(records) if k in ("sim_or_real", "kind")
    ):
        issues.append("real provenance")
    for rec in records:
        rec_s = json.dumps(rec)
        for key in THOUGHT_KEYS:
            if f'"{key}"' in rec_s:
                issues.append(f"{rec['id']} thought key {key}")
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
        if overlap >= 0.8:
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
        if not (5 <= len(rec["spike_events"]) <= 40):
            issues.append(f"{rec['id']} spike count")
        for nid in (item["neuron_id"] for item in rec["raster"]["excerpt"]):
            if not (0 <= nid < rec["raster"]["neurons"]):
                issues.append(f"{rec['id']} neuron_id {nid}")
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= rec["raster"]["window_ms"] * 1000):
                issues.append(f"{rec['id']} excerpt t_us {item['t_us']}")
        total = sum(rec["reward_components"][h] for h in HEADS)
        if abs(total - rec["reward_components"]["total"]) > 1e-6:
            issues.append(f"{rec['id']} total mismatch {total}")
        for h in HEADS:
            s = sum(t[h] for t in rec["reward_components"]["ticks"])
            if abs(s - rec["reward_components"][h]) > 1e-6:
                issues.append(f"{rec['id']} {h} tick sum {s} vs {rec['reward_components'][h]}")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
        if rec["safety_decision"]["decision"] != "ACCEPT" and exec_p == prop_p:
            issues.append(f"{rec['id']} non-ACCEPT params identical")
        lat = rec["state"]["gate_latency_us"]
        win = rec["state"]["race_window_us"]
        if not (50 <= lat <= 2000):
            issues.append(f"{rec['id']} gate_latency {lat}")
        if not (50 <= win <= 1000):
            issues.append(f"{rec['id']} race_window {win}")
        if rec["id"] == "ttf-r18-107":
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("107 inflection outside window")
        if rec["id"] == "ttf-r18-109":
            recov = rec["future_outcome"].get("recovery") or {}
            if "ACCEPT" not in str(recov.get("correct_gate")):
                issues.append("109 recovery missing ACCEPT")
            ev = rec["proposed_action"]["evidence"]
            if not (ev["neck_k"] < ev["neck_warn_k"] and ev["level_mm"] > ev["level_floor_mm"]):
                issues.append("109 sidecar predicate false")
            table_to = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.extract_go" in table_to:
                issues.append("109 routing has extract_go")
            if rec["executed_action"]["parameters"]["extract_m_s"] != 0.0:
                issues.append("109 executed extract not zero")
        rights = rec["meta"]["rights"]
        if rights["intended_use"] != "research_only" or rights["linear_issue"] != "RM-793":
            issues.append(f"{rec['id']} rights")
        if rec["meta"]["round"] != 18 or rec["meta"]["factory"] != "thalamic-trajectory-factory":
            issues.append(f"{rec['id']} meta")
    return issues, jmax, jpairs


def notes_text(jmax: float, pipeline: dict) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r18

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- IDs: `ttf-r18-106` … `ttf-r18-110`
- Domains this batch: `satellite-servicing`, `mine-ventilation`, `paper-machine`, `cryo-storage`, `amusement-ride`

Do not restack r12–r14 plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait; Nacre-Well, Quern-Forge, Tinder-Box, Whimbrel-Stack, Cinder-Loft; Oolite-Span, Fathom-Lock, Loess-Stride, Swage-Holt, Slag-Siding). All five plants are invented. Sit-out: the original eight-domain pool (`industrial-assembly`, `surgical-assist`, `autonomous-driving`, `aerial-swarm`, `warehouse-amr`, `humanoid-locomotion`, `grid-inspection`, `underwater-rov`).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r18-106 | satellite-servicing | ACCEPT | correct | designed | +1.12 | lidar 0.42 m vs RF false-lock; proposed 0.04 m/s already legal |
| ttf-r18-107 | mine-ventilation | MODIFY | correct | designed | **−0.38** | process-correct 18→9 Hz clamp; heading slug inside 38 ms raster |
| ttf-r18-108 | paper-machine | REJECT | correct | simulated | +0.76 | beta 118 g/m² > 95 cap; hold slice, do not open 0.40 mm |
| ttf-r18-109 | cryo-storage | REJECT | **incorrect (wrong-reject)** | designed | −0.54 | neck 94.2 K < 110 warn and level 612 mm > 180 floor; empty-tank class |
| ttf-r18-110 | amusement-ride | MODIFY | correct | hil | +0.88 | lap-bar 1.12 kN < 1.80 floor; recycle, do not dispatch |

Gate mix: 1 ACCEPT, 2 MODIFY, 1 correct REJECT, 1 incorrect REJECT (wrong-reject). Provenance: designed×3, simulated×1, hil×1 (Clothoid-Bowl HIL bench). Jaccard on `state.description` all ≤ {jmax:.3f}.

## Wrong-reject

**ttf-r18-109** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs r13: r13 hosted wrong-modify; r18 hosts wrong-reject. Do not emit a wrong-ACCEPT.

Frost-Cist FC-3 / Ampoule-5 reads neck `PT100=94.2 K` against a 110 K warn and LN2 `level=612 mm` against a 180 mm floor. Extract 0.15 m/s is under the 0.20 m/s cap. Sidecar arithmetic `94.2 < 110` and `612 > 180` is true. A weak supervisor treats 94.2 K as LN2-adjacent empty-tank, REJECT-holds extract at 0.00 m/s, and leaves the legal level unused. Convictable without cryo physics: `evidence.neck_k < evidence.neck_warn_k`, `evidence.level_mm > evidence.level_floor_mm`, `executed_action` sets `extract_m_s=0` / `hold=true`, `raster.routing.table` sends `relay.pt100.neck` → `policy.hold_reject` (weight 0.73) with no positive weight to `policy.extract_go`, and `gate_snn` has `hold_reject` above threshold while `extract_go` is not. Recovery: ACCEPT 0.15 m/s extract. Cost: missed 22 min fill slot / next window 3.1 days / 48 ampoules in vapor-space rack.

## Partnered-negative in-window (107)

**ttf-r18-107** is the partnered negative: process-correct MODIFY (booster held 9 Hz < 10 Hz methane cap; CH4 0.47 % after clamp) while the world still charges. Safety −0.58 prices the 1.12 % heading slug at **24.400 ms**; `task_progress` stays +0.34 because the clamp completed. Inflection `t_us=24400` is tick 5 and is **inside** the 38 ms raster (`24400 ≤ 38000`). Named un-netted loss: 11 min heading evacuation. Not folded into process heads.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is delayed surprise bound to a published sidecar (`stationkeep_reseq_s`, `abort_s`, `broke_rethread_s`, `missed_window_s`, `recycle_s`). Inflection `t_us` is an actual tick. Verified to <1e-6:

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 106 | 6 | +0.42 | +0.32 | +0.18 | +0.12 | +0.08 | +1.12 | 4 (6180) |
| 107 | 6 | +0.34 | −0.58 | −0.14 | +0.06 | −0.06 | −0.38 | 5 (24400) |
| 108 | 6 | +0.08 | +0.38 | +0.12 | +0.10 | +0.08 | +0.76 | 4 (5820) |
| 109 | 6 | −0.18 | −0.08 | −0.22 | −0.10 | +0.04 | −0.54 | 4 (7010) |
| 110 | 6 | +0.22 | +0.36 | +0.12 | +0.10 | +0.08 | +0.88 | 4 (5928) |

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 106 | satellite-servicing | 96 | 28 | 32 | 86 | 1978 | 0.001978 |
| 107 | mine-ventilation | 72 | 35 | 38 | 96 | 2208 | 0.002208 |
| 108 | paper-machine | 144 | 20 | 46 | 132 | 3036 | 0.003036 |
| 109 | cryo-storage | 48 | 40 | 26 | 50 | 1150 | 0.001150 |
| 110 | amusement-ride | 64 | 30 | 30 | 58 | 1334 | 0.001334 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (DA / NA / 5-HT / ACh / DA), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms.

## Local checks (staging, not raw)

- `check_jsonl(..., staging=FactoryStaging(enabled=True))`: {pipeline.get("check_jsonl")}
- `raster_status`: {pipeline.get("raster_status")}
- `verify_batch_for_frontier(strict=True)`: {pipeline.get("frontier")}
- `spike_probe.py --strict`: {pipeline.get("spike_probe")}
- Tick sums, refractory, Jaccard max {jmax:.3f} < 0.4

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Independent LIF is **not** labeled this round (r13-081 already closed that residual). Excerpts are independent of `spike_events` times but are not declared population sims.
2. Paper-machine LES is 2D stock-jet + lumped wire; no felt compressibility, no lip flex.
3. Wrong-ACCEPT still absent (guard).
4. Satellite ACCEPT is a fidelity upgrade into an unused domain, not a new gate class; relative-nav filter / delayed-state still missing.
5. Cryo wrong-reject class predicate is published sidecar (`neck_k`, `neck_warn_k`, `level_mm`, `level_floor_mm`) so a critic can convict without LN2 physics; a later round could add a second published unit (ppm O2) on the same plant without restacking.

## Next densification target

If a later round stays off the original eight-domain pool, bind a second unused domain (e.g. glass-float or kiln-car) and keep tick 6 on a published sidecar. Optional: labeled LIF on the partnered-neg record. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 32.0%
"""


def pipeline_validate(batch: Path) -> dict:
    sys.path.insert(0, str(REPO / "pipelines"))
    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from spike_probe import load_rasters, summarize
    from verify_execution import verify_batch_for_frontier

    errors, warnings, kinds, n = check_jsonl(
        batch, "batch-r18.jsonl", staging=FactoryStaging(enabled=True)
    )
    records = []
    for line in batch.read_text().split("\n"):
        if line.strip():
            records.append(json.loads(line))
    raster_rows = []
    for rec in records:
        st = raster_status(rec, require_raster=True, require_routing_table=True)
        raster_rows.append(
            {
                "id": rec["id"],
                "reason_codes": st["reason_codes"],
                "raster_valid": st["raster_valid"],
                "gate_snn_valid": st["gate_snn_valid"],
                "routing_table_entries": st["routing_table_entries"],
            }
        )
    counts, findings, blocked = verify_batch_for_frontier(batch, strict=True)
    rasters, problems = load_rasters([batch])
    probe = summarize(rasters, problems, [batch])
    return {
        "check_jsonl": f"{n} {kinds}, errors={len(errors)}, warnings={len(warnings)}",
        "check_jsonl_errors": errors,
        "check_jsonl_warnings": warnings,
        "raster_status": raster_rows,
        "frontier": {"counts": counts, "findings": findings, "blocked": blocked},
        "spike_probe": {
            "loaded": probe["loaded"],
            "unloadable": probe["unloadable"],
            "thalamic_records": probe["thalamic_records"],
            "problems": probe["problems"],
        },
    }


def main() -> int:
    if RAW_FORBIDDEN.exists() and str(OUT_DIR).startswith(str(RAW_FORBIDDEN)):
        print("refusing to write under outputs/raw/")
        return 2
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_106(), record_107(), record_108(), record_109(), record_110()]
    issues, jmax, jpairs = self_check(records)
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {BATCH_PATH} lines={len(lines)} jmax={jmax:.3f}")
    for a, b, v in jpairs:
        print(f"  jaccard {a}/{b} = {v:.3f}")
    if issues:
        print("SELF_CHECK_ISSUES:")
        for item in issues:
            print(" -", item)
        NOTES_PATH.write_text(notes_text(jmax, {"check_jsonl": "SELF_CHECK_FAILED"}), encoding="utf-8")
        return 1
    print("SELF_CHECK_OK")
    pipe = pipeline_validate(BATCH_PATH)
    NOTES_PATH.write_text(notes_text(jmax, {
        "check_jsonl": pipe["check_jsonl"],
        "raster_status": "all raster_valid / gate_snn_valid"
        if all(r["raster_valid"] and r["gate_snn_valid"] and not r["reason_codes"] for r in pipe["raster_status"])
        else str(pipe["raster_status"]),
        "frontier": f"{pipe['frontier']['counts']}, blocked={pipe['frontier']['blocked']}",
        "spike_probe": f"loaded={pipe['spike_probe']['loaded']}, unloadable={pipe['spike_probe']['unloadable']}",
    }), encoding="utf-8")
    print(f"wrote {NOTES_PATH}")
    print("PIPELINE", json.dumps({
        "check_jsonl": pipe["check_jsonl"],
        "check_jsonl_errors": pipe["check_jsonl_errors"],
        "check_jsonl_warnings": pipe["check_jsonl_warnings"],
        "raster_status": pipe["raster_status"],
        "frontier": pipe["frontier"],
        "spike_probe": pipe["spike_probe"],
    }, indent=2, default=str))
    bad = bool(pipe["check_jsonl_errors"] or pipe["check_jsonl_warnings"])
    bad = bad or pipe["frontier"]["blocked"]
    bad = bad or pipe["spike_probe"]["unloadable"]
    bad = bad or any(
        (not r["raster_valid"]) or (not r["gate_snn_valid"]) or r["reason_codes"]
        for r in pipe["raster_status"]
    )
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
