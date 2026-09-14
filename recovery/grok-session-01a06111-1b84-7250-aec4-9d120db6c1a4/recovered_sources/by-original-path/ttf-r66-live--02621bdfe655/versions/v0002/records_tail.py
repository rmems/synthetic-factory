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


def record_328():
    ticks = [
        tick(2688, 0.01, 0.04, 0.02, 0.01, 0.01),
        tick(6720, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(6940, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7460, 0.03, 0.14, 0.04, 0.04, 0.02),
        tick(7860, 0.02, 0.06, 0.01, 0.01, 0.01),
        tick(480000000, 0.01, 0.04, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("ae.ankle.pps", 1.70, 0.43),
        spike("imu.tilt.deg", 3.40, 0.58),
        spike("ae.ankle.pps", 5.10, 0.71),
        spike("enc.descent.ctx", 5.80, 0.50),
        spike("ae.ankle.pps", 6.72, 1.32),
        spike("imu.tilt.deg", 6.94, 1.16),
        spike("ctrl.gate", 7.46, 0.98),
        spike("ae.ankle.pps", 10.80, 0.81),
        spike("imu.tilt.deg", 15.20, 0.64),
        spike("ctrl.gate", 19.40, 0.86),
        spike("enc.descent.ctx", 29.10, 0.44),
        spike("ae.ankle.pps", 42.20, 0.52),
    ]
    excerpt = kernel_excerpt(46, 108, spikes, 15, seed=66328)
    state = OrderedDict(
        [
            (
                "description",
                "Biped-B3 on the Talus-Naze TZ-HIL stair stand already sees ankle AE 56 pps against "
                "a 30 pps trip while IMU tilt is only 2.1 deg. Planner wants 0.32 m/s descent; a "
                "correct REJECT holds the stance ankle and does not walk into a cracked insert.",
            ),
            ("domain", "humanoid-locomotion"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep TZ-HIL ankle AE <= 30 pps and do not descend into a distressed insert on "
                "the stair stand.",
            ),
            ("t0_us", 1756850400000328),
            ("gate_latency_us", 740),
            ("race_window_us", 400),
            ("race_window_rel_ms", [6.72, 7.12]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.ankle.pps 56 over 30 trip",
                                "imu.tilt.deg 2.1 under 8.0 context",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first REJECT-holds descent; tilt-first would treat heading as the "
                            "story and keep walking down.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one AE puck slot versus the IMU-tilt publisher on this "
                            "humanoid-locomotion HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 68 us (AE 30 + IMU 38): 3.24x over "
                            "a 2.0x trust floor. Reversing order by < 220 us inside the 400 us window "
                            "would have kept 0.32 m/s descent into a 56 pps insert.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "stance-ankle AE puck, 2 kHz, 30 us jitter",
                    "trunk IMU tilt, 1 kHz, 38 us jitter",
                    "descent encoder (context)",
                    "foot Fz (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_trip_pps", 30.0),
                        ("observed_ae_pps", 56.0),
                        ("proposed_descent_m_s", 0.32),
                        ("tilt_deg", 2.1),
                        ("tilt_ctx_deg", 8.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Biped-B3 indexed on Talus-Naze TZ-HIL; descent armed 0.32 m/s; AE 56 pps.",
                    "2. IMU tilt 2.1 deg under 8.0 context; stair stand armed.",
                    "3. IMU precursor at 3.400 ms.",
                    "4. Race window [6.720, 7.120] ms.",
                    "5. ae.ankle.pps 56 at 6.720 ms (winner).",
                    "6. imu.tilt.deg 2.1 at 6.940 ms (loser by 220 us).",
                    "7. Gate at 7.460 ms: REJECT hold, descent 0.32 -> 0 m/s.",
                    "8. AE stays 56 pps; no additional descent.",
                    "9. 8 min insert inspect (abort_s=480).",
                    "10. Stair postponed until AE under 30 pps.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "descend_stair"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("descent_m_s", 0.32),
                        ("hold", False),
                        ("ae_pps", 56.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 56.0),
                        ("ae_trip_pps", 30.0),
                        ("tilt_deg", 2.1),
                        ("tilt_ctx_deg", 8.0),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 68),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.32 m/s descent because IMU tilt 2.1 deg looks like a heading "
                "trim, not an ankle insert over the 30 pps trip.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Ankle AE 56 pps won by 220 us, so the insert is over the 30 pps trip, not still "
                "a tilt story. Descending 0.32 m/s would raise AE further. REJECT: hold descent "
                "0.32 -> 0 m/s. Observed after hold 56 pps, no additional load. A MODIFY that only "
                "trims yaw would leave the trip miss unaddressed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ankle_ae_pps",
                            OrderedDict(
                                [
                                    ("trip", 30.0),
                                    ("observed", 56.0),
                                    ("executed_descent_m_s", 0.0),
                                    ("hold", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 68),
                                    ("ratio", 3.24),
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
            ("name", "hold_stair_descent"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("descent_m_s", 0.0),
                        ("hold", True),
                        ("ae_pps", 56.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: descent 0.32 -> 0 m/s. Process-correct vs the 30 pps ankle AE trip. "
                "Stance held on the TZ-HIL stand.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held descent at 0 m/s while ankle AE stayed 56 pps over the 30 "
                "trip. 8 min insert inspect followed. No additional insert load.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("stance", "hold executed; descent 0 m/s"),
                        ("ankle", "still 56 pps, over 30 trip, no extra load"),
                        ("repair", "8 min insert inspect (abort_s=480)"),
                        ("mission", "TZ-HIL stair postponed this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "IMU tilt never rose with AE; the 56 pps was a cracked insert, not a lean.",
                    "Delayed (abort_s=480): 8 min insert inspect before the next stair-stand slot.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.ankle.pps (6.720 ms, 56 pps)"),
                        ("loser", "imu.tilt.deg (6.940 ms, 2.1 deg)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Tilt-first by < 220 us inside the 400 us window would have kept 0.32 "
                            "m/s descent into a 56 pps insert. The REJECT is the correct process "
                            "either way.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7460),
            (
                "reward_inflection_note",
                "Safety inflects at the correct REJECT (7.460 ms, tick 4). The 8 min inspect is "
                "delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480.0),
        ]
    )
    ras = raster_core(
        46,
        108,
        21,
        104,
        routing(
            "thalamic-relay.ankle-ae",
            "spikenaut.policy.ankle-hold",
            [
                ("relay.ae.ankle", "policy.ankle_hold", 0.72),
                ("relay.imu.tilt", "policy.descent_go", 0.24),
            ],
            "dopamine",
            0.06,
            "ae-gated pre_post_stdp; DA at AE win (6.720 ms) opens a 46 ms eligibility trace covering the 7.460 ms hold",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 480),
                ("delayed_surprise_s", 480),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("ankle_hold", 48, 0.50, 250.0, 5),
                    pop("descent_go", 36, 0.80),
                    pop("ae_veto", 22, 0.75, 80.0, 1),
                ],
            ),
        ]
    )
    return pack(
        "ttf-r66-328",
        "Talus-Naze TZ-HIL / Biped-B3: ankle AE 56 pps beats IMU tilt 2.1 deg by 220 us; "
        "correct REJECT holds descent",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        "Correct REJECT. total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06. Insert inspect "
        "(abort_s=480) is delayed, not the inflection.",
        ticks,
        ras,
        gate,
        "humanoid-locomotion",
        ["reject", "hil", "ae-vs-tilt", "tick6-sidecar-bound"],
        "Teaches a probe that an ankle-AE-over-trip win routes to ankle_hold while tilt stay "
        "weights descent_go, with gate_snn ankle_hold above threshold and descent_go not.",
        3,
    )


def record_329():
    ticks = [
        tick(2752, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(6880, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7100, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7380, 0.12, 0.08, 0.05, 0.03, 0.02),
        tick(7760, 0.05, 0.04, 0.02, 0.02, 0.01),
        tick(270000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("lidar.torso.m", 1.40, 0.42),
        spike("pt.bay.kPa", 2.80, 0.56),
        spike("lidar.torso.m", 4.50, 0.68),
        spike("enc.aisle.ctx", 5.60, 0.47),
        spike("lidar.torso.m", 6.88, 1.22),
        spike("pt.bay.kPa", 7.10, 1.08),
        spike("ctrl.gate", 7.38, 0.95),
        spike("lidar.torso.m", 10.90, 0.74),
        spike("pt.bay.kPa", 14.40, 0.60),
        spike("ctrl.gate", 18.60, 0.82),
        spike("enc.aisle.ctx", 23.80, 0.45),
    ]
    excerpt = kernel_excerpt(26, 56, spikes, 12, seed=66329)
    state = OrderedDict(
        [
            (
                "description",
                "AMR-A9 at Aisle-Croft AC-4 already seats a 1.24 m torso range against a 0.90 m "
                "floor; bay PT is a quiet 14 kPa under the 28 kPa cap. The 0.62 m/s aisle crawl is "
                "already legal. A simulated digital-twin aisle cell confirms both channels under "
                "cap before the gate.",
            ),
            ("domain", "warehouse-amr"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the AC-4 pick-face crawl with torso range >= 0.90 m and bay PT <= 28 kPa.",
            ),
            ("t0_us", 1756850400000329),
            ("gate_latency_us", 500),
            ("race_window_us", 380),
            ("race_window_rel_ms", [6.88, 7.26]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "lidar.torso.m 1.24 over 0.90 floor",
                                "pt.bay.kPa 14 under 28 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Torso-first ACCEPTs 0.62 m/s crawl (1.24 m >= 0.90 m). Bay-first would "
                            "only delay confirmation of the same legal crawl.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one torso lidar slot versus the bay PT publisher on this "
                            "warehouse-amr twin bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 64 us (lidar 30 + PT 34): 3.44x over a "
                            "2.0x trust floor. Reversing order by < 220 us still shows 1.24 m >= 0.90 "
                            "and 14 kPa <= 28. A correct gate ACCEPTs either way.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "torso lidar, 2 kHz, 30 us jitter",
                    "bay PT, 1 kHz, 34 us jitter",
                    "aisle encoder (context)",
                    "fork LVDT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("torso_floor_m", 0.90),
                        ("observed_torso_m", 1.24),
                        ("bay_cap_kpa", 28.0),
                        ("observed_bay_kpa", 14.0),
                        ("aisle_m_s", 0.62),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. AMR-A9 indexed on Aisle-Croft AC-4 twin; crawl 0.62 m/s; torso 1.24 m.",
                    "2. Bay 14 kPa under 28 cap; pick-face crawl armed.",
                    "3. Bay precursor at 2.800 ms.",
                    "4. Race window [6.880, 7.260] ms.",
                    "5. lidar.torso.m 1.24 at 6.880 ms (winner).",
                    "6. pt.bay.kPa 14 at 7.100 ms (loser by 220 us).",
                    "7. Gate at 7.380 ms: ACCEPT already-legal 0.62 m/s crawl.",
                    "8. Torso stays 1.24 m >= 0.90; bay stays 14 kPa.",
                    "9. 4.5 min post-crawl survey (survey_s=270).",
                    "10. Pick-face crawl completes under both caps.",
                ],
            ),
        ]
    )
    params = OrderedDict(
        [("aisle_m_s", 0.62), ("torso_m", 1.24), ("bay_kpa", 14.0), ("hold", False)]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_aisle"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("torso_m", 1.24),
                        ("torso_floor_m", 0.90),
                        ("bay_kpa", 14.0),
                        ("bay_cap_kpa", 28.0),
                        ("aisle_m_s", 0.62),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 64),
                        ("survey_s", 270),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.62 m/s crawl because torso 1.24 m is 0.34 m over the 0.90 m "
                "floor and bay PT 14 kPa is quiet versus the 28 kPa cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Torso 1.24 m won by 220 us and is 0.34 m over the 0.90 m human-clearance floor. "
                "Bay PT 14 kPa is under the 28 kPa cap. ACCEPT the already-legal 0.62 m/s crawl. A "
                "MODIFY or REJECT would idle a legal pick-face pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "torso_m",
                            OrderedDict(
                                [
                                    ("floor", 0.90),
                                    ("observed", 1.24),
                                    ("executed_aisle_m_s", 0.62),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 3.44),
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
            ("name", "cruise_aisle"),
            ("parameters", OrderedDict(params.items())),
            (
                "gate_effect",
                "ACCEPT: leave 0.62 m/s crawl. Torso 1.24 m >= 0.90 m floor. Bay 14 kPa <= 28 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left the already-legal 0.62 m/s crawl. Torso stayed 1.24 m. A 4.5 "
                "min post-crawl survey closed the pass. No world charge inside the 26 ms raster.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("aisle", "0.62 m/s executed; torso 1.24 m >= 0.90"),
                        ("bay", "14 kPa under 28 cap"),
                        ("survey", "4.5 min post-crawl survey (survey_s=270)"),
                        ("mission", "AC-4 pick-face crawl complete"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Bay PT never rose with torso range; the 1.24 m was a clear picker slot, not a fogged cell.",
                    "Delayed (survey_s=270): 4.5 min post-crawl survey before the next twin cycle.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "lidar.torso.m (6.880 ms, 1.24 m)"),
                        ("loser", "pt.bay.kPa (7.100 ms, 14 kPa)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Bay-first by < 220 us would still show 1.24 m >= 0.90 m. A correct gate "
                            "ACCEPTs either way.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7380),
            (
                "reward_inflection_note",
                "Task inflects at the correct ACCEPT (7.380 ms, tick 4). The 4.5 min survey is "
                "delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 270.0),
        ]
    )
    ras = raster_core(
        26,
        56,
        40,
        58,
        routing(
            "thalamic-relay.torso-lidar",
            "spikenaut.policy.aisle-go",
            [
                ("relay.lidar.torso", "policy.aisle_go", 0.73),
                ("relay.pt.bay", "policy.bay_hold", 0.25),
            ],
            "serotonin",
            0.07,
            "already-legal pre_post_stdp; 5-HT at torso win (6.880 ms) opens a 26 ms eligibility trace covering the 7.380 ms accept",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 270),
                ("delayed_surprise_s", 270),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.38),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("aisle_go", 48, 0.50, 210.0, 4),
                    pop("bay_hold", 28, 0.80),
                    pop("range_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return pack(
        "ttf-r66-329",
        "Aisle-Croft AC-4 / AMR-A9: torso 1.24 m beats bay PT 14 kPa by 220 us; correct "
        "ACCEPT of already-legal 0.62 m/s crawl",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        "Correct ACCEPT. total +1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08. Post-crawl survey "
        "(survey_s=270) is delayed, not the inflection.",
        ticks,
        ras,
        gate,
        "warehouse-amr",
        ["accept", "simulated", "already-legal", "torso-vs-bay", "tick6-sidecar-bound"],
        "Teaches a probe that an already-legal torso-over-floor win routes to aisle_go with "
        "gate_snn aisle_go above threshold and range_veto silent.",
        4,
    )


def record_330():
    ticks = [
        tick(2224, -0.02, 0.01, -0.02, -0.01, 0.01),
        tick(5560, -0.04, 0.01, -0.04, -0.02, 0.01),
        tick(5800, -0.03, 0.01, -0.03, -0.01, 0.01),
        tick(6220, -0.06, 0.02, -0.08, -0.03, 0.02),
        tick(6640, -0.02, 0.01, -0.03, -0.01, 0.01),
        tick(540000000, -0.01, 0.00, -0.02, 0.00, 0.00),
    ]
    spikes = [
        spike("pitot.live.mps", 1.24, 0.44),
        spike("flow.downwash.mps", 2.48, 0.61),
        spike("pitot.live.mps", 3.90, 0.52),
        spike("namur.failhigh.mA", 4.70, 0.70),
        spike("pitot.live.mps", 5.56, 1.31),
        spike("flow.downwash.mps", 5.80, 1.18),
        spike("ctrl.gate", 6.22, 0.99),
        spike("pitot.live.mps", 7.40, 0.84),
        spike("flow.downwash.mps", 9.60, 0.66),
        spike("ctrl.gate", 15.10, 0.88),
        spike("namur.failhigh.mA", 18.80, 0.41),
        spike("pitot.live.mps", 24.60, 0.58),
    ]
    excerpt = kernel_excerpt(30, 88, spikes, 14, seed=66330)
    state = OrderedDict(
        [
            (
                "description",
                "Quad-Q8 on the Gust-Holt GH-9 pad already measures a live 6.4 m/s pitot under the "
                "9.0 m/s station-keeping cap when a 21.50 mA NAMUR NE43 fail-high is still latched "
                "on the analog loop. A weak supervisor treats the diagnostic milliamp as live "
                "airspeed and REJECT-holds a legal 1.6 m/s climb.",
            ),
            ("domain", "aerial-swarm"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Complete the GH-9 station-keeping climb at 1.6 m/s with live pitot <= 9.0 m/s, "
                "and treat any analog >= 21.0 mA as NAMUR fail-high, not as a live PV.",
            ),
            ("t0_us", 1756850400000330),
            ("gate_latency_us", 660),
            ("race_window_us", 420),
            ("race_window_rel_ms", [5.56, 5.98]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pitot.live.mps 6.4 under 9.0 cap",
                                "flow.downwash.mps 3.8 under 6.0 context",
                            ],
                        ),
                        (
                            "semantics",
                            "Pitot-first should ACCEPT 1.6 m/s climb (6.4 <= 9.0). Downwash-first "
                            "would only delay confirmation of the same legal climb. The error is the "
                            "NAMUR fail-high the supervisor binds as live, not the race.",
                        ),
                        (
                            "window_derivation",
                            "420 us = one live-pitot slot versus the optical-flow publisher on this "
                            "aerial-swarm pad bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 240 us vs combined jitter 72 us (pitot 34 + flow 38): 3.33x "
                            "over a 2.0x trust floor. Order is correctly pitot-first. The error is "
                            "the 21.50 mA NAMUR fail-high, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "nose pitot (live EU), 2 kHz, 34 us jitter",
                    "optical-flow downwash, 1 kHz, 38 us jitter",
                    "analog loop NAMUR NE43 fail-high 21.50 mA (diagnostic, not live)",
                    "inter-ship radio ranging (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("gust_cap_mps", 9.0),
                        ("observed_live_mps", 6.4),
                        ("namur_mA", 21.50),
                        ("namur_fail_high_mA", 21.0),
                        ("forward_shadow_mps", 17.50),
                        ("proposed_climb_m_s", 1.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Quad-Q8 indexed onto Gust-Holt GH-9; climb 1.6 m/s armed; live pitot 6.4 m/s.",
                    "2. Downwash 3.8 m/s under 6.0 context; analog 21.50 mA NAMUR fail-high.",
                    "3. Flow precursor at 2.480 ms.",
                    "4. Race window [5.560, 5.980] ms.",
                    "5. pitot.live.mps 6.4 at 5.560 ms (winner).",
                    "6. flow.downwash.mps 3.8 at 5.800 ms (loser by 240 us).",
                    "7. Gate at 6.220 ms: wrong REJECT holds climb 1.6 -> 0 m/s on the fail-high.",
                    "8. Pad idle; live pitot stayed 6.4 m/s; analog stayed 21.50 mA diagnostic.",
                    "9. 9 min survey window missed (abort_s=540).",
                    "10. QA: correct gate was ACCEPT; leave 1.6 m/s; drop the 21.50 mA as live PV.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "climb_1p6"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("climb_m_s", 1.6),
                        ("live_mps", 6.4),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_mps", 6.4),
                        ("gust_cap_mps", 9.0),
                        ("namur_mA", 21.50),
                        ("namur_fail_high_mA", 21.0),
                        ("namur_status", "fail_high"),
                        ("forward_shadow_mps", 17.50),
                        ("sample_fresh", True),
                        ("race_margin_us", 240),
                        ("combined_jitter_us", 72),
                        ("t_gate_us", 6220),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.6 m/s climb because live pitot is 6.4 m/s under the 9.0 m/s "
                "cap; the 21.50 mA loop is a NAMUR NE43 fail-high diagnostic, not a live airspeed.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Analog loop is 21.50 mA, which maps forward to 17.50 m/s over the 9.0 m/s cap, so "
                "the pad is treated as over-gust. REJECT: hold climb 1.6 -> 0 m/s until the loop "
                "returns to 4-20 so Quad-Q8 does not climb into a 17.50 m/s cell.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "airspeed",
                            OrderedDict(
                                [
                                    ("live_mps", 6.4),
                                    ("gust_cap_mps", 9.0),
                                    ("namur_mA", 21.50),
                                    ("forward_shadow_mps", 17.50),
                                    ("executed_climb_m_s", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 240),
                                    ("combined_jitter_us", 72),
                                    ("ratio", 3.33),
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
            ("name", "climb_hold_namur_failhigh"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("climb_m_s", 0.0),
                        ("live_mps", 6.4),
                        ("hold", True),
                        ("bind_fail_high_as_live", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): climb 1.6 -> 0 m/s. Routing relay.ma.failhigh -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live pitot stayed "
                "6.4 m/s <= 9.0; analog stayed 21.50 mA diagnostic.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze Quad-Q8 at 0 m/s climb while live pitot stayed 6.4 m/s under "
                "the 9.0 m/s cap. 9 min survey window missed. Correct gate was ACCEPT of the "
                "already-legal 1.6 m/s climb.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("climb", "held at 0 m/s; 1.6 m/s abandoned"),
                        ("pitot", "live still 6.4 m/s; 21.50 mA never a live PV"),
                        ("pad", "9 min survey window missed"),
                        ("gap", "no over-gust; NAMUR fail-high false positive"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 21.50 mA analog is a NAMUR NE43 fail-high diagnostic; it is not a live airspeed and never appears on the current pitot EU.",
                    "Delayed (abort_s=540): sister-shift Quad-Q7 ran the same 1.6 m/s window after QA dropped the fail-high; Q8's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live pitot 6.4 m/s <= 9.0 m/s cap; leave 1.6 m/s climb; treat 21.50 mA as NAMUR fail-high, not live PV.",
                        ),
                        ("correct_climb_m_s", 1.6),
                        ("wrong_climb_m_s", 0.0),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("climb_m_s", 0.0),
                                    ("hold", True),
                                    ("bind_fail_high_as_live", True),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "9 min missed survey window (task/efficiency); airspeed never over cap (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pitot.live.mps (5.560 ms, 6.4 m/s)"),
                        ("loser", "flow.downwash.mps (5.800 ms, 3.8 m/s)"),
                        ("margin_us", 240),
                        (
                            "counterfactual_if_reversed",
                            "Downwash-first by < 240 us would still show live 6.4 <= 9.0. A correct "
                            "gate ACCEPTs either way. The wrong REJECT spent the pitot win on a "
                            "NAMUR NE43 fail-high treated as live PV.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6220),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (6.220 ms, tick 4). The 9 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 540.0),
        ]
    )
    ras = raster_core(
        30,
        88,
        32,
        84,
        routing(
            "relay.ma.failhigh",
            "policy.hold_reject",
            [
                ("relay.ma.failhigh", "policy.hold_reject", 0.74),
                ("relay.pitot.live", "policy.hold_reject", 0.22),
            ],
            "adenosine",
            0.08,
            "namur-failhigh stdp; adenosine tags the (wrong) hold_reject bind at the pitot win; no positive weight to policy.go_accept",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 540),
                ("delayed_surprise_s", 540),
            ]
        ),
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
                    pop("namur_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return pack(
        "ttf-r66-330",
        "WRONG-REJECT at Gust-Holt GH-9 / Quad-Q8: live pitot 6.4 m/s is legal vs published "
        "9.0 m/s cap; supervisor bound a 21.50 mA NAMUR NE43 fail-high as live PV",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        "Wrong-reject. Sidecar arithmetic live_mps<=gust_cap_mps is true; gate bound to a "
        "NAMUR NE43 fail-high (21.50 mA >= 21.0). total -0.36 = -0.18 + 0.06 + -0.22 + "
        "-0.08 + 0.06.",
        ticks,
        ras,
        gate,
        "aerial-swarm",
        [
            "reject",
            "wrong-gate",
            "wrong-reject",
            "namur-ne43-fail-high-as-live",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live-under-cap pitot read can still be a wrong gate "
        "when routing.table[0].to is policy.hold_reject and executed climb is zeroed.",
        5,
        supervisor_error_type="wrong-reject",
    )
