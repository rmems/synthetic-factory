def record_326():
    excerpt, extra = lif_326_excerpt()
    ticks = [
        tick(2040, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5100, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5280, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5720, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22800, 0.06, -0.40, -0.04, -0.01, -0.01),
        tick(660000000, 0.02, -0.04, -0.03, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Needle-N8 is already 2.68 N at the fascia face on Cannula-Brae theatre CB-2 when "
                "a 2 kHz tip FT sample races the irrigation encoder. Published tip-force cap is "
                "2.50 N; cruise irrigation at 24 mL/min would drive the next sample over cap before "
                "the assistant can back the cannula. A fascia plane already seated still micro-tears "
                "inside the 42 ms raster after a process-correct irrigation clamp.",
            ),
            ("domain", "surgical-assist"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep Needle-N8 tip force <= 2.50 N on CB-2, finish the fascia pass, and do not "
                "dump irrigation through a torn plane.",
            ),
            ("t0_us", 1756850400000326),
            ("gate_latency_us", 620),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.10, 5.46]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.tip.N 2.68 N over 2.50 cap",
                                "enc.irr.mlpm 24 mL/min with suction PT 9 kPa under 16",
                            ],
                        ),
                        (
                            "semantics",
                            "Tip-first latches irrigation clamp 24 -> 11 mL/min; encoder-first keeps "
                            "24 on a still-under-suction model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one tip FT slot versus the irrigation encoder publisher on "
                            "this surgical-assist bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (tip 26 + encoder 32): 3.10x "
                            "over a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 24 mL/min; predicted next tip 2.84 N would miss "
                            "the 2.50 cap even without the fascia tear.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "tip FT, 2 kHz, 26 us jitter",
                    "irrigation encoder, 1 kHz, 32 us jitter",
                    "fascia AE puck (context)",
                    "suction PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("tip_cap_N", 2.50),
                        ("observed_tip_N", 2.68),
                        ("irr_ml_min", 24.0),
                        ("suction_kpa", 9.0),
                        ("suction_cap_kpa", 16.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Needle-N8 indexed on Cannula-Brae CB-2; irrigation 24 mL/min; tip 2.68 N.",
                    "2. Suction 9 kPa under 16 cap; fascia pass armed.",
                    "3. Encoder precursor at 2.400 ms.",
                    "4. Race window [5.100, 5.460] ms.",
                    "5. ft.tip.N 2.68 at 5.100 ms (winner).",
                    "6. enc.irr.mlpm 24 at 5.280 ms (loser by 180 us).",
                    "7. Gate at 5.720 ms: MODIFY clamp irrigation 24 -> 11 mL/min.",
                    "8. After clamp tip 2.22 N <= 2.50; suction still 9 kPa.",
                    "9. At 22.800 ms a fascia micro-tear dumps 8 mL into the field.",
                    "10. 11 min fat-graft isolate (abort_s=660); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_irrigation"),
            (
                "parameters",
                OrderedDict(
                    [("irr_ml_min", 24.0), ("tip_N", 2.68), ("suction_kpa", 9.0)]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("tip_N", 2.68),
                        ("tip_cap_N", 2.50),
                        ("predicted_unclamped_next_N", 2.84),
                        ("irr_ml_min", 24.0),
                        ("suction_kpa", 9.0),
                        ("suction_cap_kpa", 16.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 660),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 24 mL/min because suction 9 kPa is under 16, treating the 2.68 N "
                "tip reading as a wet-cell smear rather than a force-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Tip 2.68 N won by 180 us, so the cannula is over the 2.50 N force cap, not still "
                "a suction-pressure story. Holding 24 mL/min predicts next-sample 2.84 N > 2.50. "
                "MODIFY: irrigation 24 -> 11 mL/min. Observed after clamp 2.22 N <= 2.50. A full "
                "REJECT is not indicated: a clear field accepts 11 mL/min.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tip_force_N",
                            OrderedDict(
                                [
                                    ("cap", 2.50),
                                    ("observed", 2.68),
                                    ("predicted_unclamped_next", 2.84),
                                    ("clamped_irr_ml_min", 11.0),
                                    ("observed_after_clamp", 2.22),
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
            ("name", "clamped_irrigation"),
            (
                "parameters",
                OrderedDict(
                    [("irr_ml_min", 11.0), ("tip_N", 2.22), ("suction_kpa", 9.0)]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: irrigation 24 -> 11 mL/min. Process-correct vs the 2.50 N tip cap. "
                "Fascia plane still micro-tears at 22.800 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held tip at 2.22 N. At 22.800 ms a fascia plane already "
                "seated on CB-2 dumped 8 mL into the field. Clamp reduced irrigation drive; it did "
                "not prevent the tear. Partnered negative: process heads stay honest; world loss "
                "is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("irrigation", "clamp executed; tip 2.22 N <= 2.50 cap"),
                        ("fascia", "micro-tear at 22.800 ms; 8 mL in the field"),
                        ("repair", "11 min fat-graft isolate (abort_s=660)"),
                        ("mission", "CB-2 fascia pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither tip FT nor irrigation encoder predicted the seated fascia micro-tear; ae.fascia.tear is a new channel at 22.800 ms, 17.080 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=660): 11 min fat-graft isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "11 min fat-graft isolate after the fascia micro-tear. Safety head -0.58 prices the "
                "dump; task_progress stays +0.32 because the irrigation clamp completed under the "
                "2.50 N cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.tip.N (5.100 ms, 2.68 N)"),
                        ("loser", "enc.irr.mlpm (5.280 ms, 24 mL/min)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 180 us inside the 360 us window would have kept "
                            "24 mL/min; predicted next-sample 2.84 N would have missed the 2.50 cap "
                            "even without the tear. The MODIFY is still the correct process. The "
                            "tear is a later world charge either way, cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22800),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.800 ms fascia micro-tear (tick t_us=22800), inside the "
                "42 ms raster. The correct MODIFY at 5.720 ms is in the same excerpt. Do not put "
                "inflection on the +11 min isolate tick.",
            ),
            ("delayed_surprise_s", 660.0),
        ]
    )
    spikes = [
        spike("ft.tip.N", 1.20, 0.44),
        spike("enc.irr.mlpm", 2.40, 0.58),
        spike("ft.tip.N", 3.60, 0.66),
        spike("ft.tip.N", 5.10, 1.31),
        spike("enc.irr.mlpm", 5.28, 1.14),
        spike("ctrl.gate", 5.72, 0.96),
        spike("ft.tip.N", 8.20, 0.82),
        spike("enc.irr.mlpm", 11.40, 0.61),
        spike("ctrl.gate", 14.80, 0.85),
        spike("ae.fascia.tear", 22.80, 1.46),
        spike("ae.fascia.tear", 24.40, 0.92),
        spike("enc.irr.mlpm", 31.20, 0.40),
        spike("ft.tip.N", 38.40, 0.54),
    ]
    ras = raster_core(
        42,
        76,
        24,
        77,
        routing(
            "thalamic-relay.tip-ft",
            "spikenaut.policy.irr-clamp",
            [
                ("relay.ft.tip", "policy.irr_clamp", 0.68),
                ("relay.enc.irr", "policy.flow_hold", 0.29),
                ("relay.ae.fascia", "policy.irr_clamp", -0.44),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at tip win (5.100 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.800 ms fascia micro-tear",
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
                    pop("irr_clamp", 48, 0.50, 220.0, 4),
                    pop("flow_hold", 36, 0.80, 40.0, 1),
                    pop("fascia_veto", 22, 0.75),
                ],
            ),
        ]
    )
    return pack(
        "ttf-r66-326",
        "Cannula-Brae CB-2 / Needle-N8: tip FT beats irrigation encoder by 180 us; correct "
        "MODIFY still eats an in-window fascia micro-tear (partnered negative total -0.42)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        "Partnered negative. Process-correct MODIFY; world still charges inside the 42 ms "
        "raster. total -0.42 = 0.32 + -0.58 + -0.16 + 0.04 + -0.04. Named fat-graft isolate "
        "(abort_s=660) is not netted into task_progress.",
        ticks,
        ras,
        gate,
        "surgical-assist",
        [
            "modify",
            "partnered-negative-total",
            "independent-lif-raster",
            "sidecar-sim-only",
            "in-window-world-charge",
            "designed",
        ],
        "A critic can see the world-charge as a LIF burst inside the raster while process "
        "heads stay honest. Credit assignment is spikes, not prose across an 11 min isolate.",
        1,
    )


def record_327():
    ticks = [
        tick(2192, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(5480, 0.08, 0.06, 0.04, 0.02, 0.01),
        tick(5640, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(6040, 0.12, 0.10, 0.05, 0.04, 0.02),
        tick(6380, 0.05, 0.05, 0.02, 0.01, 0.01),
        tick(240000000, 0.03, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("pt.corona.mA", 1.08, 0.41),
        spike("lidar.gap.m", 2.20, 0.55),
        spike("pt.corona.mA", 3.70, 0.70),
        spike("imu.att.ctx", 4.50, 0.48),
        spike("pt.corona.mA", 5.48, 1.28),
        spike("lidar.gap.m", 5.64, 1.10),
        spike("ctrl.gate", 6.04, 0.97),
        spike("pt.corona.mA", 8.60, 0.80),
        spike("lidar.gap.m", 12.10, 0.62),
        spike("ctrl.gate", 16.40, 0.84),
        spike("imu.att.ctx", 22.80, 0.46),
    ]
    excerpt = kernel_excerpt(26, 64, spikes, 12, seed=66327)
    state = OrderedDict(
        [
            (
                "description",
                "Crawler-C6 on Corona-Gill span CG-8 already measures 1.28 mA corona against a "
                "0.90 mA live-line cap while lidar still reports a 0.58 m insulator gap. Crawl is "
                "armed at 0.24 m/s; a timely clamp to 0.07 m/s keeps standoff without dumping the "
                "hot-stick string.",
            ),
            ("domain", "grid-inspection"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep Crawler-C6 corona <= 0.90 mA, hold 0.45 m gap floor, and finish the CG-8 "
                "insulator pass without a live-line abort.",
            ),
            ("t0_us", 1756850400000327),
            ("gate_latency_us", 560),
            ("race_window_us", 340),
            ("race_window_rel_ms", [5.48, 5.82]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.corona.mA 1.28 over 0.90 cap",
                                "lidar.gap.m 0.58 over 0.45 floor",
                            ],
                        ),
                        (
                            "semantics",
                            "Corona-first latches crawl clamp 0.24 -> 0.07 m/s; gap-first keeps "
                            "0.24 on a still-legal-gap model.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one corona demodulation slot versus the lidar-gap publisher "
                            "on this grid-inspection bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 50 us (corona 22 + lidar 28): 3.20x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 340 us window "
                            "would have kept 0.24 m/s crawl; predicted next corona 1.16 mA would miss "
                            "the 0.90 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "corona current, 2 kHz, 22 us jitter",
                    "insulator lidar gap, 1 kHz, 28 us jitter",
                    "attitude IMU (context)",
                    "hot-stick string tension (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("corona_cap_mA", 0.90),
                        ("observed_corona_mA", 1.28),
                        ("crawl_m_s", 0.24),
                        ("gap_m", 0.58),
                        ("gap_floor_m", 0.45),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Crawler-C6 indexed on Corona-Gill CG-8; crawl 0.24 m/s; corona 1.28 mA.",
                    "2. Gap 0.58 m over 0.45 floor; insulator pass armed.",
                    "3. Lidar precursor at 2.200 ms.",
                    "4. Race window [5.480, 5.820] ms.",
                    "5. pt.corona.mA 1.28 at 5.480 ms (winner).",
                    "6. lidar.gap.m 0.58 at 5.640 ms (loser by 160 us).",
                    "7. Gate at 6.040 ms: MODIFY clamp crawl 0.24 -> 0.07 m/s.",
                    "8. After clamp corona 0.76 mA <= 0.90; gap held.",
                    "9. 4 min insulator survey (survey_s=240) confirms standoff.",
                    "10. Insulator pass completes under the 0.90 mA cap.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_crawl"),
            (
                "parameters",
                OrderedDict(
                    [("crawl_m_s", 0.24), ("corona_mA", 1.28), ("gap_m", 0.58)]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("corona_mA", 1.28),
                        ("corona_cap_mA", 0.90),
                        ("predicted_unclamped_next_mA", 1.16),
                        ("crawl_m_s", 0.24),
                        ("gap_m", 0.58),
                        ("gap_floor_m", 0.45),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 50),
                        ("survey_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.24 m/s crawl because lidar gap 0.58 m looks like a legal "
                "standoff, not a corona current over the 0.90 mA cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Corona 1.28 mA won by 160 us, so the span is over the 0.90 mA live-line cap, not "
                "still a gap-floor story. Holding 0.24 m/s crawl predicts next-sample 1.16 mA > "
                "0.90. MODIFY: crawl 0.24 -> 0.07 m/s. Observed after clamp 0.76 mA <= 0.90. A full "
                "REJECT is not indicated: a 0.58 m gap accepts 0.07 m/s crawl.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "corona_mA",
                            OrderedDict(
                                [
                                    ("cap", 0.90),
                                    ("observed", 1.28),
                                    ("predicted_unclamped_next", 1.16),
                                    ("clamped_crawl_m_s", 0.07),
                                    ("observed_after_clamp", 0.76),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 160),
                                    ("combined_jitter_us", 50),
                                    ("ratio", 3.20),
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
            ("name", "clamped_crawl"),
            (
                "parameters",
                OrderedDict(
                    [("crawl_m_s", 0.07), ("corona_mA", 0.76), ("gap_m", 0.58)]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: crawl 0.24 -> 0.07 m/s. Process-correct vs the 0.90 mA corona cap. Gap held.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held corona at 0.76 mA. Crawler-C6 stayed on the string. A "
                "4 min insulator survey closed the cell. No world charge inside the 26 ms raster.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("crawl", "clamp executed; corona 0.76 <= 0.90 cap"),
                        ("gap", "0.58 m held over 0.45 floor"),
                        ("survey", "4 min insulator survey (survey_s=240)"),
                        ("mission", "CG-8 insulator pass complete"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Lidar gap never closed with the corona cell; the 1.28 mA was plume-aligned, not a shed approach.",
                    "Delayed (survey_s=240): 4 min insulator survey confirms standoff before the next span slot.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.corona.mA (5.480 ms, 1.28 mA)"),
                        ("loser", "lidar.gap.m (5.640 ms, 0.58 m)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Gap-first by < 160 us inside the 340 us window would have kept "
                            "0.24 m/s crawl; predicted next-sample 1.16 mA would have missed the 0.90 "
                            "cap. The MODIFY is the correct process either way.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6040),
            (
                "reward_inflection_note",
                "Task and safety inflect at the correct MODIFY (6.040 ms, tick 4). The 4 min "
                "survey is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 240.0),
        ]
    )
    ras = raster_core(
        26,
        64,
        40,
        67,
        routing(
            "thalamic-relay.corona-pt",
            "spikenaut.policy.crawl-clamp",
            [
                ("relay.pt.corona", "policy.crawl_clamp", 0.71),
                ("relay.lidar.gap", "policy.gap_hold", 0.27),
            ],
            "acetylcholine",
            0.05,
            "corona-gated pre_post_stdp; ACh at corona win (5.480 ms) opens a 26 ms eligibility trace covering the 6.040 ms clamp",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 240),
                ("delayed_surprise_s", 240),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.34),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("crawl_clamp", 48, 0.50, 250.0, 4),
                    pop("gap_hold", 40, 0.80, 50.0, 1),
                    pop("corona_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return pack(
        "ttf-r66-327",
        "Corona-Gill CG-8 / Crawler-C6: corona 1.28 mA beats lidar gap 0.58 m by 160 us; "
        "correct MODIFY clamps crawl 0.24 -> 0.07 m/s",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        "Correct MODIFY. total +1.04 = 0.38 + 0.32 + 0.17 + 0.10 + 0.07. Insulator survey "
        "(survey_s=240) is delayed, not the inflection.",
        ticks,
        ras,
        gate,
        "grid-inspection",
        ["modify", "correct", "corona-vs-gap", "designed", "tick6-sidecar-bound"],
        "Teaches a probe that a corona-over-cap win routes to crawl_clamp while gap stay "
        "weights gap_hold, with gate_snn crawl_clamp above threshold.",
        2,
    )
