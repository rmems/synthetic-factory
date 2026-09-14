def record_291():
    excerpt, extra = lif_291_excerpt()
    ticks = [
        tick(2112, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5280, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5460, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5980, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22600, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Stand Z-4 of Cluster-Riggs CR-6 is already biting 18.4 MN against a 14.0 MN roll-force "
                "cap while cluster coolant still reads a legal 420 L/min. Force-first cuts mill speed "
                "12.0 -> 8.4 m/s; flow-first would keep cruise because backup-bearing PT 2.1 bar is "
                "still under the 3.0 bar oil cap. A backup-bearing oil weep already seated on the "
                "inner race does not appear on force or coolant until the AE dump.",
            ),
            ("domain", "sendzimir-z-mill"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep Z-4 roll force <= 14.0 MN and finish the pass without dumping oil through a "
                "torn backup-bearing seal.",
            ),
            ("t0_us", 1756850400000291),
            ("gate_latency_us", 700),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.280, 5.640]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.bite.mn 18.4 over 14.0 cap",
                                "ft.cool.lpm 420 with oil 2.1 under 3.0",
                            ],
                        ),
                        (
                            "semantics",
                            "Force-first latches mill-speed clamp 12.0 -> 8.4 m/s; flow-first keeps "
                            "12.0 on a 'still under oil-pressure cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one mill-load-cell slot versus the coolant-orifice publisher on "
                            "this 20-high cluster bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (force 28 + coolant 34): 2.90x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 12.0 m/s; predicted next-sample 16.8 MN "
                            "> 14.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "roll-bite load cell, 2 kHz, 28 us jitter",
                    "coolant-orifice DP + backup oil PT, 1 kHz, 34 us jitter",
                    "backup-bearing AE puck (context)",
                    "shape-meter (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("force_cap_mn", 14.0),
                        ("observed_force_mn", 18.4),
                        ("speed_m_s", 12.0),
                        ("oil_bar", 2.1),
                        ("oil_cap_bar", 3.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Z-4 indexed on Cluster-Riggs CR-6; mill 12.0 m/s; bite 18.4 MN.",
                    "2. Backup oil 2.1 bar under 3.0 bar cap; pass armed.",
                    "3. Coolant precursor at 1.180 ms.",
                    "4. Race window [5.280, 5.640] ms.",
                    "5. ft.bite.mn 18.4 at 5.280 ms (winner).",
                    "6. ft.cool.lpm 420 at 5.460 ms (loser by 180 us).",
                    "7. Gate at 5.980 ms: MODIFY clamp 12.0 -> 8.4 m/s.",
                    "8. After clamp force 12.8 MN <= 14.0; oil still 2.1 bar.",
                    "9. At 22.600 ms a backup-bearing oil weep dumps 0.3 L.",
                    "10. 15 min bearing isolate (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_mill_speed"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_s", 12.0),
                        ("force_mn", 18.4),
                        ("oil_bar", 2.1),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("force_mn", 18.4),
                        ("force_cap_mn", 14.0),
                        ("predicted_unclamped_next_mn", 16.8),
                        ("speed_m_s", 12.0),
                        ("oil_bar", 2.1),
                        ("oil_cap_bar", 3.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 12.0 m/s because backup oil 2.1 bar is under 3.0, treating the "
                "18.4 MN bite as a still-wet load cell rather than a force-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Roll-bite 18.4 MN won by 180 us, so the cluster is off-spec, not still an "
                "oil-pressure story. Holding 12.0 m/s predicts next-sample 16.8 MN > 14.0 cap. "
                "MODIFY: mill speed 12.0 -> 8.4 m/s. Observed after clamp 12.8 MN <= 14.0. A full "
                "REJECT is not indicated: a clean pass accepts 8.4 m/s.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "force_mn",
                            OrderedDict(
                                [
                                    ("cap", 14.0),
                                    ("observed", 18.4),
                                    ("predicted_unclamped_next", 16.8),
                                    ("clamped_speed_m_s", 8.4),
                                    ("observed_after_clamp", 12.8),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 2.90),
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
            ("name", "clamped_mill_speed"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_s", 8.4),
                        ("force_mn", 12.8),
                        ("oil_bar", 2.1),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: mill speed 12.0 -> 8.4 m/s. Process-correct vs the 14.0 MN force cap. "
                "Backup-bearing oil still weeps at 22.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held roll-bite at 12.8 MN. At 22.600 ms a backup-bearing "
                "oil weep already seated on the inner race dumped 0.3 L. Clamp reduced dump "
                "energy; it did not prevent the leak. Partnered negative: process heads stay "
                "honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bite", "clamp executed; peak 12.8 MN <= 14.0 cap"),
                        ("bearing", "wept at 22.600 ms; 0.3 L oil"),
                        ("repair", "15 min bearing isolate (abort_s=900)"),
                        ("mission", "CR-6 pass incomplete this coil"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither bite load cell nor coolant FT predicted the seated backup-bearing oil weep; ae.oil.leak is a new channel at 22.600 ms, 16.620 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min bearing isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min bearing isolate after the oil weep. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the mill-speed clamp completed under the 14.0 "
                "MN cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.bite.mn (5.280 ms, 18.4 MN)"),
                        ("loser", "ft.cool.lpm (5.460 ms, 420 L/min)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Flow-first by < 180 us inside the 360 us window would have kept "
                            "12.0 m/s; predicted next-sample 16.8 MN would have missed the 14.0 "
                            "cap even without the oil weep. The MODIFY is still the correct "
                            "process. The leak is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22600),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.600 ms oil weep (tick t_us=22600), inside the 42 ms "
                "raster. The correct MODIFY at 5.980 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=900 isolation tick.",
            ),
            ("delayed_surprise_s", 900),
        ]
    )
    spikes = [
        spike("ft.cool.lpm", 1.180, 0.41),
        spike("ft.bite.mn", 2.112, 0.58),
        spike("ft.cool.lpm", 3.400, 0.50),
        spike("ft.bite.mn", 5.280, 1.31),
        spike("ft.cool.lpm", 5.460, 1.12),
        spike("ctrl.gate", 5.980, 0.97),
        spike("ft.bite.mn", 8.100, 0.82),
        spike("ft.cool.lpm", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.oil.leak", 22.600, 1.48),
        spike("ae.oil.leak", 24.100, 0.93),
        spike("ft.cool.lpm", 30.200, 0.40),
        spike("ft.bite.mn", 36.400, 0.55),
    ]
    dw = 0.36
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.zmill-force",
            "spikenaut.policy.speed-clamp",
            [
                ("relay.ft.bite", "policy.speed_clamp", 0.68),
                ("relay.ft.cool", "policy.flow_hold", 0.29),
                ("relay.ae.oil", "policy.speed_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at force win (5.280 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.600 ms oil weep",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", dw),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("speed_clamp", 50, 0.50, 220.0, dw),
                    pop_budget("flow_hold", 40, 0.80, 50.0, dw),
                    pop("oil_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r55-291"),
            (
                "title",
                "Cluster-Riggs CR-6 / Stand Z-4: roll-bite beats coolant flow by 180 us; correct "
                "MODIFY still eats an in-window backup-bearing oil weep (partnered negative "
                "total -0.44)",
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
                    "42 ms raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named "
                    "bearing isolate (abort_s=900) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "sendzimir-z-mill",
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
                    "15 min bearing isolate.",
                    1,
                ),
            ),
        ]
    )


def record_293():
    ticks = [
        tick(2736, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6840, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7020, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7640, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(7960, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.ci.mps", 1.360, 0.40),
        spike("ae.doctor.pps", 2.736, 0.56),
        spike("enc.ci.mps", 4.100, 0.48),
        spike("ae.doctor.pps", 6.840, 1.34),
        spike("enc.ci.mps", 7.020, 1.11),
        spike("ctrl.gate", 7.640, 0.98),
        spike("ae.doctor.pps", 10.400, 0.81),
        spike("enc.ci.mps", 14.800, 0.62),
        spike("ctrl.gate", 18.200, 0.84),
        spike("ae.doctor.pps", 28.400, 0.52),
        spike("enc.ci.mps", 36.100, 0.39),
        spike("ae.doctor.pps", 42.200, 0.44),
    ]
    excerpt = independent_excerpt(55293, 120, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Deck D-4 of the Anilox-Staith AS-HIL central-impression mockup is already printing "
                "when a doctor-blade AE burst of 55 pps lands 190 us before the CI-drum encoder "
                "that still claims 4.8 m/s is legal under a 6.0 m/s cap. AE-first parks the deck; "
                "drum-first would keep 4.8 m/s because the encoder never crossed its own limit. "
                "The HIL CI cylinder is the authority, not the press hall.",
            ),
            ("domain", "flexo-CI-press"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep D-4 from dispatching a scored anilox while CI-drum speed remains under its "
                "own cap.",
            ),
            ("t0_us", 1756850400000293),
            ("gate_latency_us", 800),
            ("race_window_us", 320),
            ("race_window_rel_ms", [6.840, 7.160]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.doctor.pps 55 over 15 cap",
                                "enc.ci.mps 4.8 under 6.0 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; drum-first dispatches 4.8 m/s on a "
                            "'encoder still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one doctor AE puck slot versus the CI-drum encoder publisher "
                            "on this HIL flexo bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + drum 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have dispatched 4.8 m/s into a scored anilox.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "doctor-blade AE puck, 50 kHz, 26 us jitter",
                    "CI-drum encoder, 1 kHz, 32 us jitter",
                    "anilox tach (context)",
                    "ink viscometer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 15.0),
                        ("observed_ae_pps", 55.0),
                        ("ci_m_s", 4.8),
                        ("ci_cap_m_s", 6.0),
                        ("proposed_m_s", 4.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. D-4 HIL indexed; 4.8 m/s armed.",
                    "2. CI drum 4.8 m/s under 6.0; AE 55 pps over 15.",
                    "3. Drum precursor at 1.360 ms.",
                    "4. Race window [6.840, 7.160] ms.",
                    "5. ae.doctor.pps 55 at 6.840 ms (winner).",
                    "6. enc.ci.mps 4.8 at 7.020 ms (loser by 180 us).",
                    "7. Gate at 7.640 ms: REJECT hold, do not dispatch.",
                    "8. Deck 0 m/s; drum left at 4.8 encoder counts.",
                    "9. Anilox inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min blade reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_deck"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ci_m_s", 4.8),
                        ("hold", False),
                        ("anilox_rpm", 210.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 55.0),
                        ("ae_cap_pps", 15.0),
                        ("ci_m_s", 4.8),
                        ("ci_cap_m_s", 6.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.8 m/s because the CI-drum encoder is under 6.0, treating the "
                "55 pps AE as doctor chatter rather than a scored anilox.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Doctor AE 55 pps won by 180 us, so the anilox is scored, not still a drum-speed "
                "story. CI encoder 4.8 m/s is under 6.0 and does not authorize dispatch. REJECT: "
                "hold deck 4.8 -> 0 m/s. A MODIFY that only trims drum speed would leave the scored roll.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ae_pps",
                            OrderedDict(
                                [
                                    ("cap", 15.0),
                                    ("observed", 55.0),
                                    ("executed_ci_m_s", 0.0),
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
            ("name", "hold_flexo_deck"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ci_m_s", 0.0),
                        ("hold", True),
                        ("anilox_rpm", 0.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: deck 4.8 -> 0 m/s. CI encoder left under its own 6.0 m/s cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT parked D-4. AE 55 pps beat CI-drum 4.8 m/s by 180 us. The encoder "
                "was legal; the anilox was not. 8 min blade reset (abort_s=480) is delayed survey, "
                "not a process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("deck", "held at 0 m/s"),
                        ("drum", "encoder still 4.8 < 6.0 cap"),
                        ("anilox", "8 min blade reset (abort_s=480)"),
                        ("mission", "HIL deck not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "CI-drum encoder never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min doctor-blade reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.doctor.pps (6.840 ms, 55 pps)"),
                        ("loser", "enc.ci.mps (7.020 ms, 4.8 m/s)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Drum-first by < 180 us inside the 320 us window would have dispatched "
                            "4.8 m/s into a scored anilox. The REJECT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7640),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.640 ms, tick 4). The 8 min blade "
                "reset is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    dw = 0.32
    ras = raster_core(
        46,
        120,
        20,
        110,
        routing(
            "thalamic-relay.doctor-ae",
            "spikenaut.policy.deck-hold",
            [
                ("relay.ae.doctor", "policy.deck_hold", 0.70),
                ("relay.enc.ci", "policy.drum_go", 0.24),
            ],
            "dopamine",
            0.05,
            "hold_stdp; DA tags the AE win as a reject-hold bind",
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
            ("decision_window_ms", dw),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop_budget("deck_hold", 56, 0.45, 280.0, dw),
                    pop("drum_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r55-293"),
            (
                "title",
                "Anilox-Staith AS-HIL / Deck D-4: doctor AE 55 pps beats CI-drum 4.8 m/s by "
                "180 us; correct REJECT parks the deck",
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
                    "Correct REJECT. AE 55 > 15 cap beats legal CI-drum encoder. "
                    "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "flexo-CI-press",
                    [
                        "reject",
                        "hil",
                        "ae-vs-encoder",
                        "scored-anilox",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal CI-drum encoder can lose to doctor-blade AE inside a 320 us "
                    "window; reversing 180 us would have dispatched a scored anilox.",
                    3,
                ),
            ),
        ]
    )


def record_294():
    ticks = [
        tick(2880, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7200, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7380, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7840, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8200, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("ir.wall.C", 1.200, 0.40),
        spike("gc.kcl.pct", 2.880, 0.55),
        spike("ir.wall.C", 4.400, 0.48),
        spike("gc.kcl.pct", 7.200, 1.26),
        spike("ir.wall.C", 7.380, 1.08),
        spike("ctrl.gate", 7.840, 0.95),
        spike("gc.kcl.pct", 11.200, 0.78),
        spike("ir.wall.C", 14.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("gc.kcl.pct", 22.600, 0.50),
        spike("ir.wall.C", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(55294, 48, 28000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("draw_tph", 2.4),
            ("kcl_pct", 38.2),
            ("vacuum_kpa", 12.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Vacuum body B-9 inside the Langbeinite-Beck LB-7 CFD train is holding 38.2 pct KCl "
                "against a 35.0 pct supersaturation floor. Wall IR leftover is 72 C under an 85 C "
                "scaling cap. Assay-first accepts the 2.4 t/h crystal draw; wall-first would have "
                "parked a legal body on a 'still climbing' model.",
            ),
            ("domain", "potash-crystallizer"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the LB-7 draw with KCl >= 35.0 pct and wall IR <= 85 C.",
            ),
            ("t0_us", 1756850400000294),
            ("gate_latency_us", 640),
            ("race_window_us", 360),
            ("race_window_rel_ms", [7.200, 7.560]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "gc.kcl.pct 38.2 over 35.0 floor",
                                "ir.wall.C 72 under 85 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Assay-first confirms the already-legal 2.4 t/h draw; wall-first "
                            "would have treated the GC as a climb echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one KCl GC slot versus the wall-IR publisher on this "
                            "simulated crystallizer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (GC 26 + IR 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed draw illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "KCl density GC, 26 us jitter",
                    "body-wall IR pyrometer, 32 us jitter",
                    "vacuum PT (context)",
                    "magma FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("kcl_floor_pct", 35.0),
                        ("observed_kcl_pct", 38.2),
                        ("wall_cap_C", 85.0),
                        ("observed_wall_C", 72.0),
                        ("proposed_draw_tph", 2.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. B-9 indexed on Langbeinite-Beck LB-7; 2.4 t/h draw armed.",
                    "2. Floors/caps: KCl 35.0 pct, wall 85 C.",
                    "3. IR precursor at 1.200 ms.",
                    "4. Race window [7.200, 7.560] ms.",
                    "5. gc.kcl.pct 38.2 at 7.200 ms (winner).",
                    "6. ir.wall.C 72 at 7.380 ms (loser by 180 us).",
                    "7. Gate at 7.840 ms: ACCEPT 2.4 t/h already legal.",
                    "8. Draw continues; no extra hold.",
                    "9. 6 min survey confirms KCl still over 35.0 pct.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "draw_2p4"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("kcl_pct", 38.2),
                        ("kcl_floor_pct", 35.0),
                        ("wall_C", 72.0),
                        ("wall_cap_C", 85.0),
                        ("draw_tph", 2.4),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 2.4 t/h draw because KCl 38.2 pct is over 35.0 and wall "
                "72 C is under 85 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "KCl 38.2 pct won by 180 us and is over the 35.0 pct floor. Wall 72 C is under "
                "85 C. ACCEPT the already-legal draw.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "kcl_pct",
                            OrderedDict(
                                [
                                    ("floor", 35.0),
                                    ("observed", 38.2),
                                    ("executed_draw_tph", 2.4),
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
            ("name", "draw_2p4"),
            ("parameters", OrderedDict(params.items())),
            (
                "gate_effect",
                "ACCEPT: 2.4 t/h draw and 38.2 pct KCl unchanged. Routing relay.gc.kcl -> "
                "policy.draw_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left B-9 on a 2.4 t/h / 38.2 pct draw. Wall IR hitch did not "
                "justify a hold. 6 min survey confirmed KCl still over 35.0 pct.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("body", "still 2.4 t/h / 12 kPa"),
                        ("kcl", "38.2 pct over 35.0 floor"),
                        ("wall", "72 C under 85"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Wall IR 72 C hitch is residual, not a scaling trip.",
                    "Delayed (survey_s=360): 6 min survey restacks B-9 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "gc.kcl.pct (7.200 ms, 38.2 pct)"),
                        ("loser", "ir.wall.C (7.380 ms, 72 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 180 us would only delay confirmation. The draw stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7840),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (7.840 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 360),
        ]
    )
    dw = 0.36
    ras = raster_core(
        28,
        48,
        42,
        56,
        routing(
            "thalamic-relay.kcl-gc",
            "spikenaut.policy.draw-go",
            [
                ("relay.gc.kcl", "policy.draw_go", 0.68),
                ("relay.ir.wall", "policy.ir_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_draw_stdp; 5-HT tags the draw_go bind at the GC win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 360),
                ("delayed_surprise_s", 360),
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
                    pop_budget("draw_go", 40, 0.45, 250.0, dw),
                    pop("ir_hold", 32, 0.90),
                    pop("kcl_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r55-294"),
            (
                "title",
                "Langbeinite-Beck LB-7 / Body B-9: KCl 38.2 pct beats wall IR 72 C by 180 us; "
                "ACCEPT already-legal 2.4 t/h crystal draw",
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
                    "Correct ACCEPT of an already-legal crystallizer draw. total +1.06 = "
                    "0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "potash-crystallizer",
                    [
                        "accept",
                        "already-legal",
                        "simulated-kcl-body",
                        "gc-vs-ir",
                        "sidecar-convictable",
                        "simulated",
                    ],
                    "Teaches that a KCl assay over floor can confirm an already-legal draw without "
                    "a wall-IR hitch becoming a hold.",
                    4,
                ),
            ),
        ]
    )


def record_295():
    ticks = [
        tick(2016, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5040, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5920, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(300000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.se.kwh", 0.980, 0.41),
        spike("lvdt.gap.mm", 2.016, 0.60),
        spike("ft.se.kwh", 3.200, 0.51),
        spike("lvdt.gap.mm", 5.040, 1.30),
        spike("ft.se.kwh", 5.200, 1.12),
        spike("ctrl.gate", 5.640, 0.97),
        spike("lvdt.gap.mm", 8.100, 0.78),
        spike("ft.se.kwh", 12.400, 0.62),
        spike("ctrl.gate", 16.200, 0.85),
        spike("lvdt.gap.mm", 20.400, 0.54),
        spike("ft.se.kwh", 22.800, 0.43),
    ]
    excerpt = independent_excerpt(55295, 80, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("gap_mm", 1.40),
            ("se_kwh_odt", 1.18),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Refiner plate P-11 at Spruce-Grain SG-2 is already at 1.40 mm gap against a 1.10 mm "
                "minimum, with specific energy 1.18 kWh/odt under 1.40. Gap-first accepts the plate; "
                "energy-first would have parked a legal TMP pass on a 'still tightening' model.",
            ),
            ("domain", "tmp-chip-refiner"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run P-11 at 1.40 mm gap, keep specific energy <= 1.40 kWh/odt, and leave the "
                "TMP line on schedule.",
            ),
            ("t0_us", 1756850400000295),
            ("gate_latency_us", 600),
            ("race_window_us", 280),
            ("race_window_rel_ms", [5.040, 5.320]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "lvdt.gap.mm 1.40 over 1.10 floor",
                                "ft.se.kwh 1.18 under 1.40 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Gap-first confirms the already-legal 1.40 mm plate; energy-first "
                            "would have treated the LVDT as a hitch echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one plate-LVDT slot versus the specific-energy publisher on "
                            "this TMP refiner bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (LVDT 22 + energy 30): 3.08x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal plate.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "plate LVDT, 2 kHz, 22 us jitter",
                    "specific-energy FT, 1 kHz, 30 us jitter",
                    "dilution FT (context)",
                    "housing vibration (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("gap_floor_mm", 1.10),
                        ("observed_gap_mm", 1.40),
                        ("se_cap_kwh_odt", 1.40),
                        ("observed_se_kwh_odt", 1.18),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Plate P-11 indexed on Spruce-Grain SG-2; 1.40 mm gap armed.",
                    "2. Gap over 1.10 floor; SE 1.18 under 1.40 cap.",
                    "3. Energy precursor at 0.980 ms.",
                    "4. Race window [5.040, 5.320] ms.",
                    "5. lvdt.gap.mm 1.40 at 5.040 ms (winner).",
                    "6. ft.se.kwh 1.18 at 5.200 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 1.40 mm.",
                    "8. Gap stays 1.40 mm; SE stays 1.18.",
                    "9. Freeness on-spec at the latency chest.",
                    "10. Delayed (dwell_s=300): 5 min plate reseq.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_plate_gap"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("gap_mm", 1.40),
                        ("gap_floor_mm", 1.10),
                        ("se_kwh_odt", 1.18),
                        ("se_cap_kwh_odt", 1.40),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.40 mm because gap is over the 1.10 mm floor and specific "
                "energy 1.18 is under 1.40 kWh/odt.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Plate LVDT 1.40 mm won by 160 us, so the gap is already legal, not still "
                "tightening. Specific energy 1.18 is under 1.40. ACCEPT the 1.40 mm plate. A REJECT "
                "would idle a legal TMP refiner.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "gap_mm",
                            OrderedDict(
                                [
                                    ("floor", 1.10),
                                    ("observed", 1.40),
                                    ("executed_gap_mm", 1.40),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 160),
                                    ("combined_jitter_us", 52),
                                    ("ratio", 3.08),
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
            ("name", "hold_plate_gap"),
            ("parameters", OrderedDict(params.items())),
            ("gate_effect", "ACCEPT: leave 1.40 mm; SE 1.18; plate legal."),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 1.40 mm plate. Gap beat specific energy by "
                "160 us. 5 min plate reseq (dwell_s=300) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("gap", "1.40 mm held"),
                        ("se", "1.18 < 1.40 cap"),
                        ("freeness", "latency chest on-spec"),
                        ("reseq", "5 min plate reseq (dwell_s=300)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Specific-energy FT never approached 1.40 kWh/odt; gap was already over floor.",
                    "Delayed (dwell_s=300): 5 min plate reseq after P-11.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "lvdt.gap.mm (5.040 ms, 1.40 mm)"),
                        ("loser", "ft.se.kwh (5.200 ms, 1.18 kWh/odt)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Energy-first by < 160 us inside the 280 us window would have REJECTED "
                            "an already-legal plate. The ACCEPT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5640),
            (
                "reward_inflection_note",
                "Task and safety rise at the correct ACCEPT (5.640 ms, tick 4). The 5 min reseq "
                "is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 300),
        ]
    )
    dw = 0.28
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.plate-lvdt",
            "spikenaut.policy.gap-go",
            [
                ("relay.lvdt.gap", "policy.gap_go", 0.67),
                ("relay.ft.se", "policy.se_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the plate-LVDT win as an already-legal gap",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("dwell_s", 300),
                ("delayed_surprise_s", 300),
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
                    pop_budget("gap_go", 40, 0.45, 250.0, dw),
                    pop("se_hold", 32, 0.90),
                    pop("gap_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r55-295"),
            (
                "title",
                "Spruce-Grain SG-2 / Plate P-11: gap 1.40 mm beats specific energy 1.18 kWh/odt by "
                "160 us; correct ACCEPT of an already-legal TMP plate",
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
                    "Correct ACCEPT. Gap 1.40 > 1.10; SE 1.18 < 1.40. "
                    "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "tmp-chip-refiner",
                    [
                        "accept",
                        "designed",
                        "gap-vs-energy",
                        "already-legal-plate",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal specific-energy FT can lose to plate LVDT inside a 280 us "
                    "window; reversing 160 us would have REJECTED an already-legal TMP plate.",
                    5,
                ),
            ),
        ]
    )

