def record_143():
    ticks = [
        tick(2410, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6040, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(6188, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7040, 0.03, 0.12, 0.04, 0.04, 0.01),
        tick(9100, 0.02, 0.06, 0.02, 0.01, 0.01),
        tick(360000000, 0.01, 0.04, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.field.ctx", 1.330, 0.43),
        spike("spark.rate.pps", 2.880, 0.61),
        spike("opac.lamp.pct", 4.410, 0.49),
        spike("spark.rate.pps", 6.040, 1.36),
        spike("opac.lamp.pct", 6.188, 1.11),
        spike("ctrl.gate", 7.040, 1.04),
        spike("spark.rate.pps", 9.020, 0.78),
        spike("tc.field.ctx", 12.440, 0.44),
        spike("opac.lamp.pct", 16.900, 0.58),
        spike("ctrl.gate", 22.100, 0.81),
        spike("spark.rate.pps", 29.400, 0.53),
        spike("tc.field.ctx", 38.200, 0.37),
        spike("opac.lamp.pct", 42.600, 0.46),
    ]
    excerpt = independent_excerpt(25143, 112, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Field F-4 on the Soot-Kettle SK-HIL stand shows spark rate 42 pps over the "
                "12 pps T/R cap while an opacity camera still counts 8 pct of pad-lamp scatter. "
                "Spark-first holds the T/R set; opacity-first would have treated lamp scatter as "
                "dust load and kept 55 kV armed.",
            ),
            ("domain", "electrostatic-precipitator"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep T/R off unless spark rate <= 12 pps; do not treat pad-lamp opacity as a "
                "dust-load permit.",
            ),
            ("t0_us", 1756843200000143),
            ("gate_latency_us", 1000),
            ("race_window_us", 320),
            ("race_window_rel_ms", [6.0, 6.32]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "spark.rate.pps 42 pps",
                                "opac.lamp.pct 8 pct lamp scatter",
                            ],
                        ),
                        (
                            "semantics",
                            "Spark-first REJECTs T/R (42 > 12 pps cap). Opacity-first would "
                            "ACCEPT on pad-lamp scatter mistaken for dust load.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one spark-counter sample minus opacity-camera group delay on "
                            "this HIL ESP-field bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 148 us vs combined jitter ~58 us (spark 26 + opacity 32): 2.6x over "
                            "a 2.0x trust floor. Reversing order by < 148 us inside the 320 us window "
                            "would have kept 55 kV armed on 8 pct of lamp scatter.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "field spark counter, 5 kHz burst, 26 us jitter",
                    "opacity camera, 2 kHz, 32 us jitter",
                    "field thermocouple (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("spark_cap_pps", 12.0),
                        ("observed_spark_pps", 42.0),
                        ("opac_pct", 8.0),
                        ("opac_abort_pct", 20.0),
                        ("proposed_tr_kV", 55.0),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("pad", "Soot-Kettle SK-HIL ESP-field stand"),
                        ("injected", "spark-rate burst + opacity lamp-scatter packet"),
                        (
                            "note",
                            "Hardware-in-the-loop ESP field. Invented plant; not a live boiler duct.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Field F-4 on the SK-HIL stand; T/R 55 kV armed.",
                    "2. Opacity lamp packet injected 110-150 us before the spark counter volume.",
                    "3. Field-temp precursor at 1.330 ms.",
                    "4. Race window [6.000, 6.320] ms.",
                    "5. spark.rate.pps 42 pps at 6.040 ms (winner).",
                    "6. opac.lamp.pct 8 pct at 6.188 ms (loser by 148 us).",
                    "7. Gate at 7.040 ms: REJECT hold T/R 0 kV; do not energize.",
                    "8. Spark rate remains over the 12 pps cap this cycle.",
                    "9. Opacity 8 pct stays a lamp artifact, not dust load.",
                    "10. Delayed (abort_s=360): 6 min field isolate and lamp retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "tr_55kV"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("tr_kV", 55.0),
                        ("tr_on", True),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("spark_pps", 42.0),
                        ("spark_cap_pps", 12.0),
                        ("opac_pct", 8.0),
                        ("opac_abort_pct", 20.0),
                        ("race_margin_us", 148),
                        ("combined_jitter_us", 58),
                        ("abort_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 55 kV T/R because opacity 8 pct looks like a clear duct; it "
                "has not yet bound spark 42 pps to the 12 pps cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Spark rate 42 pps won by 148 us, so the T/R cap is already violated. Opacity "
                "8 pct is under the 20 pct abort and is pad-lamp scatter. REJECT: T/R 0 kV, "
                "tr_on false. A MODIFY that keeps T/R armed is not indicated: next-sample spark "
                "is 44 pps.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "spark_pps",
                            OrderedDict(
                                [
                                    ("cap", 12.0),
                                    ("observed", 42.0),
                                    ("executed_tr_kV", 0.0),
                                ]
                            ),
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
            ("name", "tr_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("tr_kV", 0.0),
                        ("tr_on", False),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: T/R 55 -> 0 kV. Spark cap held. Lamp opacity unused as a go signal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held F-4 T/R at 0 kV. Spark 42 pps was over the 12 pps "
                "cap; opacity 8 pct was pad-lamp scatter. 6 min field isolate (abort_s=360).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("tr", "held; 0 kV"),
                        ("spark", "still 42 pps > 12 cap"),
                        ("opacity", "8 pct lamp scatter unused"),
                        ("mission", "energize deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Pad lamp injected opacity 110-150 us before the spark counter saw the same burst; spark-first is the T/R loop.",
                    "Delayed (abort_s=360): 6 min field isolate and lamp-spectrum retune.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "spark.rate.pps (6.040 ms, 42 pps)"),
                        ("loser", "opac.lamp.pct (6.188 ms, 8 pct)"),
                        ("margin_us", 148),
                        (
                            "counterfactual_if_reversed",
                            "Opacity-first by < 148 us inside the 320 us window would have kept "
                            "T/R armed on 8 pct of lamp scatter while spark stayed over 12 pps.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7040),
            (
                "reward_inflection_note",
                "Safety and coherence peak at the correct REJECT (7.040 ms, tick 4). The 6 min "
                "isolate is delayed surprise, not the inflection.",
            ),
        ]
    )
    dw = 0.32
    ras = raster_core(
        46,
        112,
        22,
        113,
        routing(
            "thalamic-relay.esp-spark",
            "spikenaut.policy.tr-hold",
            [
                ("relay.spark.rate", "policy.tr_hold", 0.71),
                ("relay.opac.lamp", "policy.tr_go", 0.24),
            ],
            "dopamine",
            0.05,
            "cap_stdp; DA tags the spark-cap bind at the counter win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", dw),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop_budget("tr_hold", 56, 0.50, 250.0, dw),
                    pop_budget("tr_go", 56, 0.80, 20.0, dw),
                    pop_budget("spark_ctx", 32, 0.55, 150.0, dw),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r25-143"),
            (
                "title",
                "Soot-Kettle SK-HIL / Field F-4: spark 42 pps beats lamp opacity 8 pct; "
                "correct REJECT holds T/R",
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
                    "Correct REJECT. Spark 42 > 12 pps cap; opacity 8 pct is lamp, not dust. "
                    "total +0.78 = 0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "electrostatic-precipitator",
                    [
                        "reject",
                        "hil",
                        "spark-vs-opacity",
                        "lamp-scatter-artifact",
                    ],
                    "Teaches that a lamp-scatter opacity packet can lose to a spark counter inside "
                    "a 320 us window; reversing 148 us would have kept T/R armed over the cap.",
                    3,
                ),
            ),
        ]
    )


def record_144():
    ticks = [
        tick(1540, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(5210, 0.10, 0.08, 0.04, 0.03, 0.02),
        tick(5388, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(6310, 0.12, 0.08, 0.04, 0.04, 0.02),
        tick(9100, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(240000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.fan.ctx", 1.140, 0.40),
        spike("ft.sting.N", 2.280, 0.56),
        spike("wall.pt.kPa", 3.610, 0.47),
        spike("ft.sting.N", 5.210, 1.27),
        spike("wall.pt.kPa", 5.388, 1.08),
        spike("ctrl.gate", 6.310, 0.99),
        spike("ft.sting.N", 8.760, 0.76),
        spike("enc.fan.ctx", 11.020, 0.43),
        spike("wall.pt.kPa", 14.400, 0.55),
        spike("ctrl.gate", 18.900, 0.82),
        spike("ft.sting.N", 22.600, 0.50),
        spike("enc.fan.ctx", 27.200, 0.36),
    ]
    excerpt = independent_excerpt(25144, 60, 29000, 13, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("aoa_deg", 4.0),
            ("hold", False),
            ("sting_N", 186.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Sting S-3 in Gulley-Tunnel GT-7 holds 4.0 deg AoA with balance force 186 N under "
                "a 280 N sting cap. A wall-pressure tap still reports 0.42 kPa residual from the last "
                "gust. Balance-first confirms the already-legal AoA; wall-first would have "
                "REJECTED a legal sting on tunnel unsteadiness.",
            ),
            ("domain", "wind-tunnel-balance"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold 4.0 deg AoA while sting force stays <= 280 N; do not abort on a 0.42 kPa wall residual.",
            ),
            ("t0_us", 1756843200000144),
            ("gate_latency_us", 1100),
            ("race_window_us", 420),
            ("race_window_rel_ms", [5.0, 5.42]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.sting.N 186 N",
                                "wall.pt.kPa 0.42 kPa residual",
                            ],
                        ),
                        (
                            "semantics",
                            "Balance-first ACCEPTS the 4.0 deg AoA (already under 280 N). "
                            "Wall-first would REJECT on a gust residual.",
                        ),
                        (
                            "window_derivation",
                            "420 us = one sting-balance sample minus wall-tap group delay on "
                            "this tunnel bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 178 us vs combined jitter ~62 us (balance 28 + wall 34): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 178 us inside the 420 us window "
                            "would have REJECTED a legal 4.0 deg AoA.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "sting 3-component balance, 2 kHz, 28 us jitter",
                    "wall static tap 0-2 kPa, 34 us jitter",
                    "fan encoder (context)",
                    "plenum RTD (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("sting_cap_N", 280.0),
                        ("observed_sting_N", 186.0),
                        ("wall_kPa", 0.42),
                        ("wall_abort_kPa", 1.80),
                        ("proposed_aoa_deg", 4.0),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "lumped sting-flex + 3-component balance, seed 25144; 8 modal beams, "
                            "4 s gust; NOT U-RANS, NOT actuator-disk, NOT a live tunnel",
                        ),
                        (
                            "fidelity_limits",
                            "Linear flex; no stall buffet. Raster is kernelized events, "
                            "not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Sting S-3 indexed in GT-7; AoA 4.0 deg armed.",
                    "2. Balance 186 N; wall residual 0.42 kPa.",
                    "3. Fan-encoder precursor at 1.140 ms.",
                    "4. Race window [5.000, 5.420] ms.",
                    "5. ft.sting.N 186 N at 5.210 ms (winner).",
                    "6. wall.pt.kPa 0.42 kPa at 5.388 ms (loser by 178 us).",
                    "7. Gate at 6.310 ms: ACCEPT 4.0 deg; executed identical to proposed.",
                    "8. AoA continues; peak sting 191 N < 280 cap.",
                    "9. Wall 0.42 kPa remains a gust residual, not a force loop.",
                    "10. Delayed (survey_s=240): 4 min balance recount on the next gust.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "aoa_40"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("sting_N", 186.0),
                        ("sting_cap_N", 280.0),
                        ("wall_kPa", 0.42),
                        ("wall_abort_kPa", 1.80),
                        ("race_margin_us", 178),
                        ("combined_jitter_us", 62),
                        ("survey_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.0 deg AoA because sting 186 N is under the 280 N "
                "cap; wall 0.42 kPa is under the 1.80 abort and is treated as gust, not force.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Sting 186 N won by 178 us and is under the 280 N cap. Wall 0.42 kPa is "
                "under the 1.80 kPa abort. ACCEPT the already-legal 4.0 deg AoA. A REJECT on gust "
                "would stall a legal polar.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "sting_N",
                            OrderedDict(
                                [
                                    ("cap", 280.0),
                                    ("observed", 186.0),
                                    ("executed_aoa_deg", 4.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 178),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 2.87),
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
            ("name", "aoa_40"),
            ("parameters", OrderedDict(params)),
            (
                "gate_effect",
                "ACCEPT: AoA 4.0 deg unchanged. Sting stayed 186-191 N < 280 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept S-3 at 4.0 deg. Sting 186 N was under the "
                "280 N cap; wall 0.42 kPa was gust. 4 min balance recount (survey_s=240).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("aoa", "4.0 deg continued"),
                        ("sting", "peak 191 N < 280 cap"),
                        ("wall", "0.42 kPa unused as a hold"),
                        ("mission", "polar continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Wall residual arrived 178 us after the balance; reversing that order would have REJECTED a legal AoA.",
                    "Delayed (survey_s=240): 4 min balance recount on the next gust, not a force event.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.sting.N (5.210 ms, 186 N)"),
                        ("loser", "wall.pt.kPa (5.388 ms, 0.42 kPa)"),
                        ("margin_us", 178),
                        (
                            "counterfactual_if_reversed",
                            "Wall-first by < 178 us inside the 420 us window would have REJECTED "
                            "an already-legal 4.0 deg AoA on a 0.42 kPa gust residual.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6310),
            (
                "reward_inflection_note",
                "Task and safety peak at the correct ACCEPT (6.310 ms, tick 4). The 4 min recount "
                "is delayed surprise, not the inflection.",
            ),
        ]
    )
    dw = 0.42
    ras = raster_core(
        29,
        60,
        34,
        59,
        routing(
            "thalamic-relay.sting-ft",
            "spikenaut.policy.aoa-go",
            [
                ("relay.ft.sting", "policy.aoa_go", 0.69),
                ("relay.wall.pt", "policy.wall_hold", 0.28),
            ],
            "serotonin",
            0.03,
            "sting_stdp; 5-HT tags the already-legal balance bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", dw),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("aoa_go", 40, 0.50, 280.0, dw),
                    pop_budget("wall_hold", 40, 0.50, 70.0, dw),
                    pop_budget("sting_ctx", 24, 0.55, 120.0, dw),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r25-144"),
            (
                "title",
                "Gulley-Tunnel GT-7 / sting S-3: balance 186 N beats wall 0.42 kPa by 178 us; "
                "correct ACCEPT of an already-legal 4.0 deg AoA",
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
                    "Correct ACCEPT. Sting 186 < 280 cap; wall is gust, not load. "
                    "total +1.08 = 0.42 + 0.30 + 0.16 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "wind-tunnel-balance",
                    [
                        "accept",
                        "wind-tunnel",
                        "sting-vs-wall",
                        "simulated-flex",
                        "simulated",
                    ],
                    "Teaches that a wall-tap residual can lose to sting balance inside a 420 us "
                    "window; reversing 178 us would have REJECTED an already-legal AoA.",
                    4,
                ),
            ),
        ]
    )
