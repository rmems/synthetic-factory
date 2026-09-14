def record_336():
    excerpt, extra = lif_336_excerpt()
    ticks = [
        tick(2140, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6140, 0.07, -0.04, -0.03, 0.01, -0.01),
        tick(6348, 0.05, -0.03, -0.02, 0.00, 0.00),
        tick(6960, 0.08, -0.06, -0.03, 0.02, -0.01),
        tick(22600, 0.04, -0.40, -0.04, -0.01, -0.02),
        tick(840000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "TSL-R2 at Matte-Lynchet ML-3 is already blowing 8400 Nm3/h oxygen into a 1424 C "
                "matte bath against a 1380 C refractory-skin cap. A bath-first latch clamps the "
                "lance; a feed-first story would keep the 8400 Nm3/h cruise. Stored splash strain "
                "in the brick is not yet an observable of either race channel.",
            ),
            ("domain", "isasmelt-furnace"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the ML-3 TSL pass, keep bath temperature <= 1380 C, and leave the "
                "magnesia brick unmarked.",
            ),
            ("t0_us", 1756850400000336),
            ("gate_latency_us", 820),
            ("race_window_us", 400),
            ("race_window_rel_ms", [6.10, 6.50]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bath.C 1424 C pulse",
                                "ft.o2.nm3h 8400 Nm3/h cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Bath-first latches oxygen 8400 -> 5100 Nm3/h; feed-first keeps "
                            "cruise on a still-cooling brick model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one 2 kHz bath-RTD sample minus lance-orifice group "
                            "delay on this TSL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 208 us vs combined jitter ~64 us (bath 30 + oxygen 34): 3.2x over "
                            "a 2.0x trust floor. Reversing order by < 208 us inside the 400 us window "
                            "would have kept 8400 Nm3/h cruise; predicted next-sample 1392 C > 1380 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bath dip RTD, 2 kHz, 30 us timestamp jitter",
                    "lance-oxygen FT, 1 kHz, 34 us jitter",
                    "refractory AE puck (context until the splash)",
                    "offgas SO2 analyzer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bath_cap_C", 1380.0),
                        ("observed_bath_C", 1424.0),
                        ("proposed_o2_nm3h", 8400.0),
                        ("matte_feed_tph", 48.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. TSL-R2 indexed on Matte-Lynchet ML-3; lance armed at 8400 Nm3/h.",
                    "2. Cruise 8400 Nm3/h; bath 1424 C against 1380 C refractory-skin cap.",
                    "3. Oxygen precursor at 1.140 ms; bath warm-start 1424 C.",
                    "4. Race window [6.100, 6.500] ms opens on the TSL bus.",
                    "5. rtd.bath.C 1424 C at 6.140 ms (winner).",
                    "6. ft.o2.nm3h 8400 Nm3/h at 6.348 ms (loser by 208 us).",
                    "7. Gate at 6.960 ms (winner + 820 us): MODIFY clamp 8400 -> 5100 Nm3/h.",
                    "8. Clamp executes; next-sample bath 1366 C < 1380 cap.",
                    "9. At 22.600 ms stored strain still splashes an 18 mm brick face; AE burst.",
                    "10. Furnace isolate 14 min (abort_s=840); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_o2_8400"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("o2_nm3h", 8400.0),
                        ("matte_feed_tph", 48.0),
                        ("lance_immersion_mm", 420.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bath_C", 1424.0),
                        ("bath_cap_C", 1380.0),
                        ("predicted_unclamped_next_C", 1392.0),
                        ("o2_nm3h", 8400.0),
                        ("race_margin_us", 208),
                        ("combined_jitter_us", 64),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 8400 Nm3/h cruise: 1424 C looks like an offgas-SO2 spike, not "
                "brick contact, and R2 volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bath 1424 C won by 208 us, so the brick is loading heat, not still cooling. "
                "Holding 8400 Nm3/h predicts next-sample 1392 C > 1380 cap. MODIFY: oxygen 8400 -> "
                "5100 Nm3/h. Observed after clamp 1366 C < 1380. A full REJECT is not indicated: a "
                "sound TSL pass accepts 5100 Nm3/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bath_C",
                            OrderedDict(
                                [
                                    ("cap", 1380.0),
                                    ("observed", 1424.0),
                                    ("predicted_unclamped_next", 1392.0),
                                    ("clamped_o2_nm3h", 5100.0),
                                    ("observed_after_clamp", 1366.0),
                                ]
                            ),
                        ),
                        (
                            "o2_nm3h",
                            OrderedDict([("proposed", 8400.0), ("clamped", 5100.0)]),
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
            ("name", "clamped_o2_5100"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("o2_nm3h", 5100.0),
                        ("matte_feed_tph", 48.0),
                        ("lance_immersion_mm", 420.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: oxygen 8400 -> 5100 Nm3/h. Process-correct vs the 1380 C refractory-skin "
                "cap. Brick splash still occurs at 22.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held bath at 1366 C. At 22.600 ms stored strain "
                "in the magnesia brick still splashed an 18 mm face. Clamp reduced dump energy; "
                "it did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("oxygen", "clamp executed; peak 1366 C < 1380"),
                        ("brick", "18 mm splash at 22.600 ms"),
                        ("repair", "14 min furnace isolate (abort_s=840)"),
                        ("mission", "ML-3 TSL pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither bath RTD nor oxygen FT predicted the splash charge; ae.refr.splash is a new channel at 22.600 ms, 15.640 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=840): 14 min furnace isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "14 min furnace isolate after an 18 mm magnesia-brick splash. Safety head -0.60 "
                "prices the split; task_progress stays +0.30 because the lance clamp completed "
                "under the 1380 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bath.C (6.140 ms, 1424 C)"),
                        ("loser", "ft.o2.nm3h (6.348 ms, 8400 Nm3/h)"),
                        ("margin_us", 208),
                        (
                            "counterfactual_if_reversed",
                            "Feed-first by < 208 us inside the 400 us window would have kept "
                            "8400 Nm3/h cruise; predicted next-sample 1392 C would have exceeded "
                            "the 1380 cap even without the splash charge. The MODIFY is still the "
                            "correct process. The splash is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22600),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.600 ms refractory splash (tick t_us=22600), inside "
                "the 42 ms raster. The correct MODIFY at 6.960 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=840 isolate tick.",
            ),
            ("delayed_surprise_s", 840.0),
            ("abort_s", 840),
        ]
    )
    spikes = [
        spike("enc.o2.ctx", 1.140, 0.42),
        spike("rtd.bath.C", 2.140, 0.61),
        spike("ft.o2.nm3h", 3.620, 0.50),
        spike("rtd.bath.C", 6.140, 1.32),
        spike("ft.o2.nm3h", 6.348, 1.14),
        spike("ctrl.gate", 6.960, 0.98),
        spike("rtd.bath.C", 8.420, 0.80),
        spike("ft.o2.nm3h", 11.200, 0.62),
        spike("ctrl.gate", 14.880, 0.84),
        spike("ae.refr.splash", 22.600, 1.46),
        spike("ae.refr.splash", 24.410, 0.91),
        spike("enc.o2.ctx", 31.200, 0.41),
        spike("rtd.bath.C", 38.100, 0.53),
    ]
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.bath-lining",
            "spikenaut.policy.o2-clamp",
            [
                ("relay.rtd.bath", "policy.o2_clamp", 0.66),
                ("relay.ft.o2", "policy.o2_hold", 0.30),
                ("relay.ae.splash", "policy.o2_clamp", -0.45),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at bath win (6.140 ms) opens a 50 ms "
            "eligibility trace that still covers the 22.600 ms refractory splash",
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
                    pop("o2_clamp", 40, 0.50, 250.0, 4),
                    pop("o2_hold", 40, 0.50, 62.5, 1),
                    pop("bath_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r64-336",
        "Matte-Lynchet ML-3 / TSL-R2: bath 1424 C beats oxygen-feed by 208 us; correct "
        "MODIFY still eats an in-window refractory splash (partnered negative total -0.47)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "42 ms raster. total -0.47 = 0.30 + -0.60 + -0.16 + 0.04 + -0.05. Named furnace "
        "isolate (abort_s=840) is not netted into task_progress.",
        ras,
        gate,
        "isasmelt-furnace",
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
        "14 min furnace isolate.",
        1,
    )


def record_337():
    ticks = [
        tick(1680, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(4260, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(4418, -0.03, -0.01, -0.03, -0.02, 0.01),
        tick(4960, -0.07, -0.04, -0.09, -0.05, 0.02),
        tick(6820, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(1080000000, -0.02, -0.01, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("dp.feed.ctx", 0.840, 0.40),
        spike("live.pt.bar", 1.680, 0.58),
        spike("ma.loop.fwd", 2.440, 0.51),
        spike("live.pt.bar", 4.260, 1.32),
        spike("ma.loop.fwd", 4.418, 1.15),
        spike("ctrl.gate", 4.960, 1.00),
        spike("live.pt.bar", 6.820, 0.74),
        spike("ma.loop.fwd", 8.200, 0.61),
        spike("ctrl.gate", 12.100, 0.82),
        spike("dp.feed.ctx", 16.400, 0.42),
        spike("live.pt.bar", 20.800, 0.53),
        spike("ma.loop.fwd", 23.400, 0.47),
    ]
    excerpt = independent_excerpt(52277, 92, 24000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Cleavage-C5 on Cumox-Pike CP-2 is holding phenol-acetone feed at 22.0 t/h with live "
                "kettle 3.20 bar against a 6.50 bar trip. The 4-20 mA loop is reverse-scaled "
                "(20 mA = 0 bar, 4 mA = 10.00 bar). Reverse-first should ACCEPT the feed; a weak "
                "supervisor that binds the forward map of 14.88 mA as 6.80 bar will REJECT a legal kettle.",
            ),
            ("domain", "phenol-acetone-cleavage"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep 22.0 t/h feed on C5 while live kettle stays <= 6.50 bar; do not spend a "
                "forward-scaled 4-20 mA shadow on the hold.",
            ),
            ("t0_us", 1756850400000337),
            ("gate_latency_us", 700),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.20, 4.52]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "live.pt.bar 3.20 bar reverse-scaled live",
                                "ma.loop.fwd 14.88 mA forward-shadow 6.80 bar",
                            ],
                        ),
                        (
                            "semantics",
                            "Reverse-first should ACCEPT 22.0 t/h (3.20 bar < 6.50 bar trip). "
                            "Forward-first tempts a weak supervisor to treat 14.88 mA as 6.80 bar.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one kettle-PT sample minus 4-20 mA transmitter group delay "
                            "on this cleavage bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 158 us vs combined jitter ~56 us (live 24 + mA 32): 2.8x over "
                            "a 2.0x trust floor. Order is correctly reverse-first. The error is binding "
                            "the forward 4-20 map, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "kettle gauge PT reverse-scaled 4-20 mA, 4 kHz, 24 us jitter",
                    "raw loop mA sibling, 4 kHz, 32 us jitter, scale_dir=reverse",
                    "feed differential pressure (context)",
                    "cumene FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("kettle_trip_bar", 6.50),
                        ("live_bar", 3.20),
                        ("ma_mA", 14.88),
                        ("forward_shadow_bar", 6.80),
                        ("span_bar", 10.00),
                        ("proposed_feed_tph", 22.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Cleavage-C5 latched on Cumox-Pike CP-2; feed 22.0 t/h armed.",
                    "2. Live kettle 3.20 bar; raw loop prints 14.88 mA (forward shadow 6.80 bar).",
                    "3. Feed-dp precursor at 0.840 ms.",
                    "4. Race window [4.200, 4.520] ms.",
                    "5. live.pt.bar 3.20 bar at 4.260 ms (winner).",
                    "6. ma.loop.fwd 14.88 mA at 4.418 ms (loser by 158 us).",
                    "7. Gate at 4.960 ms: REJECT hold 0.0 t/h (incorrect).",
                    "8. Legal feed cancelled; live kettle still 3.20 bar < 6.50 bar trip.",
                    "9. Reverse 4-20 map remains the published live; forward map is the shadow.",
                    "10. Delayed missed_window_s=1080 (18 min phenol-quality window) while the kettle waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "feed_22"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 22.0),
                        ("hold", False),
                        ("scale_dir", "reverse"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_bar", 3.20),
                        ("kettle_trip_bar", 6.50),
                        ("ma_mA", 14.88),
                        ("forward_shadow_bar", 6.80),
                        ("reverse_bar", 3.20),
                        ("span_bar", 10.00),
                        ("scale_dir", "reverse"),
                        ("pv_live", True),
                        ("proposed_feed_tph", 22.0),
                        ("race_margin_us", 158),
                        ("combined_jitter_us", 56),
                        ("missed_window_s", 1080),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 22.0 t/h feed because live kettle 3.20 bar is under the "
                "6.50 bar trip; 14.88 mA is a reverse-scaled loop (20 mA = 0 bar), not 6.80 bar live.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Forward map of 14.88 mA is 6.80 bar, over the 6.50 bar trip once the supervisor "
                "treats the reverse loop as forward. REJECT: hold feed 0.0 t/h until the tag "
                "recovers under 6.50 so the kettle does not see an over-pressure event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "kettle_bar",
                            OrderedDict(
                                [
                                    ("published_live_trip", 6.50),
                                    ("observed_live", 3.20),
                                    ("ma_mA", 14.88),
                                    ("misbound_forward_bar", 6.80),
                                    ("scale_dir", "reverse"),
                                    ("executed_feed_tph", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 158),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 2.82),
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
            ("name", "feed_hold_forward_as_live"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 0.0),
                        ("hold", True),
                        ("scale_dir", "forward"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): feed 22.0 -> 0.0 t/h. Routing relay.ma.fwd -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live 3.20 bar never "
                "violated the 6.50 bar trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze C5 at 0.0 t/h while live kettle stayed 3.20 bar under the "
                "6.50 bar trip. 18 min phenol-quality window missed. Correct gate was ACCEPT of "
                "the already-legal 22.0 t/h feed.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held at 0.0 t/h; 22.0 t/h abandoned"),
                        ("live_bar", "still 3.20 bar, under 6.50 bar published trip"),
                        ("loop", "18 min phenol-quality window missed"),
                        ("mA", "14.88 mA reverse-scale false positive, not a live over-trip"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 6.80 bar reading is a forward map of a reverse 4-20 loop, not a published live over-trip.",
                    "Delayed (missed_window_s=1080): sister cleavage C6 ran the same 22.0 t/h quality window after QA rebound the reverse scale; C5's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live 3.20 bar < published 6.50 bar trip; leave 22.0 t/h.",
                        ),
                        ("correct_trip_bar", 6.50),
                        ("wrong_forward_bar", 6.80),
                        ("scale_dir", "reverse"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("feed_tph", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "18 min missed phenol-quality window (task/efficiency); live kettle never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "live.pt.bar (4.260 ms, 3.20 bar reverse)"),
                        ("loser", "ma.loop.fwd (4.418 ms, 14.88 mA / 6.80 bar forward)"),
                        ("margin_us", 158),
                        (
                            "counterfactual_if_reversed",
                            "Forward-first by < 158 us would still show live 3.20 bar < 6.50 bar. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the reverse-scale "
                            "win on a forward 4-20 shadow.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4960),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (4.960 ms, tick 4). The 18 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 1080.0),
            ("missed_window_s", 1080),
        ]
    )
    ras = raster_core(
        24,
        92,
        34,
        75,
        routing(
            "relay.ma.fwd",
            "policy.hold_reject",
            [
                ("relay.ma.fwd", "policy.hold_reject", 0.74),
                ("relay.live.pt", "policy.hold_reject", 0.20),
            ],
            "acetylcholine",
            0.06,
            "reverse_scale_stdp; ACh tags the (wrong) hold_reject bind at the forward 4-20 shadow",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("missed_window_s", 1080),
                ("delayed_surprise_s", 1080),
                ("scale_dir", "reverse"),
                ("forward_shadow_bar", 6.80),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 48, 0.50, 260.4, 4),
                    pop("go_accept", 48, 0.80, 6.5, 0),
                    pop("ma_ctx", 32, 0.55, 97.7, 1),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r64-337",
        "WRONG-REJECT at Cumox-Pike CP-2 / Cleavage-C5: live kettle 3.20 bar < 6.50 bar trip; "
        "supervisor bound a reverse 4-20 mA loop as a forward 6.80 bar over-trip",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 3.20 < 6.50 on reverse-scaled bar is true; clamp bound "
        "to a 6.80 bar forward shadow. total -0.58 = -0.20 + -0.10 + -0.22 + -0.12 + 0.06.",
        ras,
        gate,
        "phenol-acetone-cleavage",
        [
            "reject",
            "wrong-gate",
            "reverse-scale-4-20",
            "inverted-transmitter",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live<trip reverse-scale read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed.",
        2,
        supervisor_error_type="wrong-reject",
    )


def record_338():
    ticks = [
        tick(2480, 0.01, 0.05, 0.01, 0.01, 0.01),
        tick(5720, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5894, 0.02, 0.07, 0.02, 0.02, 0.01),
        tick(6560, 0.03, 0.12, 0.04, 0.03, 0.02),
        tick(8840, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(540000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("ir.bead.ctx", 1.280, 0.43),
        spike("ae.weld.pps", 2.480, 0.62),
        spike("ir.bead.C", 4.020, 0.49),
        spike("ae.weld.pps", 5.720, 1.35),
        spike("ir.bead.C", 5.894, 1.12),
        spike("ctrl.gate", 6.560, 1.03),
        spike("ae.weld.pps", 8.840, 0.77),
        spike("ir.bead.ctx", 13.100, 0.44),
        spike("ir.bead.C", 17.200, 0.58),
        spike("ctrl.gate", 22.400, 0.81),
        spike("ae.weld.pps", 28.600, 0.50),
        spike("ir.bead.C", 34.800, 0.46),
        spike("ae.weld.ctx", 38.200, 0.40),
    ]
    excerpt = independent_excerpt(52278, 108, 40000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Mill-M6 on Skelp-Fen SF-HIL is armed for a 48 m/min ERW pass while weld AE sits "
                "at 52 pps against a 14 pps crack floor. A bead pyrometer, lit by the pad lamp "
                "spectrum, still reports 980 C under a 1180 C HAZ cap. AE-first holds the mill; "
                "bead-first would commit 48 m/min into a seam split.",
            ),
            ("domain", "erw-pipe-mill"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Run M6 only if weld AE stays <= 14 pps; otherwise hold so a cracked seam is "
                "not loaded at 48 m/min.",
            ),
            ("t0_us", 1756850400000338),
            ("gate_latency_us", 840),
            ("race_window_us", 400),
            ("race_window_rel_ms", [5.68, 6.08]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.weld.pps 52 pps seam crack",
                                "ir.bead.C 980 C pad-lamp glint",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches mill hold 48 -> 0 m/min; bead-first would commit "
                            "48 m/min on a still-legal 980 C HAZ-cap story.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one weld-AE slot versus bead-IR decode on this HIL mill bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 174 us vs combined jitter ~62 us (AE 28 + IR 34): 2.8x over "
                            "a 2.0x trust floor. Reversing order by < 174 us inside the 400 us "
                            "window would have committed 48 m/min into a 52 pps seam crack.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "weld AE puck, 5 kHz, 28 us jitter",
                    "bead IR camera, 200 Hz, 34 us jitter",
                    "line-speed encoder (context)",
                    "impeder-current CT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_crack_floor_pps", 14.0),
                        ("observed_ae_pps", 52.0),
                        ("haz_cap_C", 1180.0),
                        ("observed_bead_C", 980.0),
                        ("proposed_speed_m_min", 48.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Mill-M6 indexed on Skelp-Fen SF-HIL; line 48 m/min armed.",
                    "2. Bead IR 980 C under 1180 C HAZ cap; weld AE already 52 pps.",
                    "3. Bead-context precursor at 1.280 ms.",
                    "4. Race window [5.680, 6.080] ms.",
                    "5. ae.weld.pps 52 pps at 5.720 ms (winner).",
                    "6. ir.bead.C 980 C at 5.894 ms (loser by 174 us).",
                    "7. Gate at 6.560 ms: REJECT hold mill 0 m/min.",
                    "8. Pass cancelled; seam crack not loaded.",
                    "9. HIL pad lamp spectrum remains the bead glint source.",
                    "10. Delayed (abort_s=540): 9 min coil re-thread before the next pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "erw_48"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_min", 48.0),
                        ("hold", False),
                        ("mill", "M6"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 52.0),
                        ("ae_crack_floor_pps", 14.0),
                        ("bead_C", 980.0),
                        ("haz_cap_C", 1180.0),
                        ("race_margin_us", 174),
                        ("combined_jitter_us", 62),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 48 m/min because bead 980 C is under the 1180 C HAZ "
                "cap and treats the AE puck as skelp noise.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Weld AE 52 pps won by 174 us, so the seam is cracking, not still quiet. "
                "52 pps > 14 pps floor. REJECT: hold mill 48 -> 0 m/min. Bead 980 C < 1180 C "
                "does not license the pass once AE is over floor.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "weld_ae_pps",
                            OrderedDict(
                                [
                                    ("floor", 14.0),
                                    ("observed", 52.0),
                                    ("executed_speed_m_min", 0.0),
                                ]
                            ),
                        ),
                        (
                            "bead_C",
                            OrderedDict(
                                [
                                    ("cap", 1180.0),
                                    ("observed", 980.0),
                                    ("does_not_license_pass", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 174),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 2.81),
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
            ("name", "mill_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_min", 0.0),
                        ("hold", True),
                        ("mill", "M6"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (correct): mill 48 -> 0 m/min. Routing relay.ae.weld -> "
                "policy.seam_hold. Seam crack is not loaded.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held M6 at 0 m/min. AE 52 pps beat bead 980 C; seam "
                "was already over the 14 pps crack floor. 9 min re-thread follows (abort_s=540).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("mill", "held at 0 m/min; 48 m/min abandoned"),
                        ("seam", "52 pps crack not loaded"),
                        ("bead", "980 C still under 1180 C HAZ cap"),
                        ("coil", "9 min re-thread queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Bead IR 980 C was a HIL pad-lamp glint, not a HAZ-cap exceedance.",
                    "Delayed (abort_s=540): 9 min coil re-thread before the next pass on SF-HIL.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.weld.pps (5.720 ms, 52 pps)"),
                        ("loser", "ir.bead.C (5.894 ms, 980 C)"),
                        ("margin_us", 174),
                        (
                            "counterfactual_if_reversed",
                            "Bead-first by < 174 us would have committed 48 m/min into a seam "
                            "already at 52 pps. The REJECT is still the correct process; AE is the "
                            "licensing channel, not bead IR.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6560),
            (
                "reward_inflection_note",
                "Safety and task credit the correct REJECT at 6.560 ms (tick 4). The 9 min "
                "re-thread is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 540.0),
            ("abort_s", 540),
        ]
    )
    ras = raster_core(
        40,
        108,
        21,
        91,
        routing(
            "thalamic-relay.weld-ae",
            "spikenaut.policy.mill-hold",
            [
                ("relay.ae.weld", "policy.seam_hold", 0.68),
                ("relay.ir.bead", "policy.seam_commit", 0.28),
                ("relay.ae.weld", "policy.seam_hold", 0.12),
            ],
            "dopamine",
            0.07,
            "ae_floor_stdp; DA at weld win (5.720 ms) opens a 70 ms eligibility trace",
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
            ("decision_window_ms", 0.40),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("seam_hold", 52, 0.50, 240.4, 5),
                    pop("seam_commit", 52, 0.50, 48.1, 1),
                    pop("ae_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r64-338",
        "Skelp-Fen SF-HIL / Mill-M6: weld AE 52 pps beats bead 980 C; correct "
        "REJECT holds the ERW pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 52 pps > 14 pps floor beats a legal bead IR. "
        "total +0.78 = 0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "erw-pipe-mill",
        ["reject", "hil", "weld-ae", "erw", "correct-gate"],
        "Teaches a weld-AE vs bead-glint race on a HIL ERW mill: the crack floor, not the "
        "HAZ cap, licenses the pass.",
        3,
    )


def record_339():
    ticks = [
        tick(1620, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(3840, 0.09, 0.07, 0.04, 0.03, 0.02),
        tick(3962, 0.07, 0.06, 0.03, 0.02, 0.01),
        tick(4380, 0.12, 0.10, 0.05, 0.03, 0.02),
        tick(6240, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(300000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.pulp.ctx", 0.920, 0.41),
        spike("do.opt.ppm", 1.620, 0.58),
        spike("do.bubble.ppm", 2.880, 0.47),
        spike("do.opt.ppm", 3.840, 1.28),
        spike("do.bubble.ppm", 3.962, 1.10),
        spike("ctrl.gate", 4.380, 0.97),
        spike("do.opt.ppm", 6.240, 0.72),
        spike("enc.pulp.ctx", 9.800, 0.44),
        spike("do.bubble.ppm", 13.400, 0.55),
        spike("ctrl.gate", 17.200, 0.80),
        spike("do.opt.ppm", 20.100, 0.49),
        spike("enc.pulp.ctx", 21.600, 0.38),
    ]
    excerpt = independent_excerpt(52279, 80, 22000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Tank-T11 of Leach-Croft LC-7 is already at 6.4 ppm dissolved oxygen while a "
                "bubble-fouled probe still reports 2.1 ppm against a 3.0 ppm floor the optical "
                "DO has not crossed. Optical-first should ACCEPT 16 t/h pulp; bubble-first would "
                "invent a hold on an already-legal CIL pass.",
            ),
            ("domain", "gold-cil-tank"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Run LC-7 at 16 t/h while optical DO stays >= 3.0 ppm; do not spend a bubble-"
                "fouled probe on the tank hold.",
            ),
            ("t0_us", 1756850400000339),
            ("gate_latency_us", 540),
            ("race_window_us", 280),
            ("race_window_rel_ms", [3.80, 4.08]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "do.opt.ppm 6.4 ppm live",
                                "do.bubble.ppm 2.1 ppm fouled probe",
                            ],
                        ),
                        (
                            "semantics",
                            "Optical-first should ACCEPT 16 t/h (6.4 ppm > 3.0 ppm floor). "
                            "Bubble-first would hold on a simulated probe foul.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one optical-DO sample versus Clark-probe decode on this "
                            "CIL-tank bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 122 us vs combined jitter ~48 us (optical 22 + bubble 26): 2.5x over "
                            "a 2.0x trust floor. Reversing order by < 122 us inside the 280 us "
                            "window would have invented a hold on an already-legal 6.4 ppm tank.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "optical DO, 4 kHz, 22 us jitter",
                    "Clark bubble probe, 200 Hz, 26 us jitter",
                    "pulp-density meter (context)",
                    "free-cyanide analyzer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("do_floor_ppm", 3.0),
                        ("observed_do_ppm", 6.4),
                        ("bubble_ppm", 2.1),
                        ("proposed_pulp_tph", 16.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Tank-T11 indexed on Leach-Croft LC-7; pulp 16 t/h armed.",
                    "2. Optical DO 6.4 ppm; bubble probe 2.1 ppm under 3.0 ppm floor.",
                    "3. Pulp-encoder precursor at 0.920 ms.",
                    "4. Race window [3.800, 4.080] ms.",
                    "5. do.opt.ppm 6.4 ppm at 3.840 ms (winner).",
                    "6. do.bubble.ppm 2.1 ppm at 3.962 ms (loser by 122 us).",
                    "7. Gate at 4.380 ms: ACCEPT leave 16 t/h.",
                    "8. Optical remains 6.4 ppm > 3.0 ppm; bubble unused as a hold.",
                    "9. Simulated probe foul remains the Clark source.",
                    "10. Delayed (survey_hold_s=300): 5 min gold-in-solution survey after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cil_16"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pulp_tph", 16.0),
                        ("hold", False),
                        ("cn_ppm", 180.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("do_ppm", 6.4),
                        ("do_floor_ppm", 3.0),
                        ("bubble_ppm", 2.1),
                        ("proposed_pulp_tph", 16.0),
                        ("race_margin_us", 122),
                        ("combined_jitter_us", 48),
                        ("survey_hold_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 16 t/h because optical DO 6.4 ppm is over the 3.0 ppm floor; "
                "2.1 ppm is a bubble-fouled Clark probe, not a tank oxygen.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Optical 6.4 ppm won by 122 us and sits 3.4 ppm over the 3.0 ppm floor. Bubble "
                "2.1 ppm is a fouled Clark probe, not a tank reading. ACCEPT: leave 16 t/h. A "
                "hold would idle a legal CIL pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "do_ppm",
                            OrderedDict(
                                [
                                    ("floor", 3.0),
                                    ("observed", 6.4),
                                    ("executed_pulp_tph", 16.0),
                                ]
                            ),
                        ),
                        (
                            "bubble_ppm",
                            OrderedDict(
                                [
                                    ("observed", 2.1),
                                    ("not_a_tank_reading", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 122),
                                    ("combined_jitter_us", 48),
                                    ("ratio", 2.54),
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
            ("name", "cil_16"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pulp_tph", 16.0),
                        ("hold", False),
                        ("cn_ppm", 180.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 16 t/h. Routing relay.do.opt -> policy.cil_go. "
                "Bubble probe unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left LC-7 at 16 t/h. Optical 6.4 ppm beat bubble 2.1 ppm; "
                "the 3.0 ppm floor was never crossed. 5 min gold-in-solution survey follows "
                "(survey_hold_s=300).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("pulp", "16 t/h held as proposed"),
                        ("do", "6.4 ppm > 3.0 ppm floor"),
                        ("bubble", "2.1 ppm foul unused"),
                        ("survey", "5 min gold-in-solution survey queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Clark 2.1 ppm was a simulated bubble foul, not a tank under-floor.",
                    "Delayed (survey_hold_s=300): 5 min gold-in-solution survey after the pass on LC-7.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "do.opt.ppm (3.840 ms, 6.4 ppm)"),
                        ("loser", "do.bubble.ppm (3.962 ms, 2.1 ppm)"),
                        ("margin_us", 122),
                        (
                            "counterfactual_if_reversed",
                            "Bubble-first by < 122 us would still be a fouled probe under the "
                            "3.0 ppm floor; a correct gate ACCEPTs either way. Reversing would only "
                            "have delayed confirmation of the same legal tank.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4380),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 4.380 ms (tick 4). The 5 min "
                "survey is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 300.0),
            ("survey_hold_s", 300),
        ]
    )
    ras = raster_core(
        22,
        80,
        34,
        60,
        routing(
            "thalamic-relay.opt-do",
            "spikenaut.policy.cil-go",
            [
                ("relay.do.opt", "policy.cil_go", 0.70),
                ("relay.do.bubble", "policy.foul_hold", 0.22),
                ("relay.do.opt", "policy.cil_go", 0.10),
            ],
            "serotonin",
            0.04,
            "already_legal_stdp; 5-HT at optical win (3.840 ms) tags the go bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_hold_s", 300),
                ("delayed_surprise_s", 300),
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
                    pop("cil_go", 40, 0.50, 267.9, 3),
                    pop("foul_hold", 40, 0.80, 8.9, 0),
                    pop("do_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r64-339",
        "Leach-Croft LC-7 / Tank-T11: optical DO 6.4 ppm beats bubble-fouled probe; correct ACCEPT "
        "of an already-legal 16 t/h (total +1.16)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Optical 6.4 ppm > 3.0 ppm floor; bubble probe unused. "
        "total +1.16 = 0.44 + 0.34 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "gold-cil-tank",
        ["accept", "simulated-foul", "do-vs-bubble", "cil", "simulated"],
        "Teaches that a bubble-fouled Clark probe can lose to a legal optical DO inside a "
        "280 us window; reversing 122 us would have invented a hold on an already-legal tank.",
        4,
    )


def record_340():
    ticks = [
        tick(1960, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(5120, 0.09, 0.06, 0.04, 0.03, 0.02),
        tick(5286, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(5740, 0.12, 0.09, 0.06, 0.03, 0.02),
        tick(8120, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.mono.ctx", 1.080, 0.42),
        spike("rtd.kettle.C", 1.960, 0.59),
        spike("rtd.jacket.C", 3.440, 0.48),
        spike("rtd.kettle.C", 5.120, 1.30),
        spike("rtd.jacket.C", 5.286, 1.11),
        spike("ctrl.gate", 5.740, 0.99),
        spike("rtd.kettle.C", 8.120, 0.74),
        spike("rtd.jacket.C", 11.600, 0.56),
        spike("ctrl.gate", 15.400, 0.82),
        spike("ft.mono.ctx", 19.200, 0.43),
        spike("rtd.kettle.C", 22.800, 0.51),
        spike("rtd.jacket.C", 23.700, 0.40),
    ]
    excerpt = independent_excerpt(52280, 56, 24000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Kettle-K3 at Butyl-Mear BM-4 is polymerizing at 12.0 t/h with kettle -96 C "
                "against a -88 C ceiling. Jacket RTD sits at -102 C under a -80 C jacket floor. "
                "Kettle-first should ACCEPT the 12.0 t/h already-legal set; jacket-first would only "
                "delay confirmation of the same legal slurry.",
            ),
            ("domain", "butyl-rubber-reactor"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 12.0 t/h on K3 while kettle stays <= -88 C and jacket <= -80 C.",
            ),
            ("t0_us", 1756850400000340),
            ("gate_latency_us", 620),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.08, 5.44]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.kettle.C -96 C slurry",
                                "rtd.jacket.C -102 C ethylene",
                            ],
                        ),
                        (
                            "semantics",
                            "Kettle-first should ACCEPT 12.0 t/h (-96 C < -88 C ceiling). "
                            "Jacket-first would only delay confirmation of the same legal slurry.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one kettle-RTD slot versus jacket-RTD group delay on this "
                            "butyl bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 166 us vs combined jitter ~58 us (kettle 26 + jacket 32): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 166 us inside the 360 us "
                            "window would still show both channels under ceiling; ACCEPT either way.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "kettle slurry RTD, 2 kHz, 26 us jitter",
                    "ethylene-jacket RTD, 1 kHz, 32 us jitter",
                    "kettle PT (context)",
                    "isobutene FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("kettle_ceiling_C", -88.0),
                        ("observed_kettle_C", -96.0),
                        ("jacket_floor_C", -80.0),
                        ("observed_jacket_C", -102.0),
                        ("proposed_tph", 12.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Kettle-K3 indexed on Butyl-Mear BM-4; slurry 12.0 t/h armed.",
                    "2. Kettle -96 C; jacket -102 C under -80 C jacket floor.",
                    "3. Monomer-FT precursor at 1.080 ms.",
                    "4. Race window [5.080, 5.440] ms.",
                    "5. rtd.kettle.C -96 C at 5.120 ms (winner).",
                    "6. rtd.jacket.C -102 C at 5.286 ms (loser by 166 us).",
                    "7. Gate at 5.740 ms: ACCEPT leave 12.0 t/h.",
                    "8. Kettle remains -96 C < -88 C; jacket unused as a hold.",
                    "9. Isobutene sendout continues.",
                    "10. Delayed (dwell_s=360): 6 min Mooney-survey dwell after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "butyl_12"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 12.0),
                        ("hold", False),
                        ("isobutene_tph", 9.4),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("kettle_C", -96.0),
                        ("kettle_ceiling_C", -88.0),
                        ("jacket_C", -102.0),
                        ("jacket_floor_C", -80.0),
                        ("proposed_tph", 12.0),
                        ("race_margin_us", 166),
                        ("combined_jitter_us", 58),
                        ("dwell_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 12.0 t/h because kettle -96 C is under the -88 C ceiling "
                "and jacket -102 C is under the -80 C jacket floor.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Kettle -96 C won by 166 us and sits under the -88 C ceiling. Jacket -102 C "
                "is under -80 C. ACCEPT: leave 12.0 t/h. A hold would idle a legal butyl slurry.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "kettle_C",
                            OrderedDict(
                                [
                                    ("ceiling", -88.0),
                                    ("observed", -96.0),
                                    ("executed_tph", 12.0),
                                ]
                            ),
                        ),
                        (
                            "jacket_C",
                            OrderedDict(
                                [
                                    ("floor", -80.0),
                                    ("observed", -102.0),
                                    ("under_floor", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 166),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 2.86),
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
            ("name", "butyl_12"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 12.0),
                        ("hold", False),
                        ("isobutene_tph", 9.4),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 12.0 t/h. Routing relay.rtd.kettle -> policy.butyl_go. "
                "Jacket unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left K3 at 12.0 t/h. Kettle -96 C beat jacket -102 C; both "
                "ceilings held. 6 min Mooney-survey dwell follows (dwell_s=360).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("slurry", "12.0 t/h held as proposed"),
                        ("kettle", "-96 C < -88 C ceiling"),
                        ("jacket", "-102 C < -80 C floor"),
                        ("survey", "6 min Mooney-survey dwell queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Jacket -102 C was never a trip; it only lost the race to a legal kettle RTD.",
                    "Delayed (dwell_s=360): 6 min Mooney-survey dwell after the pass on BM-4.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.kettle.C (5.120 ms, -96 C)"),
                        ("loser", "rtd.jacket.C (5.286 ms, -102 C)"),
                        ("margin_us", 166),
                        (
                            "counterfactual_if_reversed",
                            "Jacket-first by < 166 us would still be under -80 C; a correct gate "
                            "ACCEPTs either way. Reversing would only have delayed confirmation of "
                            "the same legal slurry.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5740),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 5.740 ms (tick 4). The 6 min "
                "dwell is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 360.0),
            ("dwell_s", 360),
        ]
    )
    ras = raster_core(
        24,
        56,
        40,
        54,
        routing(
            "thalamic-relay.kettle-rtd",
            "spikenaut.policy.butyl-go",
            [
                ("relay.rtd.kettle", "policy.butyl_go", 0.69),
                ("relay.rtd.jacket", "policy.jack_hold", 0.24),
                ("relay.rtd.kettle", "policy.butyl_go", 0.11),
            ],
            "adenosine",
            0.08,
            "already_legal_stdp; adenosine at kettle win (5.120 ms) tags the go bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("dwell_s", 360),
                ("delayed_surprise_s", 360),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("butyl_go", 36, 0.50, 231.5, 3),
                    pop("jack_hold", 36, 0.80, 7.7, 0),
                    pop("temp_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r64-340",
        "Butyl-Mear BM-4 / Kettle-K3: kettle -96 C beats jacket -102 C; correct ACCEPT "
        "of an already-legal 12.0 t/h (total +1.14)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Kettle -96 C < -88 C ceiling; jacket unused. "
        "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
        ras,
        gate,
        "butyl-rubber-reactor",
        ["accept", "designed", "kettle-vs-jacket", "already-legal", "butyl"],
        "Teaches an already-legal butyl slurry: both kettle and jacket sit under ceiling; "
        "race order only confirms the ACCEPT.",
        5,
    )
