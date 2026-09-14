def record_266():
    excerpt, extra = lif_266_excerpt()
    ticks = [
        tick(2480, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(6140, 0.07, -0.03, -0.03, 0.01, -0.01),
        tick(6348, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(7060, 0.07, -0.05, -0.03, 0.02, -0.02),
        tick(22100, 0.05, -0.38, -0.03, -0.02, -0.02),
        tick(840000000, 0.02, -0.05, -0.01, 0.00, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Chip-Toft CT-6 is already holding Kamyr-Tube KT-4 at 18.4 t/h steam while "
                "the extraction liquor RTD sits at 178 C against a 168 C chip-column cap. A "
                "liquor-first latch clamps the steam; a steam-first story would keep the "
                "18.4 t/h cruise. Stored hoop in the liquor heater is not yet an observable "
                "of either race channel.",
            ),
            ("domain", "kamyr-chip-digester"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the KT-4 continuous cook, keep liquor <= 168 C, and leave the "
                "heater tubes unmarked.",
            ),
            ("t0_us", 1756794621000266),
            ("gate_latency_us", 920),
            ("race_window_us", 500),
            ("race_window_rel_ms", [6.05, 6.55]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.liquor.C 178 C pulse",
                                "enc.steam.tph 18.4 t/h cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Liquor-first latches steam 18.4 -> 11.2 t/h; steam-first keeps "
                            "cruise on a still-cooling chip-column model.",
                        ),
                        (
                            "window_derivation",
                            "500 us = one 1 kHz liquor-RTD sample minus steam-encoder group "
                            "delay on this Kamyr bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 208 us vs combined jitter ~64 us (liquor 28 + steam 36): 3.2x over "
                            "a 2.0x trust floor. Reversing order by < 208 us inside the 500 us window "
                            "would have kept 18.4 t/h cruise; predicted next-sample 171 C > 168 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "extraction-liquor RTD, 1 kHz, 28 us timestamp jitter",
                    "steam-flow encoder, 500 Hz, 36 us jitter",
                    "heater-shell AE puck (context until the tube rupture)",
                    "chip-meter PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("liquor_cap_C", 168.0),
                        ("observed_liquor_C", 178.0),
                        ("proposed_steam_t_h", 18.4),
                        ("chip_feed_odt_h", 42.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Chip-Toft CT-6 indexed onto KT-4; steam armed at 18.4 t/h.",
                    "2. Cruise 18.4 t/h; liquor 178 C against 168 C chip-column cap.",
                    "3. Steam precursor at 1.180 ms; liquor warm-start 178 C.",
                    "4. Race window [6.050, 6.550] ms opens on the Kamyr bus.",
                    "5. tc.liquor.C 178 C at 6.140 ms (winner).",
                    "6. enc.steam.tph 18.4 t/h at 6.348 ms (loser by 208 us).",
                    "7. Gate at 7.060 ms (winner + 920 us): MODIFY clamp 18.4 -> 11.2 t/h.",
                    "8. Clamp executes; next-sample liquor 164 C < 168 cap.",
                    "9. At 22.100 ms stored hoop still ruptures an 18 mm heater tube; AE burst.",
                    "10. Isolate 14 min (abort_s=840); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_steam_flow"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_t_h", 18.4),
                        ("chip_feed_odt_h", 42.0),
                        ("kappa_target", 28.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("liquor_C", 178.0),
                        ("liquor_cap_C", 168.0),
                        ("predicted_unclamped_next_C", 171.0),
                        ("steam_t_h", 18.4),
                        ("race_margin_us", 208),
                        ("combined_jitter_us", 64),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.4 t/h cruise: 178 C looks like a chip-meter spike, not "
                "heater contact, and KT-4 volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Liquor 178 C won by 208 us, so the heater is loading heat, not "
                "still cooling. Holding 18.4 t/h predicts next-sample 171 C > 168 cap. "
                "MODIFY: steam 18.4 -> 11.2 t/h. Observed after clamp 164 C < 168. A full "
                "REJECT is not indicated: a sound Kamyr cook accepts 11.2 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "liquor_C",
                            OrderedDict(
                                [
                                    ("cap", 168.0),
                                    ("observed", 178.0),
                                    ("predicted_unclamped_next", 171.0),
                                    ("clamped_steam_t_h", 11.2),
                                    ("observed_after_clamp", 164.0),
                                ]
                            ),
                        ),
                        (
                            "steam_t_h",
                            OrderedDict(
                                [
                                    ("proposed", 18.4),
                                    ("clamped", 11.2),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 208),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 3.25),
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
            ("name", "clamped_steam_flow"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_t_h", 11.2),
                        ("chip_feed_odt_h", 42.0),
                        ("kappa_target", 28.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: steam 18.4 -> 11.2 t/h. Process-correct vs the 168 C liquor "
                "cap. Heater-tube rupture still occurs at 22.100 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held liquor at 164 C. At 22.100 ms stored "
                "hoop in the liquor heater still ruptured an 18 mm tube. Clamp reduced dump energy; "
                "it did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("steam", "clamp executed; peak 164 C < 168"),
                        ("heater_tube", "18 mm rupture at 22.100 ms"),
                        ("repair", "14 min isolate (abort_s=840)"),
                        ("mission", "KT-4 cook incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither liquor RTD nor steam-flow predicted the hoop charge; ae.heater.rupture is a new channel at 22.100 ms, 15.040 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=840): 14 min isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "14 min isolate after an 18 mm heater-tube rupture. Safety head -0.56 "
                "prices the split; task_progress stays +0.30 because the steam clamp completed "
                "under the 168 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.liquor.C (6.140 ms, 178 C)"),
                        ("loser", "enc.steam.tph (6.348 ms, 18.4 t/h)"),
                        ("margin_us", 208),
                        (
                            "counterfactual_if_reversed",
                            "Steam-first by < 208 us inside the 500 us window would have kept "
                            "18.4 t/h cruise; predicted next-sample 171 C would have exceeded "
                            "the 168 cap even without the hoop charge. The MODIFY is still the "
                            "correct process. The rupture is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22100),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.100 ms heater-tube rupture (tick t_us=22100), inside "
                "the 42 ms raster. The correct MODIFY at 7.060 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=840 isolate tick.",
            ),
        ]
    )
    spikes = [
        spike("enc.steam.ctx", 1.180, 0.41),
        spike("tc.liquor.C", 2.480, 0.60),
        spike("enc.steam.tph", 3.720, 0.49),
        spike("tc.liquor.C", 6.140, 1.29),
        spike("enc.steam.tph", 6.348, 1.12),
        spike("ctrl.gate", 7.060, 0.97),
        spike("tc.liquor.C", 8.420, 0.78),
        spike("enc.steam.tph", 11.200, 0.61),
        spike("ctrl.gate", 15.100, 0.83),
        spike("ae.heater.rupture", 22.100, 1.44),
        spike("ae.heater.rupture", 24.040, 0.89),
        spike("enc.steam.ctx", 31.800, 0.40),
        spike("tc.liquor.C", 38.600, 0.52),
    ]
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.kamyr-liquor",
            "spikenaut.policy.steam-clamp",
            [
                ("relay.tc.liquor", "policy.steam_clamp", 0.67),
                ("relay.enc.steam", "policy.steam_hold", 0.29),
                ("relay.ae.rupture", "policy.steam_clamp", -0.44),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at liquor win (6.140 ms) opens a 50 ms "
            "eligibility trace that still covers the 22.100 ms heater-tube rupture",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.50),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("steam_clamp", 38, 0.50, 263.2, 5),
                    pop("steam_hold", 38, 0.50, 52.6, 1),
                    pop("liquor_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r50-266"),
            (
                "title",
                "Chip-Toft CT-6 / Kamyr-Tube KT-4: liquor 178 C beats steam-flow by 208 us; correct "
                "MODIFY still eats an in-window heater-tube rupture (partnered negative total -0.44)",
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
                    "42 ms raster. total -0.44 = 0.30 + -0.56 + -0.14 + 0.02 + -0.06. Named isolate "
                    "(abort_s=840) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "kamyr-chip-digester",
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
                    "14 min isolate.",
                    1,
                ),
            ),
        ]
    )


def record_267():
    ticks = [
        tick(1680, -0.02, -0.01, -0.03, -0.01, 0.01),
        tick(4260, -0.05, -0.02, -0.04, -0.02, 0.01),
        tick(4412, -0.03, -0.01, -0.04, -0.02, 0.01),
        tick(5040, -0.08, -0.03, -0.09, -0.04, 0.02),
        tick(6820, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(1440000000, -0.02, 0.00, -0.02, 0.00, 0.00),
    ]
    spikes = [
        spike("dp.nox.ctx", 0.920, 0.39),
        spike("nh3.pct", 1.680, 0.57),
        spike("loop.mA", 2.440, 0.50),
        spike("nh3.pct", 4.260, 1.30),
        spike("loop.mA", 4.412, 1.14),
        spike("ctrl.gate", 5.040, 0.99),
        spike("nh3.pct", 6.820, 0.72),
        spike("loop.mA", 8.200, 0.60),
        spike("ctrl.gate", 12.400, 0.81),
        spike("dp.nox.ctx", 16.800, 0.41),
        spike("nh3.pct", 21.200, 0.52),
        spike("loop.mA", 25.100, 0.46),
    ]
    excerpt = independent_excerpt(50267, 96, 26000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Nox-Skid NX-4 on Honeycomb-Dene HD-3 is armed for a 4.8 pct NH3 injection "
                "with live reagent 4.8 pct against a 10.0 pct slip cap. A 4-20 mA transmitter "
                "on the same valve still reports 11.68 mA (span 0-10 pct). Pct-first should "
                "ACCEPT the injection; a weak supervisor that treats the raw milliamp as an "
                "engineering percent will REJECT a legal move.",
            ),
            ("domain", "scr-nh3-injection"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 4.8 pct NH3 while reagent stays <= 10.0 pct; do not spend a raw "
                "milliamp loop on the injection hold.",
            ),
            ("t0_us", 1756794621000267),
            ("gate_latency_us", 780),
            ("race_window_us", 360),
            ("race_window_rel_ms", [4.20, 4.56]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "nh3.pct 4.8 pct",
                                "loop.mA 11.68 mA raw-count",
                            ],
                        ),
                        (
                            "semantics",
                            "Pct-first should ACCEPT 4.8 pct (4.8 < 10.0 cap). "
                            "Milliamp-first tempts a weak supervisor to treat 11.68 mA as 11.68 pct.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one NH3 Hall sample minus 4-20 mA encoder "
                            "group delay on this dual-bus skid.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 152 us vs combined jitter ~52 us (pct 22 + mA 30): 2.9x over "
                            "a 2.0x trust floor. Order is correctly pct-first. The error is which "
                            "quantity the REJECT is bound to, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "NH3 mass-fraction Hall, 4 kHz, 22 us jitter",
                    "4-20 mA valve loop, 4 kHz, 30 us jitter",
                    "NOx differential (context)",
                    "catalyst-brick thermocouple (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("nh3_cap_pct", 10.0),
                        ("nh3_pct", 4.8),
                        ("loop_mA", 11.68),
                        ("loop_span_pct", 10.0),
                        ("proposed_nh3_pct", 4.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. NX-4 valve latched; 4.8 pct NH3 armed on HD-3.",
                    "2. Live 4.8 pct; 4-20 mA loop 11.68 mA on a separate raw-count bus.",
                    "3. NOx-dp precursor at 0.920 ms.",
                    "4. Race window [4.200, 4.560] ms.",
                    "5. nh3.pct 4.8 pct at 4.260 ms (winner).",
                    "6. loop.mA 11.68 mA at 4.412 ms (loser by 152 us).",
                    "7. Gate at 5.040 ms: REJECT hold 0.00 pct (incorrect).",
                    "8. Legal injection cancelled; reagent still 4.8 pct < 10.0 cap.",
                    "9. 11.68 mA remains a loop current, not a percent.",
                    "10. Delayed missed_window_s=1440 (24 min catalyst window) while the skid waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "nh3_inject_48"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("nh3_pct", 4.8),
                        ("hold", False),
                        ("unit", "pct"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("nh3_pct", 4.8),
                        ("nh3_cap_pct", 10.0),
                        ("unit_live", "pct"),
                        ("loop_mA", 11.68),
                        ("loop_as_pct_if_misbound", 11.68),
                        ("unit_shadow", "mA"),
                        ("proposed_nh3_pct", 4.8),
                        ("race_margin_us", 152),
                        ("combined_jitter_us", 52),
                        ("missed_window_s", 1440),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.8 pct NH3 because live 4.8 pct is under "
                "the 10.0 pct slip cap; 11.68 mA is a 4-20 mA loop current, not 11.68 pct.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Loop 11.68 mA looks like a reagent excursion over a 10 pct cap once the "
                "supervisor treats milliamps as percent. Pct-first is treated as a "
                "noisy echo of the same loop. Over-caution on a dual-bus skid is the stated doctrine.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "nh3_pct",
                            OrderedDict(
                                [
                                    ("cap", 10.0),
                                    ("observed", 4.8),
                                    ("executed_nh3_pct", 0.0),
                                    ("unit", "pct"),
                                ]
                            ),
                        ),
                        (
                            "loop_mA",
                            OrderedDict(
                                [
                                    ("observed", 11.68),
                                    ("misbound_as_pct", 11.68),
                                    ("misbound_as", "reagent_excursion"),
                                    ("unit", "mA"),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 152),
                                    ("combined_jitter_us", 52),
                                    ("ratio", 2.92),
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
            ("name", "nh3_hold_wrong_mA"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("nh3_pct", 0.0),
                        ("hold", True),
                        ("unit", "pct"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): NH3 4.8 -> 0.00 pct. Routing relay.loop.mA -> "
                "policy.nh3_hold; live 4.8 pct left unused as a go signal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT held NX-4 at 0.00 pct. Live 4.8 pct was under the 10.0 pct "
                "cap; 11.68 mA was a 4-20 mA loop current, not 11.68 pct. 24 min catalyst "
                "window missed (missed_window_s=1440). Correct gate was ACCEPT of the 4.8 pct injection.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("nh3", "held; 0.00 pct; live still 4.8 pct < 10.0"),
                        ("loop", "11.68 mA unused, still a current not a percent"),
                        ("skid", "24 min catalyst window missed"),
                        ("mission", "injection deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Pct-first was the correct order and the live number was legal; the REJECT spent that win on the raw milliamp.",
                    "Delayed (missed_window_s=1440): HD-3 loses the 24 min catalyst window; next window 6.1 h.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT the 4.8 pct NH3 injection; leave 11.68 mA to its own loop bus.",
                        ),
                        ("correct_unit", "pct"),
                        ("wrong_unit", "mA"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("nh3_pct", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "Missed 24 min catalyst window (task/efficiency); reagent never exceeded 4.8 pct (safety near-miss of a false hold).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "nh3.pct (4.260 ms, 4.8 pct)"),
                        ("loser", "loop.mA (4.412 ms, 11.68 mA)"),
                        ("margin_us", 152),
                        (
                            "counterfactual_if_reversed",
                            "Milliamp-first by < 152 us would still be a loop current, not 11.68 pct; "
                            "a correct gate binds nh3.pct to nh3_go either way. The wrong "
                            "REJECT spent the pct win on the raw milliamp.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5040),
            (
                "reward_inflection_note",
                "Task, efficiency, and coherence drop at the wrong REJECT (5.040 ms, tick 4). "
                "The 24 min missed window is delayed surprise, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        26,
        96,
        32,
        80,
        routing(
            "relay.loop.mA",
            "policy.nh3_hold",
            [
                ("relay.loop.mA", "policy.nh3_hold", 0.74),
                ("relay.nh3.pct", "policy.nh3_hold", 0.19),
            ],
            "acetylcholine",
            0.06,
            "raw_mA_stdp; ACh tags the (wrong) nh3_hold bind at the milliamp loop",
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
            ("decision_window_ms", 0.36),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("nh3_hold", 46, 0.50, 241.5, 4),
                    pop("nh3_go", 46, 0.80, 6.0, 0),
                    pop("loop_ctx", 30, 0.55, 92.6, 1),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r50-267"),
            (
                "title",
                "WRONG-REJECT at Honeycomb-Dene HD-3 / Nox-Skid NX-4: live 4.8 pct < 10.0 pct cap; "
                "supervisor treats 11.68 mA raw loop as 11.68 pct",
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
                    "Wrong-reject. Sidecar arithmetic 4.8 < 10.0 on pct is true; REJECT bound "
                    "to raw milliamp. total -0.58 = -0.22 + -0.08 + -0.24 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "scr-nh3-injection",
                    [
                        "reject",
                        "wrong-gate",
                        "raw-mA-as-EU",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct pct-first race can still be a wrong gate "
                    "when the REJECT binds a 4-20 mA raw count onto the injection hold. Convictable from "
                    "unit IDs and caps without SCR physics.",
                    2,
                    supervisor_error_type="wrong-reject",
                ),
            ),
        ]
    )


def record_268():
    ticks = [
        tick(2540, 0.01, 0.05, 0.01, 0.01, 0.01),
        tick(5860, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(6028, 0.02, 0.07, 0.02, 0.02, 0.01),
        tick(6940, 0.03, 0.12, 0.04, 0.03, 0.02),
        tick(9120, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("tc.slab.ctx", 1.420, 0.42),
        spike("py.slab.C", 2.540, 0.61),
        spike("ir.roof.glint", 4.200, 0.48),
        spike("py.slab.C", 5.860, 1.33),
        spike("ir.roof.glint", 6.028, 1.11),
        spike("ctrl.gate", 6.940, 1.02),
        spike("py.slab.C", 9.120, 0.76),
        spike("tc.slab.ctx", 14.400, 0.43),
        spike("ir.roof.glint", 18.600, 0.57),
        spike("ctrl.gate", 24.800, 0.80),
        spike("py.slab.C", 31.200, 0.53),
        spike("tc.slab.ctx", 38.400, 0.37),
        spike("ir.roof.glint", 42.800, 0.45),
    ]
    excerpt = independent_excerpt(50268, 112, 44000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Walking-Beam WB-2 is frozen on Reheat-Garth RG-8's HIL slab furnace while a "
                "surface pyrometer reports 1284 C against a 1260 C discharge cap. A roof-IR, "
                "lit by the pad lamp spectrum, still reads 1190 C apparent. Pyrometer-first "
                "latches REJECT hold; glint-first would walk a 1.80 m/min hot slab.",
            ),
            ("domain", "walking-beam-reheat"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not walk the beam unless slab surface <= 1260 C; keep speed 0.00 m/min "
                "until the injected hot-slab packet drops.",
            ),
            ("t0_us", 1756794621000268),
            ("gate_latency_us", 1080),
            ("race_window_us", 420),
            ("race_window_rel_ms", [5.80, 6.22]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "py.slab.C 1284 C",
                                "ir.roof.glint 1190 C apparent",
                            ],
                        ),
                        (
                            "semantics",
                            "Pyrometer-first latches REJECT hold 0.00 m/min; glint-first would "
                            "commit 1.80 m/min on an apparent 1190 C under-read of a hot-slab packet.",
                        ),
                        (
                            "window_derivation",
                            "420 us = one surface-pyrometer slot versus roof-IR integration on this "
                            "reheat HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 168 us vs combined jitter ~56 us (pyrometer 24 + IR 32): 3.0x "
                            "over a 2.0x trust floor. Pad injects the lamp 100-140 us before the "
                            "pyrometer (geometric lag, not a sensor fault); the apparent "
                            "1190 C packet is still the loser in this 420 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "slab-surface pyrometer, 5 kHz burst, 24 us jitter",
                    "roof IR, 200 Hz, 32 us jitter",
                    "skid-rail thermocouple (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("discharge_cap_C", 1260.0),
                        ("observed_slab_C", 1284.0),
                        ("roof_apparent_C", 1190.0),
                        ("proposed_walk_m_min", 1.80),
                        ("lamp_inject_lead_us", [100, 140]),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("pad", "Reheat-Garth RG-8 walking-beam mockup"),
                        ("injected", "hot-slab packet + roof-IR lamp spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop walking-beam furnace. Invented plant; not a live reheat mill.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Walking-Beam WB-2 on the RG-8 HIL furnace; walk 1.80 m/min armed.",
                    "2. Lamp injected 100-140 us before pyrometer sees the hot-slab packet.",
                    "3. Skid-rail precursor at 1.420 ms.",
                    "4. Race window [5.800, 6.220] ms.",
                    "5. py.slab.C 1284 C at 5.860 ms (winner).",
                    "6. ir.roof.glint 1190 C at 6.028 ms (loser by 168 us).",
                    "7. Gate at 6.940 ms: REJECT hold 0.00 m/min; do not walk 1.80 m/min.",
                    "8. Slab remains over cap this cycle; discharge cap held.",
                    "9. Soak recycle queued on the pad.",
                    "10. Delayed (abort_s=480): 8 min beam retune and lamp-spectrum retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "walk_beam_180"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("walk_m_min", 1.80),
                        ("hold", False),
                        ("roof_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("slab_C", 1284.0),
                        ("discharge_cap_C", 1260.0),
                        ("roof_apparent_C", 1190.0),
                        ("race_margin_us", 168),
                        ("combined_jitter_us", 56),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.80 m/min walk because roof-IR apparent 1190 C looks "
                "under the 1260 C cap, treating slab 1284 C as a noisy sheath echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Slab 1284 C is over the 1260 C discharge cap. Roof-IR apparent "
                "1190 C is a HIL lamp under-read of a hot-slab packet, not a clearance. REJECT: hold "
                "0.00 m/min; do not commit 1.80 m/min across the beam.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "slab_C",
                            OrderedDict(
                                [
                                    ("cap", 1260.0),
                                    ("observed_slab", 1284.0),
                                    ("roof_apparent", 1190.0),
                                ]
                            ),
                        ),
                        (
                            "walk_m_min",
                            OrderedDict(
                                [
                                    ("proposed", 1.80),
                                    ("executed", 0.00),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 168),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 3.00),
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
            ("name", "hold_for_discharge_cap"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("walk_m_min", 0.00),
                        ("hold", True),
                        ("roof_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0.00 m/min; 1.80 m/min walk cancelled. Slab 1284 > 1260 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Walking-Beam WB-2 at 0.00 m/min. Slab over cap this cycle; "
                "discharge cap held. Roof-IR apparent was not treated as a slab clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("beam", "held; walk 0.00 m/min"),
                        ("slab", "still over 1260 C this cycle"),
                        ("roof_ir", "1190 C unused as clearance"),
                        ("mission", "walk deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: lamp was injected 100-140 us before the pyrometer, yet the pyrometer still won the 420 us race.",
                    "Delayed (abort_s=480): pad policy update forbids treating roof-IR apparent as a slab substitute after an 8 min retune.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "py.slab.C (5.860 ms, 1284 C)"),
                        ("loser", "ir.roof.glint (6.028 ms, 1190 C apparent)"),
                        ("margin_us", 168),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 168 us inside the 420 us window would have committed "
                            "1.80 m/min with slab 1284 > 1260 cap. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6940),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (6.940 ms, tick 4) as the hold "
                "locks in over the illegal walk.",
            ),
        ]
    )
    ras = raster_core(
        44,
        112,
        18,
        89,
        routing(
            "thalamic-relay.reheat-slab",
            "spikenaut.policy.beam-hold",
            [
                ("relay.py.slab", "policy.walk_hold", 0.70),
                ("relay.ir.roof", "policy.walk_commit", 0.26),
                ("relay.tc.slab", "policy.walk_hold", 0.12),
            ],
            "dopamine",
            0.09,
            "discharge_stdp; DA at pyrometer win (5.860 ms) tags walk_hold over walk_commit",
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
            ("decision_window_ms", 0.42),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("walk_hold", 54, 0.50, 220.5, 5),
                    pop("walk_commit", 42, 0.50, 56.7, 1),
                    pop("slab_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r50-268"),
            (
                "title",
                "Reheat-Garth RG-8 HIL / Walking-Beam WB-2: slab 1284 C beats roof-IR 1190; "
                "correct REJECT holds the hot-slab walk",
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
                    "Correct REJECT. Slab over cap; roof-IR lamp under-read unused as clearance. "
                    "total +0.78 = 0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "walking-beam-reheat",
                    [
                        "reject",
                        "hil-reheat",
                        "slab-vs-roof",
                        "discharge-cap",
                        "hil",
                    ],
                    "Teaches that a HIL roof-IR lamp under-read can lose to a slab pyrometer inside a "
                    "420 us window; reversing 168 us would have selected an illegal hot-slab walk.",
                    3,
                ),
            ),
        ]
    )


def record_269():
    ticks = [
        tick(3120, 0.04, 0.03, 0.02, 0.01, 0.00),
        tick(6980, 0.09, 0.06, 0.04, 0.02, 0.01),
        tick(7188, 0.05, 0.04, 0.03, 0.02, 0.01),
        tick(7440, 0.12, 0.09, 0.04, 0.03, 0.01),
        tick(9680, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.02, 0.02, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("pt.jacket.ctx", 1.620, 0.41),
        spike("rtd.wall.C", 3.120, 0.58),
        spike("ir.jacket.glint", 5.040, 0.47),
        spike("rtd.wall.C", 6.980, 1.28),
        spike("ir.jacket.glint", 7.188, 1.08),
        spike("ctrl.gate", 7.440, 0.95),
        spike("rtd.wall.C", 9.680, 0.72),
        spike("pt.jacket.ctx", 13.900, 0.44),
        spike("ir.jacket.glint", 17.600, 0.56),
        spike("ctrl.gate", 21.800, 0.79),
        spike("rtd.wall.C", 25.400, 0.50),
        spike("pt.jacket.ctx", 27.600, 0.37),
    ]
    excerpt = independent_excerpt(50269, 68, 28000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Initiator-Loop IL-7 at Tubular-Howe TH-5 still holds 18 ppm peroxide while a "
                "312 C inner-wall pulse sits over a 295 C LDPE skin cap. A jacket IR on the same "
                "bay still claims 246 C cool-glint. Wall-first latches an initiator clamp; "
                "glint-first would keep 18 ppm into a close-out surge.",
            ),
            ("domain", "ldpe-tubular-reactor"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run TH-5 only if inner wall <= 295 C; otherwise clamp "
                "initiator so the surge is not made at 18 ppm.",
            ),
            ("t0_us", 1756794621000269),
            ("gate_latency_us", 460),
            ("race_window_us", 480),
            ("race_window_rel_ms", [6.90, 7.38]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.wall.C 312 C",
                                "ir.jacket.glint 246 C cool-glint",
                            ],
                        ),
                        (
                            "semantics",
                            "Wall-first latches initiator clamp 18 -> 11 ppm; glint-first keeps "
                            "18 ppm on a false-cool jacket.",
                        ),
                        (
                            "window_derivation",
                            "480 us = one 2 kHz wall-RTD sample versus jacket-IR decode on this "
                            "tubular bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 208 us vs combined jitter ~68 us (wall 30 + jacket 38): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 208 us inside the 480 us "
                            "window would have kept 18 ppm into a 312 C pulse.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "inner-wall RTD, 2 kHz, 30 us jitter",
                    "jacket IR camera, 200 Hz, 38 us jitter",
                    "jacket-oil PT (context)",
                    "initiator-pump encoder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("skin_cap_C", 295.0),
                        ("observed_wall_C", 312.0),
                        ("proposed_initiator_ppm", 18.0),
                        ("jacket_glint_C", 246.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Initiator-Loop indexed onto TH-5 tube; IL-7 armed at 18 ppm.",
                    "2. Jacket IR reports 246 C cool-glint; wall already sees 312 C.",
                    "3. Jacket-PT precursor at 1.620 ms.",
                    "4. Race window [6.900, 7.380] ms.",
                    "5. rtd.wall.C 312 C at 6.980 ms (winner).",
                    "6. ir.jacket.glint 246 C at 7.188 ms (loser by 208 us).",
                    "7. Gate at 7.440 ms: MODIFY initiator 18 -> 11 ppm.",
                    "8. Clamp applies; next-sample wall 288 C < 295 cap.",
                    "9. Tube occupies; next hyper-compressor queued.",
                    "10. Delayed (tubular_reseq_s=360): dispatcher resequences the following drop +6 min.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "initiator_18"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("initiator_ppm", 18.0),
                        ("pressure_bar", 2680.0),
                        ("tube_id", 5),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("wall_C", 312.0),
                        ("skin_cap_C", 295.0),
                        ("jacket_cool", True),
                        ("race_margin_us", 208),
                        ("combined_jitter_us", 68),
                        ("tubular_reseq_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18 ppm initiator because the jacket IR claims the bay "
                "is cool, treating wall 312 C as a sidelobe.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Wall 312 C won by 208 us, so the pulse is inside the 295 C skin cap. "
                "Jacket-IR cool-glint is not a wall temperature. MODIFY: initiator 18 -> 11 ppm. "
                "A full REJECT (kill the tube) is not indicated: 11 ppm is a legal catch-and-pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "wall_C",
                            OrderedDict(
                                [
                                    ("cap", 295.0),
                                    ("observed", 312.0),
                                    ("jacket_cool", True),
                                    ("observed_after_clamp", 288.0),
                                ]
                            ),
                        ),
                        (
                            "initiator_ppm",
                            OrderedDict(
                                [
                                    ("proposed", 18.0),
                                    ("clamped", 11.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 208),
                                    ("combined_jitter_us", 68),
                                    ("ratio", 3.06),
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
            ("name", "clamped_initiator_11"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("initiator_ppm", 11.0),
                        ("pressure_bar", 2680.0),
                        ("tube_id", 5),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: initiator 18 -> 11 ppm. Process-correct vs the 295 C skin cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct MODIFY held IL-7 at 11 ppm. Next-sample wall 288 C under the "
                "295 C cap. Jacket 246 C cool-glint was not treated as a wall clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("initiator", "clamped 18 -> 11 ppm"),
                        ("wall", "288 C < 295 cap after clamp"),
                        ("jacket", "246 C unused as clearance"),
                        ("mission", "drop completed under cap"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Jacket-IR cool-glint lagged the wall pulse by 208 us; order, not amplitude, selected the clamp.",
                    "Delayed (tubular_reseq_s=360): dispatcher resequences the following drop +6 min. Not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.wall.C (6.980 ms, 312 C)"),
                        ("loser", "ir.jacket.glint (7.188 ms, 246 C)"),
                        ("margin_us", 208),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 208 us inside the 480 us window would have kept "
                            "18 ppm into a 312 C pulse over the 295 cap. The MODIFY is "
                            "the correct process either way once wall RTD is bound.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7440),
            (
                "reward_inflection_note",
                "Task and safety step up at the MODIFY gate (7.440 ms, tick 4). Tick 6 is "
                "tubular_reseq_s=360.",
            ),
        ]
    )
    ras = raster_core(
        28,
        68,
        38,
        72,
        routing(
            "thalamic-relay.ldpe-wall",
            "spikenaut.policy.initiator-clamp",
            [
                ("relay.rtd.wall", "policy.init_clamp", 0.65),
                ("relay.ir.jacket", "policy.glint_hold", 0.28),
                ("relay.pt.jacket", "policy.init_clamp", 0.13),
            ],
            "serotonin",
            0.07,
            "skin_stdp; 5-HT at wall win (6.980 ms) tags init_clamp over glint_hold",
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
            ("decision_window_ms", 0.48),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("init_clamp", 32, 0.50, 260.4, 4),
                    pop("glint_hold", 32, 0.50, 65.1, 1),
                    pop("wall_veto", 22, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r50-269"),
            (
                "title",
                "Tubular-Howe TH-5 / Initiator-Loop IL-7: wall 312 C beats jacket cool-glint; "
                "correct MODIFY clamps initiator 18 -> 11 ppm",
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
                    "Correct MODIFY. Wall over cap; jacket cool-glint unused. total +0.94 = "
                    "0.36 + 0.28 + 0.16 + 0.10 + 0.04.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "ldpe-tubular-reactor",
                    [
                        "modify",
                        "designed",
                        "wall-vs-jacket",
                        "skin-cap",
                    ],
                    "Teaches that a cool-glint jacket IR can lose to a legal inner-wall RTD inside "
                    "a 480 us window; reversing 208 us would have kept an illegal 18 ppm initiator.",
                    4,
                ),
            ),
        ]
    )


def record_270():
    ticks = [
        tick(1640, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(3880, 0.11, 0.07, 0.05, 0.03, 0.02),
        tick(4006, 0.06, 0.05, 0.03, 0.02, 0.01),
        tick(4460, 0.14, 0.09, 0.05, 0.04, 0.02),
        tick(6280, 0.07, 0.04, 0.03, 0.01, 0.01),
        tick(300000000, 0.03, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("pt.car.ctx", 0.640, 0.38),
        spike("rtd.coke.C", 1.640, 0.56),
        spike("ir.tower.glint", 2.480, 0.47),
        spike("rtd.coke.C", 3.880, 1.27),
        spike("ir.tower.glint", 4.006, 1.09),
        spike("ctrl.gate", 4.460, 0.96),
        spike("rtd.coke.C", 6.280, 0.75),
        spike("ir.tower.glint", 8.900, 0.60),
        spike("ctrl.gate", 12.600, 0.82),
        spike("pt.car.ctx", 16.200, 0.40),
        spike("rtd.coke.C", 19.800, 0.53),
        spike("ir.tower.glint", 22.400, 0.45),
    ]
    excerpt = independent_excerpt(50270, 80, 24000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Coke-Buggy CB-3 in Quench-Wath QW-1 is already rolling at 1.15 m/s while a "
                "coke RTD sits at 1080 C against a 1200 C incandescent cap that the tower "
                "pyrometer has not crossed. Coke-first should ACCEPT the already-legal 1.15 m/s "
                "roll; glint-first would hold a legal car on lighting.",
            ),
            ("domain", "coke-quench-car"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Run CB-3 when coke RTD is <= 1200 C; do not spend a quench-tower pyrometer "
                "glint on a hold.",
            ),
            ("t0_us", 1756794621000270),
            ("gate_latency_us", 580),
            ("race_window_us", 280),
            ("race_window_rel_ms", [3.82, 4.10]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.coke.C 1080 C",
                                "ir.tower.glint 1240 lighting",
                            ],
                        ),
                        (
                            "semantics",
                            "Coke-first ACCEPTS the already-legal 1080 C roll. Glint-first would "
                            "REJECT a legal car on a 1240 C lighting.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one coke-RTD sample minus tower-pyrometer integration on this "
                            "quench-car simulation.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 126 us vs combined jitter ~50 us (RTD 22 + IR 28): 2.5x over "
                            "a 2.0x trust floor. Reversing order by < 126 us inside the 280 us window "
                            "would have invented a hold on an already-legal 1080 C coke bed.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "coke-bed RTD, 2 kHz, 22 us jitter",
                    "quench-tower pyrometer, 200 Hz, 28 us jitter",
                    "car PT (context)",
                    "buggy-axle torque (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("incandescent_cap_C", 1200.0),
                        ("observed_coke_C", 1080.0),
                        ("tower_glint_C", 1240.0),
                        ("proposed_speed_m_s", 1.15),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. CB-3 seeded; coke at 1080 C under 1200 incandescent cap.",
                    "2. Tower pyrometer glint 1240 from quench lighting, not coke cake.",
                    "3. Car-PT precursor at 0.640 ms.",
                    "4. Race window [3.820, 4.100] ms.",
                    "5. rtd.coke.C 1080 C at 3.880 ms (winner).",
                    "6. ir.tower.glint 1240 at 4.006 ms (loser by 126 us).",
                    "7. Gate at 4.460 ms: ACCEPT 1.15 m/s as proposed.",
                    "8. Roll executes; coke remains 1080 C < 1200.",
                    "9. Charge emptied; next oven queued.",
                    "10. Delayed (survey_hold_s=300): 5.0 min quench survey. Not a safety inflection.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "roll_115"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_s", 1.15),
                        ("hold", False),
                        ("water_m3_min", 8.4),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("coke_C", 1080.0),
                        ("incandescent_cap_C", 1200.0),
                        ("tower_glint_C", 1240.0),
                        ("race_margin_us", 126),
                        ("combined_jitter_us", 50),
                        ("survey_hold_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.15 m/s because coke RTD 1080 C is under the 1200 C "
                "incandescent cap; tower 1240 C is lighting, not coke.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Coke RTD 1080 C is under the 1200 C incandescent cap. Tower 1240 C is a "
                "lighting glint, not coke load. ACCEPT the proposed 1.15 m/s; do not invent a hold.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "coke_C",
                            OrderedDict(
                                [
                                    ("cap", 1200.0),
                                    ("observed", 1080.0),
                                    ("tower_glint_C", 1240.0),
                                ]
                            ),
                        ),
                        (
                            "speed_m_s",
                            OrderedDict(
                                [
                                    ("proposed", 1.15),
                                    ("executed", 1.15),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 126),
                                    ("combined_jitter_us", 50),
                                    ("ratio", 2.52),
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
            ("name", "roll_115"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_s", 1.15),
                        ("hold", False),
                        ("water_m3_min", 8.4),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: proposed 1.15 m/s executed unchanged. Coke 1080 C < 1200; tower glint unused.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT ran CB-3 at 1080 C coke. Tower 1240 C was lighting, not coke. "
                "The proposal was already legal; reversing 126 us would have invented a hold.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("car", "roll executed; coke 1080 C < 1200"),
                        ("tower_ir", "1240 C glint unused as coke"),
                        ("water", "held 8.4 m3/min through the pass"),
                        ("mission", "roll committed"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Tower 1240 C is a legal lighting glint, not a high-coke alarm; coke-first discarded a false hold.",
                    "Delayed (5.0 min / survey_hold_s=300): quench survey. Not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.coke.C (3.880 ms, 1080 C)"),
                        ("loser", "ir.tower.glint (4.006 ms, 1240 lighting)"),
                        ("margin_us", 126),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 126 us inside the 280 us window would have held the car "
                            "on a false high-coke story. The proposal was already under the 1200 cap, "
                            "so the correct gate is still ACCEPT.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4460),
            (
                "reward_inflection_note",
                "Task and safety step up at the ACCEPT gate (4.460 ms, tick 4). Tick 6 is "
                "survey_hold_s=300.",
            ),
        ]
    )
    ras = raster_core(
        24,
        80,
        30,
        58,
        routing(
            "thalamic-relay.coke-rtd",
            "spikenaut.policy.quench-accept",
            [
                ("relay.rtd.coke", "policy.quench_go", 0.63),
                ("relay.ir.tower", "policy.glint_hold", 0.27),
                ("relay.pt.car", "policy.quench_go", 0.15),
            ],
            "adenosine",
            0.16,
            "pre_post_stdp; adenosine at coke win (3.880 ms) opens 160 ms eligibility covering the 4.460 ms accept",
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
            ("decision_window_ms", 0.28),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("quench_go", 40, 0.50, 267.9, 3),
                    pop("glint_hold", 40, 0.50, 8.9, 0),
                    pop("coke_veto", 24, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r50-270"),
            (
                "title",
                "Quench-Wath QW-1 / Coke-Buggy CB-3: coke 1080 C beats tower glint; correct "
                "ACCEPT of an already-legal 1.15 m/s (total +1.18)",
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
                    "Correct ACCEPT. Coke 1080 C < 1200; tower glint is lighting, not coke. "
                    "total +1.18 = 0.46 + 0.32 + 0.20 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "coke-quench-car",
                    [
                        "accept",
                        "simulated-lighting",
                        "coke-vs-tower",
                        "quench-roll",
                        "simulated",
                    ],
                    "Teaches that a quench-tower lighting glint can lose to a legal coke RTD inside a "
                    "280 us window; reversing 126 us would have invented a hold on an already-legal roll.",
                    5,
                ),
            ),
        ]
    )
