def record_231():
    excerpt, extra = lif_231_excerpt()
    extra = OrderedDict(extra)
    extra["abort_s"] = 840
    extra["delayed_surprise_s"] = 840
    ticks = [
        tick(2440, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6120, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(6308, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6840, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22400, 0.04, -0.45, -0.03, -0.01, -0.01),
        tick(840000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Reactor R-7 at Lampblack-Fen LF-4 is feeding 4.2 t/h of feedstock oil while "
                "the throat pyrometer sits at 1548 C against a 1520 C roof cap. Temperature-first "
                "cuts oil to 3.1 t/h; feed-first would keep 4.2 t/h because quench water 18 t/h "
                "is still under the 22 t/h header cap. A hopper bridge already seated in the "
                "pellet elevator does not appear on throat T or oil FT until the AE dump.",
            ),
            ("domain", "carbon-black-reactor"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep Reactor R-7 throat temperature <= 1520 C and finish the pellet sendout "
                "without dumping hot carbon into the bag filter.",
            ),
            ("t0_us", 1756850400000231),
            ("gate_latency_us", 720),
            ("race_window_us", 400),
            ("race_window_rel_ms", [6.0, 6.40]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.throat.C 1548 over 1520 roof cap",
                                "oil.feed.tph 4.2 with quench 18 under 22",
                            ],
                        ),
                        (
                            "semantics",
                            "Temperature-first latches oil-feed clamp 4.2 -> 3.1 t/h; feed-first "
                            "keeps 4.2 t/h on a 'still under quench-header cap' model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one throat-pyrometer slot versus the oil-feed orifice "
                            "publisher on this furnace skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 188 us vs combined jitter 64 us (TC 30 + oil 34): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 188 us inside the 400 us "
                            "window would have kept 4.2 t/h; predicted next-sample 1552 C > 1520 "
                            "roof cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "throat two-color pyrometer, 2 kHz, 30 us jitter",
                    "oil-feed orifice + quench FT, 1 kHz, 34 us jitter",
                    "pellet-elevator AE puck (context)",
                    "bag-filter DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("throat_cap_C", 1520.0),
                        ("observed_throat_C", 1548.0),
                        ("oil_feed_tph", 4.2),
                        ("quench_tph", 18.0),
                        ("quench_cap_tph", 22.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Reactor R-7 indexed; oil 4.2 t/h; throat 1548 C.",
                    "2. Quench 18 t/h under 22 t/h cap; pellet sendout armed.",
                    "3. Orifice precursor at 1.180 ms.",
                    "4. Race window [6.000, 6.400] ms.",
                    "5. tc.throat.C 1548 C at 6.120 ms (winner).",
                    "6. oil.feed.tph 4.2 at 6.308 ms (loser by 188 us).",
                    "7. Gate at 6.840 ms: MODIFY clamp 4.2 -> 3.1 t/h.",
                    "8. After clamp throat 1512 C <= 1520; quench still 18 t/h.",
                    "9. At 22.400 ms a hopper bridge dumps 0.4 t of hot pellet into the bag filter.",
                    "10. 14 min filter fire watch (abort_s=840); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_oil_feed"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("oil_feed_tph", 4.2),
                        ("throat_C", 1548.0),
                        ("quench_tph", 18.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("throat_C", 1548.0),
                        ("throat_cap_C", 1520.0),
                        ("predicted_unclamped_next_C", 1552.0),
                        ("oil_feed_tph", 4.2),
                        ("quench_tph", 18.0),
                        ("quench_cap_tph", 22.0),
                        ("race_margin_us", 188),
                        ("combined_jitter_us", 64),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.2 t/h because quench 18 t/h is under 22, treating the "
                "1548 C throat as a still-sooty pyrometer rather than a roof-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Throat 1548 C won by 188 us, so the reactor is over the 1520 C roof cap, not "
                "still a quench-header story. Holding 4.2 t/h predicts next-sample 1552 C > "
                "1520. MODIFY: oil 4.2 -> 3.1 t/h. Observed after clamp 1512 C <= 1520. A full "
                "REJECT is not indicated: a clean sendout accepts 3.1 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "throat_C",
                            OrderedDict(
                                [
                                    ("cap", 1520.0),
                                    ("observed", 1548.0),
                                    ("predicted_unclamped_next", 1552.0),
                                    ("clamped_oil_tph", 3.1),
                                    ("observed_after_clamp", 1512.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 188),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 2.94),
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
            ("name", "clamped_oil_feed"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("oil_feed_tph", 3.1),
                        ("throat_C", 1512.0),
                        ("quench_tph", 18.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: oil 4.2 -> 3.1 t/h. Process-correct vs the 1520 C roof cap. Hopper "
                "bridge still dumps at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held throat temperature at 1512 C. At 22.400 ms a "
                "hopper bridge already seated in the pellet elevator dumped 0.4 t of hot "
                "carbon into the bag filter. Clamp reduced dump energy; it did not prevent "
                "the dump. Partnered negative: process heads stay honest; world loss is named, "
                "not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("throat", "clamp executed; peak 1512 C <= 1520 cap"),
                        ("hopper_bridge", "dumped at 22.400 ms; 0.4 t hot pellet"),
                        ("repair", "14 min filter fire watch (abort_s=840)"),
                        ("mission", "LF-4 pellet sendout incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither throat T nor oil FT predicted the seated hopper bridge; ae.hopper.dump is a new channel at 22.400 ms, 15.560 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=840): 14 min filter fire watch. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "14 min filter fire watch after the hopper-bridge dump. Safety head -0.64 "
                "prices the dump; task_progress stays +0.30 because the oil clamp completed "
                "under the 1520 C roof cap. World loss is named here, not subtracted from "
                "process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.throat.C (6.120 ms, 1548 C)"),
                        ("loser", "oil.feed.tph (6.308 ms, 4.2 t/h)"),
                        ("margin_us", 188),
                        (
                            "counterfactual_if_reversed",
                            "Feed-first by < 188 us inside the 400 us window would have kept "
                            "4.2 t/h; predicted next-sample 1552 C would have missed the 1520 "
                            "roof cap even without the hopper dump. The MODIFY is still the "
                            "correct process. The dump is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms hopper-bridge dump (tick t_us=22400), inside "
                "the 42 ms raster. The correct MODIFY at 6.840 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=840 fire-watch tick.",
            ),
        ]
    )
    spikes = [
        spike("enc.oil.ctx", 1.180, 0.41),
        spike("tc.throat.C", 2.440, 0.58),
        spike("oil.feed.tph", 3.880, 0.50),
        spike("tc.throat.C", 6.120, 1.31),
        spike("oil.feed.tph", 6.308, 1.12),
        spike("ctrl.gate", 6.840, 0.97),
        spike("tc.throat.C", 8.200, 0.82),
        spike("oil.feed.tph", 10.550, 0.64),
        spike("ctrl.gate", 14.100, 0.86),
        spike("ae.hopper.dump", 22.400, 1.48),
        spike("ae.hopper.dump", 24.200, 0.93),
        spike("enc.oil.ctx", 29.800, 0.40),
        spike("tc.throat.C", 36.200, 0.55),
    ]
    ras = raster_core(
        42,
        72,
        24,
        73,
        routing(
            "thalamic-relay.cb-throat",
            "spikenaut.policy.oil-clamp",
            [
                ("relay_throat_C", "policy_oil_clamp", 0.68),
                ("relay_oil_feed", "policy_feed_hold", 0.29),
                ("relay_ae_hop", "policy_oil_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at throat win (6.120 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.400 ms hopper dump",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("oil_clamp", 50, 0.50, 200.0, 4),
                    pop("feed_hold", 40, 0.80, 50.0, 1),
                    pop("hopper_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r43-231"),
            (
                "title",
                "Lampblack-Fen LF-4 / Reactor R-7: throat T beats oil feed by 188 us; correct "
                "MODIFY still eats an in-window hopper-bridge dump (partnered negative total -0.48)",
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
                    "42 ms raster. total -0.48 = 0.30 + -0.64 + -0.14 + 0.04 + -0.04. Named "
                    "filter fire watch (abort_s=840) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "carbon-black-reactor",
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
                    "14 min filter fire watch.",
                    1,
                ),
            ),
        ]
    )


def record_232():
    ticks = [
        tick(2210, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5480, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5662, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6020, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6400, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(540000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.mix.ctx", 1.050, 0.42),
        spike("ir.inlet.C", 2.210, 0.57),
        spike("enc.mix.timer", 3.400, 0.49),
        spike("ir.inlet.C", 5.480, 1.29),
        spike("enc.mix.timer", 5.662, 1.10),
        spike("ctrl.gate", 6.020, 0.96),
        spike("p.binder.pulse", 6.400, 1.18),
        spike("ir.inlet.C", 7.800, 0.80),
        spike("enc.mix.timer", 10.200, 0.63),
        spike("ctrl.gate", 13.500, 0.84),
        spike("enc.mix.ctx", 18.400, 0.41),
        spike("ir.inlet.C", 22.100, 0.54),
        spike("enc.mix.timer", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(43232, 96, 30000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Mixer M-7 at Tack-Drum TD-3 is already showing baghouse inlet 218 C against a "
                "190 C fabric cap, with 2.4 s still on the 45 s wet-mix timer. Damper-now should "
                "bind 40 -> 12 percent before the 6.400 ms binder pulse (latest_legal_clamp_us="
                "6400). A weak supervisor waits for mix-timer end and applies the same 12 percent "
                "damper at 9.200 ms, after the pulse has already overshot the bags.",
            ),
            ("domain", "asphalt-drum-mixer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold baghouse inlet <= 190 C on Mixer M-7 by clamping the exhaust damper at or "
                "before latest_legal_clamp_us=6400, before the next binder pulse.",
            ),
            ("t0_us", 1756850400000232),
            ("gate_latency_us", 540),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.4, 5.76]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.inlet.C 218 C on live baghouse inlet",
                                "enc.mix.timer 2.4 s remaining on wet-mix",
                            ],
                        ),
                        (
                            "semantics",
                            "Inlet-first should latch damper-now 40 -> 12 percent at t_gate; "
                            "timer-first is a false 'wait for mix-end' bind that delays the same "
                            "magnitude until 9.200 ms.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one baghouse-inlet IR slot versus the mix-timer encoder "
                            "publisher on this drum PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 182 us vs combined jitter 60 us (inlet 28 + timer 32). Order "
                            "is correctly inlet-first. The error is when the clamp is applied, "
                            "not which loop or what magnitude.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "baghouse-inlet IR pyrometer, 2 kHz, 28 us jitter",
                    "wet-mix timer encoder, 1 kHz, 32 us jitter",
                    "binder-pulse PT (context)",
                    "drum-tach PLC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("inlet_cap_C", 190.0),
                        ("observed_inlet_C", 218.0),
                        ("damper_pct", 40.0),
                        ("correct_damper_pct", 12.0),
                        ("latest_legal_clamp_us", 6400),
                        ("binder_pulse_us", 6400),
                        ("mix_remaining_s", 2.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. M-7 already in wet-mix; baghouse inlet 218 C; damper 40 percent.",
                    "2. Mix-timer 2.4 s remaining; not a mix-end story.",
                    "3. Encoder precursor at 1.050 ms.",
                    "4. Race window [5.400, 5.760] ms.",
                    "5. ir.inlet.C 218 C at 5.480 ms (winner).",
                    "6. enc.mix.timer 2.4 s at 5.662 ms (loser by 182 us).",
                    "7. Gate at 6.020 ms: WRONG-MODIFY schedules damper 12 percent at 9.200 ms.",
                    "8. Binder pulse at 6.400 ms hits bags while damper still 40 percent.",
                    "9. Late 12 percent clamp at 9.200 ms; fabric overshoot already done.",
                    "10. Delayed (abort_s=540): 9 min baghouse isolate while M-7 is purged.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_wet_mix_damper"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("damper_pct", 40.0),
                        ("clamp_t_us", 0),
                        ("inlet_C", 218.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("inlet_C", 218.0),
                        ("inlet_cap_C", 190.0),
                        ("damper_pct", 40.0),
                        ("correct_damper_pct", 12.0),
                        ("latest_legal_clamp_us", 6400),
                        ("t_gate_us", 6020),
                        ("mix_remaining_s", 2.4),
                        ("race_margin_us", 182),
                        ("combined_jitter_us", 60),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 40 percent damper: mix-timer 2.4 s remaining is "
                "treated as a still-wet drum, so the 218 C inlet is deferred to mix-end.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Inlet 218 C exceeds the 190 C fabric cap (true). At this pose the drum loop "
                "is still wet-mix (2.4 s remaining). Schedule damper 40 -> 12 percent after "
                "mix-timer end so the wet batch is not left in the drum; do not clamp now.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "inlet_C",
                            OrderedDict(
                                [
                                    ("cap", 190.0),
                                    ("observed", 218.0),
                                    ("executed_damper_pct", 12.0),
                                    ("executed_clamp_t_us", 9200),
                                    ("latest_legal_clamp_us", 6400),
                                ]
                            ),
                        ),
                        (
                            "timing",
                            OrderedDict(
                                [
                                    ("t_gate_us", 6020),
                                    ("latest_legal_clamp_us", 6400),
                                    ("executed_clamp_t_us", 9200),
                                    ("late_by_us", 2800),
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
            ("name", "damper_clamp_too_late"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("damper_pct", 12.0),
                        ("clamp_t_us", 9200),
                        ("latest_legal_clamp_us", 6400),
                        ("inlet_C", 218.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / clamp-too-late): damper magnitude 40 -> 12 percent is the "
                "right axis and size, applied at 9.200 ms after latest_legal_clamp_us=6400. "
                "Routing relay_inlet_T -> policy_delay_clamp; no positive weight to "
                "policy_now_clamp.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY applied the correct 12 percent damper after the 6.400 ms binder "
                "pulse. Inlet 218 C was over the 190 C floor at t_gate 6.020 ms, which was "
                "still inside latest_legal_clamp_us=6400. 9 min baghouse isolate (abort_s=540). "
                "Correct gate was MODIFY damper 40 -> 12 percent immediately at t_gate.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("inlet", "pulse overshoot at 6.400 ms; damper still 40 percent then"),
                        ("damper", "12 percent arrives at 9.200 ms, 2800 us late"),
                        ("bags", "9 min isolate, M-7 purge"),
                        ("mission", "wet-mix deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Inlet-first was the correct order and 12 percent was the correct magnitude; the MODIFY spent that win on a mix-timer delay.",
                    "Delayed (abort_s=540): TD-3 holds 9 min while M-7 is purged; next lot 11 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY damper 40 -> 12 percent immediately at t_gate_us=6020; leave mix-timer running.",
                        ),
                        ("correct_actuator", "exhaust_damper"),
                        ("wrong_timing", "clamp_t_us=9200 after latest_legal_clamp_us=6400"),
                        ("actual_latest_legal_us", 6400),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("damper_pct", 12.0),
                                    ("clamp_t_us", 9200),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "9 min baghouse isolate (task/efficiency); binder pulse at 6.400 ms hit fabric while damper still 40 percent (safety near-miss of a late-but-right-magnitude clamp).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.inlet.C (5.480 ms, 218 C)"),
                        ("loser", "enc.mix.timer (5.662 ms, 2.4 s remaining)"),
                        ("margin_us", 182),
                        (
                            "counterfactual_if_reversed",
                            "Timer-first by < 182 us would still leave 2.4 s on a legal wet-mix; "
                            "a correct gate binds ir.inlet.C to policy_now_clamp either way. The "
                            "wrong MODIFY spent the inlet win on a delayed mix-end clamp.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6020),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong MODIFY (6.020 ms, tick 4). "
                "The 9 min baghouse isolate is delayed surprise, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        30,
        96,
        32,
        92,
        routing(
            "thalamic-relay.drum-inlet",
            "spikenaut.policy.delay-clamp",
            [
                ("relay_inlet_T", "policy_delay_clamp", 0.72),
                ("relay_mix_timer", "policy_delay_clamp", 0.22),
            ],
            "acetylcholine",
            0.08,
            "late_cap_stdp; ACh tags the (wrong) delay_clamp bind at the inlet win",
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
            ("decision_window_ms", 0.36),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("delay_clamp", 42, 0.45, 280.0, 4),
                    pop("now_clamp", 42, 0.90),
                    pop("timer_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r43-232"),
            (
                "title",
                "WRONG-MODIFY at Tack-Drum TD-3 / Mixer M-7: inlet 218 C read correctly; "
                "12 percent damper applied after latest_legal_clamp_us (clamp-too-late)",
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
                    "Wrong-modify / clamp-too-late. Sidecar arithmetic 218 > 190 is true and "
                    "12 percent is the right magnitude; MODIFY bound after latest_legal_clamp_us. "
                    "total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "asphalt-drum-mixer",
                    [
                        "modify",
                        "wrong-gate",
                        "clamp-too-late",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct inlet-first race and a correct damper "
                    "magnitude can still be a wrong gate when the MODIFY is applied after "
                    "latest_legal_clamp_us. Convictable from timestamps without asphalt physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_233():
    ticks = [
        tick(2810, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(7040, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7218, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7900, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(8200, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(360000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("tc.chamber.ctx", 1.420, 0.43),
        spike("ig.chamber.nPa", 2.880, 0.61),
        spike("enc.gap.mm", 4.550, 0.49),
        spike("ig.chamber.nPa", 7.040, 1.34),
        spike("enc.gap.mm", 7.218, 1.11),
        spike("ctrl.gate", 7.900, 1.02),
        spike("ig.chamber.nPa", 10.200, 0.78),
        spike("tc.chamber.ctx", 14.800, 0.44),
        spike("enc.gap.mm", 19.400, 0.58),
        spike("ctrl.gate", 24.600, 0.81),
        spike("ig.chamber.nPa", 31.200, 0.53),
        spike("enc.gap.mm", 38.800, 0.46),
        spike("tc.chamber.ctx", 44.100, 0.37),
    ]
    excerpt = independent_excerpt(43233, 128, 48000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Undulator U-12 on the Gap-Orbit GO-HIL pad is armed for a 0.40 mm/s gap crawl "
                "while a chamber ion-gauge packet reads 48 nPa against a 12 nPa move cap. A "
                "gap encoder, lit by the pad lamp, still reads 8.2 mm under a 9.0 mm travel "
                "look. Vacuum-first latches REJECT hold; encoder-first would commit a 0.40 mm/s "
                "crawl on an under-read chamber.",
            ),
            ("domain", "beamline-undulator"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not crawl Undulator U-12 unless chamber pressure <= 12 nPa; keep gap motor "
                "0.0 mm/s until the injected vacuum recovers.",
            ),
            ("t0_us", 1756850400000233),
            ("gate_latency_us", 860),
            ("race_window_us", 290),
            ("race_window_rel_ms", [6.95, 7.24]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ig.chamber.nPa 48 nPa",
                                "enc.gap.mm 8.2 mm under 9.0",
                            ],
                        ),
                        (
                            "semantics",
                            "Vacuum-first latches REJECT hold 0.0 mm/s gap; encoder-first would "
                            "commit a 0.40 mm/s crawl on an apparent 8.2 mm under-read.",
                        ),
                        (
                            "window_derivation",
                            "290 us = one ion-gauge sample versus encoder integration on this "
                            "undulator HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 178 us vs combined jitter 56 us (IG 24 + ENC 32): 3.2x over a "
                            "2.0x trust floor. Pad injects the encoder lamp 120-160 us before the "
                            "gauge (geometric lag, not a sensor fault); the 8.2 mm packet is still "
                            "the loser in this 290 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "chamber ion gauge, 5 kHz burst, 24 us jitter",
                    "gap linear encoder, 200 Hz, 32 us jitter",
                    "chamber thermocouple (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("vac_cap_nPa", 12.0),
                        ("observed_vac_nPa", 48.0),
                        ("gap_mm", 8.2),
                        ("gap_look_mm", 9.0),
                        ("proposed_crawl_mm_s", 0.40),
                        ("lamp_inject_lead_us", [120, 160]),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("pad", "Gap-Orbit GO-HIL undulator mockup with physical gap motor"),
                        ("injected", "chamber vacuum burst + encoder lamp spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop beamline undulator. Invented plant; not a live storage-ring sector.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Undulator U-12 on the GO-HIL pad; 0.40 mm/s crawl armed.",
                    "2. Encoder lamp injected 120-160 us before IG sees 48 nPa.",
                    "3. Chamber-TC precursor at 1.420 ms.",
                    "4. Race window [6.950, 7.240] ms.",
                    "5. ig.chamber.nPa 48 nPa at 7.040 ms (winner).",
                    "6. enc.gap.mm 8.2 mm at 7.218 ms (loser by 178 us).",
                    "7. Gate at 7.900 ms: REJECT hold 0.0 mm/s; do not crawl 0.40.",
                    "8. Chamber remains over 12 nPa this cycle; crawl cap held.",
                    "9. Bake recycle queued on the pad.",
                    "10. Delayed (abort_s=360): 6 min chamber re-bake and lamp-spectrum retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "crawl_undulator_gap"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("gap_mm_s", 0.40),
                        ("hold", False),
                        ("encoder_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("vac_nPa", 48.0),
                        ("vac_cap_nPa", 12.0),
                        ("gap_mm", 8.2),
                        ("gap_look_mm", 9.0),
                        ("race_margin_us", 178),
                        ("combined_jitter_us", 56),
                        ("abort_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 0.40 mm/s gap crawl because encoder 8.2 mm looks under the "
                "9.0 mm travel look, treating chamber 48 nPa as a noisy bus echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Chamber 48 nPa is over the 12 nPa gap-move cap. Encoder 8.2 mm is a HIL lamp "
                "under-read, not a clearance. REJECT: hold 0.0 mm/s; do not commit a 0.40 mm/s "
                "crawl.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "vac_nPa",
                            OrderedDict(
                                [
                                    ("cap", 12.0),
                                    ("observed", 48.0),
                                    ("gap_mm", 8.2),
                                ]
                            ),
                        ),
                        (
                            "gap_mm_s",
                            OrderedDict([("proposed", 0.40), ("executed", 0.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 178),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 3.18),
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
            ("name", "hold_for_vac_drop"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("gap_mm_s", 0.0),
                        ("hold", True),
                        ("encoder_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0.0 mm/s; 0.40 mm/s crawl cancelled. Vacuum 48 > 12 nPa cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Undulator U-12 at 0.0 mm/s gap. Chamber over cap this "
                "cycle; crawl cap held. Encoder apparent was not treated as a vacuum clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("gap", "held; 0.0 mm/s"),
                        ("vacuum", "still over 12 nPa this cycle"),
                        ("encoder", "8.2 mm unused as clearance"),
                        ("mission", "crawl deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: encoder lamp was injected 120-160 us before the ion gauge, yet vacuum still won the 290 us race.",
                    "Delayed (abort_s=360): pad policy update forbids treating gap encoder mm as a chamber-vacuum substitute after a 6 min re-bake.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ig.chamber.nPa (7.040 ms, 48 nPa)"),
                        ("loser", "enc.gap.mm (7.218 ms, 8.2 mm)"),
                        ("margin_us", 178),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 178 us inside the 290 us window would have committed "
                            "a 0.40 mm/s crawl with vacuum 48 > 12 nPa cap. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7900),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (7.900 ms, tick 4) as the hold "
                "lands. The 6 min re-bake is delayed surprise bound to abort_s=360.",
            ),
        ]
    )
    ras = raster_core(
        48,
        128,
        18,
        111,
        routing(
            "thalamic-relay.undulator-vac",
            "spikenaut.policy.gap-hold",
            [
                ("relay_ig_nPa", "policy_gap_hold", 0.70),
                ("relay_enc_gap", "policy_enc_crawl", 0.24),
            ],
            "dopamine",
            0.15,
            "vac_hold_stdp; DA tags the gap_hold bind at the ion-gauge win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 360),
                ("delayed_surprise_s", 360),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.29),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("gap_hold", 70, 0.48, 250.0, 5),
                    pop("enc_crawl", 50, 0.85),
                    pop("vac_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r43-233"),
            (
                "title",
                "Gap-Orbit GO-HIL / Undulator U-12: chamber 48 nPa beats gap encoder 8.2 mm by "
                "178 us; correct REJECT holds the gap crawl",
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
                    "Correct REJECT. Vacuum over cap beats encoder under-read. "
                    "total 0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06. Tick 6 binds abort_s=360.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "beamline-undulator",
                    [
                        "reject",
                        "hil",
                        "chamber-vac",
                        "encoder-underread",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a HIL encoder under-read losing a 178 us race does not clear a "
                    "chamber-vacuum over-pressure. Hold is distillable from nPa vs cap.",
                    3,
                ),
            ),
        ]
    )


def record_234():
    ticks = [
        tick(3220, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(8120, 0.08, 0.05, 0.04, 0.03, 0.02),
        tick(8310, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(8520, 0.12, 0.09, 0.05, 0.04, 0.02),
        tick(8980, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(120000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.line.ctx", 1.105, 0.43),
        spike("tc.bath.C", 3.220, 0.59),
        spike("ir.dross.C", 5.010, 0.50),
        spike("tc.bath.C", 8.120, 1.27),
        spike("ir.dross.C", 8.310, 1.09),
        spike("ctrl.gate", 8.520, 0.97),
        spike("tc.bath.C", 11.200, 0.78),
        spike("ir.dross.C", 14.880, 0.61),
        spike("ctrl.gate", 18.400, 0.84),
        spike("tc.bath.C", 22.050, 0.56),
        spike("enc.line.ctx", 24.100, 0.40),
    ]
    excerpt = independent_excerpt(43234, 52, 26000, 13, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("line_m_min", 1.4),
            ("bath_C", 455.0),
            ("dross_C", 612.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Pot P-2 in Spelter-Weir SW-5 holds a 455 C zinc bath under a 480 C pot cap "
                "with a 1.4 m/min strip already filed under the 1.8 m/min wipe ceiling. "
                "Dross-first would extra-clamp a legal line; bath-first ACCEPTS the filed "
                "1.4 m/min pass.",
            ),
            ("domain", "hot-dip-galvanize"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold the 1.4 m/min strip pass while bath stays <= 480 C and line stays <= "
                "1.8 m/min; do not extra-clamp a legal coating.",
            ),
            ("t0_us", 1756850400000234),
            ("gate_latency_us", 400),
            ("race_window_us", 460),
            ("race_window_rel_ms", [8.0, 8.46]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.bath.C 455 C under 480",
                                "ir.dross.C 612 C smear over 480 look",
                            ],
                        ),
                        (
                            "semantics",
                            "Bath-first ACCEPTS the already-legal 1.4 m/min pass. Dross-first would "
                            "extra-clamp because 612 C looks over a 480 C pot look.",
                        ),
                        (
                            "window_derivation",
                            "460 us = one bath-TC slot versus dross-IR group delay on this "
                            "galvanize-pot skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 190 us vs combined jitter 66 us (TC 32 + IR 34): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 190 us inside the 460 us "
                            "window would have extra-clamped a legal 455 C / 1.4 m/min pass.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "pot-bath thermocouple tree, 1 kHz, 32 us jitter",
                    "dross-surface IR pyrometer, 2 kHz, 34 us jitter",
                    "strip-speed encoder (context)",
                    "air-knife PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("pot_cap_C", 480.0),
                        ("observed_bath_C", 455.0),
                        ("dross_C", 612.0),
                        ("line_cap_m_min", 1.8),
                        ("proposed_line_m_min", 1.4),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "species-transport + free-surface FEM, seed 43234; 28 m zinc pot, "
                            "bath TC map; NOT lumped-capacity, NOT U-RANS, NOT a wet-stand",
                        ),
                        (
                            "fidelity_limits",
                            "Rigid pot shell; no dross-island motion. Raster is kernelized events, "
                            "not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Pot P-2 in coat; 1.4 m/min pass armed.",
                    "2. Bath 455 C under 480 C pot; line 1.4 under 1.8 m/min wipe.",
                    "3. Encoder precursor at 1.105 ms.",
                    "4. Race window [8.000, 8.460] ms.",
                    "5. tc.bath.C 455 C at 8.120 ms (winner).",
                    "6. ir.dross.C 612 C at 8.310 ms (loser by 190 us).",
                    "7. Gate at 8.520 ms: ACCEPT 1.4 m/min; executed identical to proposed.",
                    "8. Bath stays 455.4 C < 480; line 1.41 m/min < 1.8.",
                    "9. Dross remaining a surface glint did not require an extra clamp.",
                    "10. Delayed (survey_s=120): 120 s coupon-weight sample on pass 3.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_strip_pass"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bath_C", 455.0),
                        ("pot_cap_C", 480.0),
                        ("dross_C", 612.0),
                        ("line_cap_m_min", 1.8),
                        ("race_margin_us", 190),
                        ("combined_jitter_us", 66),
                        ("survey_s", 120),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 1.4 m/min pass: bath 455 C is under the "
                "480 C pot cap and 1.4 m/min is under 1.8 m/min wipe.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bath 455 C won by 190 us and is under the 480 C pot cap. Dross 612 C is a "
                "surface glint, not a pot over-temp. ACCEPT the filed 1.4 m/min pass. Executed "
                "identical to proposed. An extra clamp is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bath_C",
                            OrderedDict(
                                [
                                    ("cap", 480.0),
                                    ("observed", 455.0),
                                    ("executed_line_m_min", 1.4),
                                ]
                            ),
                        ),
                        (
                            "dross_C",
                            OrderedDict([("look", 480.0), ("observed", 612.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 190),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 2.88),
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
            ("name", "hold_strip_pass"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 1.4 m/min pass. Bath 455 C < 480 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 1.4 m/min strip pass. Bath stayed 455.4 C "
                "under 480 C. Dross remaining a surface glint was the losing channel and did "
                "not justify an extra clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("line", "held; 1.4 m/min"),
                        ("bath", "455.4 C < 480 C"),
                        ("dross", "612 C glint unused as pot over-temp"),
                        ("coils", "galvanize pass continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Dross IR 612 C losing a 190 us race did not predict a pot over-temp; reversing 190 us would have extra-clamped a legal 455 C pass.",
                    "Delayed (survey_s=120): 120 s coupon-weight sample on pass 3; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bath.C (8.120 ms, 455 C)"),
                        ("loser", "ir.dross.C (8.310 ms, 612 C)"),
                        ("margin_us", 190),
                        (
                            "counterfactual_if_reversed",
                            "Dross-first by < 190 us inside the 460 us window would have extra-clamped "
                            "a legal strip pass. Bath-first confirms the filed line speed.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 8520),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (8.520 ms, tick 4). The 120 s coupon-weight sample "
                "is delayed surprise bound to survey_s=120, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        26,
        52,
        44,
        59,
        routing(
            "thalamic-relay.zinc-bath",
            "spikenaut.policy.line-accept",
            [
                ("relay_bath_C", "policy_line_accept", 0.66),
                ("relay_dross_IR", "policy_extra_clamp", 0.23),
            ],
            "serotonin",
            0.12,
            "pot_confirm_stdp; 5-HT tags the line_accept bind at the bath-TC win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 120),
                ("delayed_surprise_s", 120),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.46),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("line_accept", 50, 0.50, 175.0, 4),
                    pop("extra_clamp", 40, 0.85, 40.0, 1),
                    pop("dross_veto", 22, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r43-234"),
            (
                "title",
                "Spelter-Weir SW-5 / Pot P-2: bath 455 C beats dross IR 612 C by 190 us; "
                "ACCEPT already-legal 1.4 m/min galvanize pass",
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
                    "Clean ACCEPT of an already-legal galvanize pass. "
                    "total 1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08. Tick 6 t_us binds survey_s=120.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "hot-dip-galvanize",
                    [
                        "accept",
                        "simulated",
                        "bath-vs-dross",
                        "zinc-pot",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging dross IR losing a 190 us race does not require an "
                    "extra clamp when bath TC already shows pot-cap margin.",
                    4,
                ),
            ),
        ]
    )


def record_235():
    ticks = [
        tick(2140, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(4960, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(5140, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5480, 0.14, 0.10, 0.06, 0.04, 0.02),
        tick(5900, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(240000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.face.ctx", 0.880, 0.40),
        spike("ndir.ch4.pct", 2.040, 0.56),
        spike("enc.afc.m_min", 3.120, 0.47),
        spike("ndir.ch4.pct", 4.960, 1.26),
        spike("enc.afc.m_min", 5.140, 1.08),
        spike("ctrl.gate", 5.480, 0.99),
        spike("ndir.ch4.pct", 7.200, 0.76),
        spike("enc.afc.m_min", 9.880, 0.55),
        spike("ctrl.gate", 13.100, 0.82),
        spike("enc.face.ctx", 16.400, 0.43),
        spike("ndir.ch4.pct", 19.200, 0.50),
    ]
    excerpt = independent_excerpt(43235, 84, 22000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("shear_m_min", 8.0),
            ("ch4_pct", 0.42),
            ("afc_m_min", 12.4),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Drum D-19 at Cleat-Face CF-8 is shearing at 8.0 m/min with NDIR CH4 at 0.42 "
                "percent LEL, 0.58 under the 1.00 percent trip. AFC 12.4 m/min is residual "
                "conveyor haul under a 16.0 m/min cap. Methane-first ACCEPTS the filed shear; "
                "haul-first would wait for a 16.0 m/min face that is not packing.",
            ),
            ("domain", "longwall-shearer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 8.0 m/min shear on Drum D-19 while CH4 stays <= 1.00 percent LEL and AFC "
                "stays <= 16.0 m/min; do not abort on residual conveyor haul.",
            ),
            ("t0_us", 1756850400000235),
            ("gate_latency_us", 520),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.85, 5.17]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ndir.ch4.pct 0.42 under 1.00",
                                "enc.afc.m_min 12.4 under 16.0",
                            ],
                        ),
                        (
                            "semantics",
                            "Methane-first ACCEPTS the 8.0 m/min shear (already under 1.00 percent "
                            "LEL). Haul-first would wait for a phantom 16.0 m/min pack.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one NDIR methane slot versus AFC encoder group delay on "
                            "this longwall shearer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (NDIR 26 + AFC 32): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have stalled a legal 0.42 percent shear.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "face NDIR methane cell, 2 kHz, 26 us jitter",
                    "AFC haul encoder, 1 kHz, 32 us jitter",
                    "drum-pick load cell (context)",
                    "chock-pressure PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ch4_trip_pct", 1.00),
                        ("observed_ch4_pct", 0.42),
                        ("afc_m_min", 12.4),
                        ("afc_cap_m_min", 16.0),
                        ("proposed_shear_m_min", 8.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Drum D-19 indexed on the face; 0.42 percent CH4; 8.0 m/min armed.",
                    "2. AFC 12.4 m/min under 16.0 m/min haul cap.",
                    "3. Encoder precursor at 0.880 ms.",
                    "4. Race window [4.850, 5.170] ms.",
                    "5. ndir.ch4.pct 0.42 at 4.960 ms (winner).",
                    "6. enc.afc.m_min 12.4 at 5.140 ms (loser by 180 us).",
                    "7. Gate at 5.480 ms: ACCEPT 8.0 m/min; executed identical to proposed.",
                    "8. CH4 peak 0.44 percent < 1.00; AFC stays 12.4 m/min.",
                    "9. AFC remaining under haul did not require a wait.",
                    "10. Delayed (survey_s=240): 4 min ventilation-curtain check on the next gate.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_legal_shear"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ch4_pct", 0.42),
                        ("ch4_trip_pct", 1.00),
                        ("afc_m_min", 12.4),
                        ("afc_cap_m_min", 16.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 8.0 m/min shear: 0.42 percent CH4 is under 1.00 percent LEL "
                "and AFC 12.4 m/min is under 16.0 m/min.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "CH4 0.42 percent won by 180 us and is under the 1.00 percent LEL trip. AFC "
                "12.4 m/min is not a pack problem. ACCEPT the filed 8.0 m/min shear. Executed "
                "identical to proposed. A wait for a 16.0 m/min haul is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ch4_pct",
                            OrderedDict(
                                [
                                    ("cap", 1.00),
                                    ("observed", 0.42),
                                    ("executed_shear_m_min", 8.0),
                                ]
                            ),
                        ),
                        (
                            "afc_m_min",
                            OrderedDict([("cap", 16.0), ("observed", 12.4)]),
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
            ("name", "hold_legal_shear"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 8.0 m/min shear. CH4 0.42 percent < 1.00 trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 8.0 m/min shear. CH4 peaked 0.44 percent under "
                "1.00 percent LEL. AFC remaining under haul was the losing channel and did not "
                "justify a wait.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("shear", "8.0 m/min executed"),
                        ("ch4", "peak 0.44 percent < 1.00 trip"),
                        ("afc", "12.4 m/min < 16.0 cap"),
                        ("face", "web continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "AFC 12.4 m/min losing a 180 us race did not predict a pack; reversing 180 us would have stalled a legal 0.42 percent shear.",
                    "Delayed (survey_s=240): 4 min ventilation-curtain check on the next gate; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ndir.ch4.pct (4.960 ms, 0.42 percent LEL)"),
                        ("loser", "enc.afc.m_min (5.140 ms, 12.4 m/min)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Haul-first by < 180 us inside the 320 us window would have waited "
                            "for a phantom 16.0 m/min pack. Methane-first confirms the filed shear.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5480),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (5.480 ms, tick 4). The 4 min curtain check is delayed "
                "surprise bound to survey_s=240, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        22,
        84,
        26,
        48,
        routing(
            "thalamic-relay.face-ch4",
            "spikenaut.policy.shear-accept",
            [
                ("relay_ch4_pct", "policy_shear_accept", 0.69),
                ("relay_afc_enc", "policy_haul_wait", 0.21),
            ],
            "octopamine",
            0.05,
            "ch4_confirm_stdp; octopamine tags the shear_accept bind at the NDIR win",
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
            ("decision_window_ms", 0.32),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("shear_accept", 45, 0.50, 210.0, 3),
                    pop("haul_wait", 40, 0.85, 40.0, 1),
                    pop("ch4_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r43-235"),
            (
                "title",
                "Cleat-Face CF-8 / Drum D-19: CH4 0.42 percent LEL beats AFC 12.4 m/min by 180 us; "
                "ACCEPT already-legal 8.0 m/min shear",
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
                    "Clean ACCEPT of an already-legal longwall shear. "
                    "total 1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08. Tick 6 binds survey_s=240.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "longwall-shearer",
                    [
                        "accept",
                        "designed",
                        "ch4-vs-afc",
                        "shear-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging AFC encoder losing a 180 us race does not require a "
                    "wait when face methane is already under the LEL trip.",
                    5,
                ),
            ),
        ]
    )
