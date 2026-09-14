def record_366():
    ticks = [
        tick(2176, -0.02, 0.01, -0.02, -0.01, 0.01),
        tick(5440, -0.04, 0.01, -0.04, -0.02, 0.01),
        tick(5680, -0.03, 0.01, -0.03, -0.01, 0.01),
        tick(6200, -0.06, 0.02, -0.08, -0.03, 0.02),
        tick(6620, -0.02, 0.01, -0.03, -0.01, 0.01),
        tick(780000000, -0.01, 0.00, -0.02, 0.00, 0.00),
    ]
    spikes = [
        spike("enc.nbz.ctx", 1.160, 0.43),
        spike("ft.h2.lin", 2.480, 0.62),
        spike("dp.orifice.raw", 3.720, 0.51),
        spike("bus.hydr.ctx", 4.540, 0.46),
        spike("ft.h2.lin", 5.440, 1.32),
        spike("dp.orifice.raw", 5.680, 1.16),
        spike("ctrl.gate", 6.200, 0.99),
        spike("ft.h2.lin", 7.440, 0.83),
        spike("dp.orifice.raw", 9.620, 0.64),
        spike("ctrl.gate", 15.100, 0.86),
        spike("enc.nbz.ctx", 19.200, 0.40),
        spike("ft.h2.lin", 25.400, 0.57),
    ]
    excerpt = independent_excerpt(70366, 76, 28000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Hydrogenator HY-4 at Aniline-Carlin already holds a linearized hydrogen flow of "
                "4.20 t/h when that analog sample races a leftover raw orifice Delta-P still "
                "published on a sibling tag. Published cap is 5.50 t/h on the sqrt-extracted flow; "
                "a weak supervisor treats the unextracted 6.80 kPa DP as if it were t/h and zeros "
                "a legal 4.20 t/h nitrobenzene feed.",
            ),
            ("domain", "aniline-hydrogenator"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 4.20 t/h on HY-4, keep linearized H2 flow < 5.50 t/h cap, and finish the "
                "13 min aniline window.",
            ),
            ("t0_us", 1762300000000366),
            ("gate_latency_us", 760),
            ("race_window_us", 420),
            ("race_window_rel_ms", [5.440, 5.860]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.h2.lin 4.20 t/h linearized hydrogen",
                                "dp.orifice.raw 6.80 kPa leftover unextracted DP",
                            ],
                        ),
                        (
                            "semantics",
                            "Linearized-first should ACCEPT 4.20 t/h (4.20 < 5.50 t/h cap). "
                            "Raw-DP-first would only delay confirmation of the same legal flow.",
                        ),
                        (
                            "window_derivation",
                            "420 us = one hydrogen-flow analog slot versus the leftover-raw-DP "
                            "publisher on this 2 kHz hydrogenation bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 240 us vs combined jitter 72 us (linear 32 + raw-DP 40): 3.3x over "
                            "a 2.0x trust floor. Order is correctly linearized-first. The error is binding "
                            "unextracted DP as if it were the live flow EU, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "H2 linearized flow, 2 kHz, 32 us jitter, axis hydr_h2_t_h, sqrt_extracted true",
                    "orifice raw DP, 1 kHz, 40 us jitter, leftover unextracted kPa",
                    "nitrobenzene-mass encoder (context)",
                    "bed RTD (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("live_flow_t_h", 4.20),
                        ("flow_cap_t_h", 5.50),
                        ("raw_dp_kPa", 6.80),
                        ("sqrt_extracted", True),
                        ("raw_dp_as_flow", True),
                        ("analog_fresh", True),
                        ("heartbeat_age_ms", 18.0),
                        ("max_age_ms", 200.0),
                        ("proposed_t_h", 4.20),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Hydrogenator HY-4 indexed on Aniline-Carlin; linearized H2 4.20 t/h, nitrobenzene 4.20 t/h armed.",
                    "2. Published flow cap 5.50 t/h; raw orifice DP tagged leftover unextracted kPa.",
                    "3. Encoder precursor at 1.160 ms.",
                    "4. Race window [5.440, 5.860] ms.",
                    "5. Linearized H2 4.20 t/h at 5.440 ms (winner).",
                    "6. Leftover raw DP 6.80 kPa at 5.680 ms (loser by 240 us).",
                    "7. Gate at 6.200 ms: wrong REJECT holds 0 t/h on the raw DP as flow.",
                    "8. Feed idle; linearized flow never crossed 5.50 t/h.",
                    "9. 13 min aniline window missed.",
                    "10. QA: correct gate was ACCEPT; leave 4.20 t/h; bind linearized 4.20 vs 5.50 t/h cap.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hydr_4p2_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 4.20),
                        ("h2_t_h", 4.20),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_flow_t_h", 4.20),
                        ("flow_cap_t_h", 5.50),
                        ("raw_dp_kPa", 6.80),
                        ("sqrt_extracted", True),
                        ("raw_dp_as_flow", True),
                        ("analog_fresh", True),
                        ("heartbeat_age_ms", 18.0),
                        ("ft_axis", "hydr_h2_t_h"),
                        ("race_margin_us", 240),
                        ("combined_jitter_us", 72),
                        ("t_gate_us", 6200),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.20 t/h because linearized H2 4.20 t/h is 1.30 t/h under the "
                "published 5.50 t/h cap and the 6.80 kPa raw DP is leftover unextracted orifice, not a flow EU.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Raw orifice DP prints 6.80, so the flow is treated as 6.80 t/h over the 5.50 t/h "
                "cap (true vs that leftover unextracted tag). REJECT: hold 0 t/h until the raw DP "
                "falls so the hydrogenator does not see an over-flow event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "hydr_h2_t_h",
                            OrderedDict(
                                [
                                    ("published_flow_cap", 5.50),
                                    ("observed_linearized", 4.20),
                                    ("raw_dp_as_flow_applied", True),
                                    ("raw_dp_kPa", 6.80),
                                    ("executed_t_h", 0.0),
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
            ("name", "hydr_hold_raw_dp"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 0.0),
                        ("h2_t_h", 4.20),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): feed 4.20 -> 0 t/h. Routing relay.dp.raw -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Linearized 4.20 t/h never "
                "violated the 5.50 t/h cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze HY-4 at 0 t/h while linearized H2 stayed 4.20 t/h under the "
                "5.50 t/h cap. 13 min aniline window missed. Correct gate was ACCEPT of the "
                "already-legal 4.20 t/h command.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("hydrogenator", "held at 0 t/h; 4.20 t/h abandoned"),
                        ("h2_t_h", "still 4.20 t/h, under 5.50 t/h published cap"),
                        ("aniline", "13 min hydrogenation window missed"),
                        ("flag", "no over-flow; leftover raw-DP false positive"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 6.80 kPa tag is leftover unextracted orifice DP, not a live linearized flow EU.",
                    "Delayed (13 min): sister hydrogenator HY-5 ran the same 4.20 t/h aniline window after QA rebound the linearized cap; HY-4's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: linearized 4.20 t/h < published 5.50 t/h cap; leave 4.20 t/h; ignore leftover raw DP.",
                        ),
                        ("correct_cap_t_h", 5.50),
                        ("wrong_flag", True),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("feed_t_h", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "13 min missed aniline window (task/efficiency); linearized never over cap (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.h2.lin (5.440 ms, 4.20 t/h)"),
                        ("loser", "dp.orifice.raw (5.680 ms, leftover unextracted 6.80 kPa)"),
                        ("margin_us", 240),
                        (
                            "counterfactual_if_reversed",
                            "Raw-DP-first by < 240 us would still show linearized 4.20 t/h < 5.50. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the linearized win "
                            "on leftover unextracted DP.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6200),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (6.200 ms, tick 4). The 13 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 780.0),
            ("missed_window_s", 780),
        ]
    )
    ras = raster_core(
        28,
        76,
        32,
        68,
        routing(
            "relay.dp.raw",
            "policy.hold_reject",
            [
                ("relay.dp.raw", "policy.hold_reject", 0.72),
                ("relay.ft.h2", "policy.hold_reject", 0.21),
            ],
            "acetylcholine",
            0.08,
            "raw_dp_as_flow_stdp; ACh tags the (wrong) hold_reject bind at the linearized win",
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
                    pop("hold_reject", 48, 0.50, 200.0, 4),
                    pop("go_accept", 48, 0.80, 10.0, 0),
                    pop("flow_cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r70-366",
        "WRONG-REJECT at Aniline-Carlin / HY-4: linearized H2 4.20 t/h is legal vs "
        "published 5.50 t/h cap; supervisor bound leftover unextracted orifice DP as the flow EU",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 4.20 < 5.50 is true; clamp bound to leftover "
        "unextracted DP. total -0.36 = -0.18 + 0.06 + -0.22 + -0.08 + 0.06.",
        ras,
        gate,
        "aniline-hydrogenator",
        [
            "reject",
            "wrong-gate",
            "raw-DP-as-flow",
            "sqrt-unextracted",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct linearized<cap read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed.",
        1,
        supervisor_error_type="wrong-reject",
    )


def record_367():
    excerpt, extra = lif_367_excerpt()
    ticks = [
        tick(1912, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(4780, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(5020, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5700, 0.10, -0.06, -0.03, 0.02, -0.01),
        tick(22400, 0.05, -0.42, -0.04, 0.00, -0.02),
        tick(960000000, 0.02, -0.05, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Switch condenser SC-8 at Phthalic-Soke is already pulling 18 t/h hot oil when a "
                "return-temperature pulse arrives 240 us before the oil-flow encoder that still "
                "reads a legal melt. Temperature-first latches a process clamp under the "
                "240 C cap; flow-first would keep cruise oil. Stored switch-tube freeze-plug load is "
                "not yet an observable of either race channel.",
            ),
            ("domain", "phthalic-switch-condenser"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep SC-8 on 18 t/h hot oil only while return temperature stays <= 240 C, and "
                "leave the switch-tube freeze plug un-ruptured.",
            ),
            ("t0_us", 1762300000000367),
            ("gate_latency_us", 920),
            ("race_window_us", 400),
            ("race_window_rel_ms", [4.780, 5.180]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.oil.ret 248 C hot-oil return",
                                "ft.oil.t_h 18 t/h still-legal melt flow",
                            ],
                        ),
                        (
                            "semantics",
                            "Temperature-first latches oil clamp 18 -> 12 t/h; flow-first keeps "
                            "cruise oil on a 'tube still open' model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one oil-return RTD slot minus flow-encoder group delay on this "
                            "1 kHz switch-condenser bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 240 us vs combined jitter 70 us (RTD 32 + flow 38): 3.4x over "
                            "a 2.0x trust floor. Reversing order by < 240 us inside the 400 us window "
                            "would have kept 18 t/h cruise; predicted next-sample return 244 C > 240 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "hot-oil return RTD, 1 kHz, 32 us timestamp jitter",
                    "oil-flow encoder, 1 kHz, 38 us jitter",
                    "switch-valve encoder (context)",
                    "tube-plug AE (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ret_cap_C", 240.0),
                        ("observed_ret_C", 248.0),
                        ("proposed_oil_t_h", 18.0),
                        ("oil_floor_t_h", 8.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Switch condenser SC-8 indexed; 18 t/h hot oil; return 248 C > 240 cap.",
                    "2. Cruise oil 18 t/h armed; return over the 240 C cap.",
                    "3. Encoder precursor at 1.120 ms; oil-side warm-start 248 C.",
                    "4. Race window [4.780, 5.180] ms opens on the switch bus.",
                    "5. Return RTD 248 C at 4.780 ms (winner).",
                    "6. Oil flow 18 t/h at 5.020 ms (loser by 240 us).",
                    "7. Gate at 5.700 ms (winner + 920 us): MODIFY clamp 18 -> 12 t/h.",
                    "8. Clamp executes; next-sample return 236 C < 240 cap.",
                    "9. At 22.400 ms stored freeze-plug load ruptures a switch tube.",
                    "10. Emergency isolate 16 min + tube pull; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_oil_melt"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("oil_t_h", 18.0),
                        ("ret_C", 248.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ret_C", 248.0),
                        ("ret_cap_C", 240.0),
                        ("predicted_unclamped_next_C", 244.0),
                        ("oil_t_h", 18.0),
                        ("race_margin_us", 240),
                        ("combined_jitter_us", 70),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18 t/h cruise: oil flow looks like an open switch tube, not a "
                "frozen plug, and the 240 C return cap is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Return 248 C won by 240 us, so the switch is running packed, not still "
                "free. Holding 18 t/h predicts next-sample 244 C > 240 C cap. MODIFY: oil "
                "18 -> 12 t/h. Observed after clamp 236 C < 240. A full REJECT is not "
                "indicated: a sound switch accepts 12 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "oil_ret_C",
                            OrderedDict(
                                [
                                    ("cap", 240.0),
                                    ("observed", 248.0),
                                    ("predicted_unclamped_next", 244.0),
                                    ("clamped_oil_t_h", 12.0),
                                    ("observed_after_clamp", 236.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 240),
                                    ("combined_jitter_us", 70),
                                    ("ratio", 3.43),
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
            ("name", "clamped_oil_melt"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("oil_t_h", 12.0),
                        ("ret_C", 236.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: oil 18 -> 12 t/h. Process-correct vs the 240 C return cap. Switch-tube "
                "freeze-plug rupture still occurs at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held return at 236 C. At 22.400 ms stored freeze-plug load "
                "ruptured a switch tube. Clamp reduced oil energy; it did not dump the plug charge. "
                "Partnered negative: process heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("oil", "clamp executed; return 236 C < 240"),
                        ("switch_tube", "freeze-plug rupture at 22.400 ms"),
                        ("repair", "16 min emergency isolate + tube pull"),
                        ("mission", "condenser still switching; plug precursor controlled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither return RTD nor oil flow predicted the plug charge; ae.plug.pack is a new channel at 22.400 ms, 16.700 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (16 min): emergency isolate and tube pull close the rupture. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "16 min emergency isolate + tube pull after a switch-tube freeze-plug rupture. Safety "
                "head -0.62 prices the precursor; task_progress stays +0.34 because the oil clamp "
                "completed under the 240 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.oil.ret (4.780 ms, 248 C)"),
                        ("loser", "ft.oil.t_h (5.020 ms, 18 t/h)"),
                        ("margin_us", 240),
                        (
                            "counterfactual_if_reversed",
                            "Flow-first by < 240 us inside the 400 us window would have kept "
                            "18 t/h cruise; predicted next-sample 244 C would have exceeded the "
                            "240 C cap even without the plug charge. The MODIFY is still the "
                            "correct process. The rupture is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms switch-tube freeze-plug rupture (tick t_us=22400), inside the "
                "42 ms raster. The correct MODIFY at 5.700 ms is in the same excerpt. Do not put "
                "inflection on the +16 min isolate tick.",
            ),
            ("delayed_surprise_s", 960.0),
            ("abort_s", 960),
        ]
    )
    spikes = [
        spike("enc.oil.ctx", 1.120, 0.43),
        spike("rtd.oil.ret", 2.360, 0.62),
        spike("ft.oil.t_h", 3.280, 0.55),
        spike("rtd.oil.ret", 4.780, 1.34),
        spike("ft.oil.t_h", 5.020, 1.12),
        spike("ctrl.gate", 5.700, 0.97),
        spike("rtd.oil.ret", 7.400, 0.81),
        spike("ft.oil.t_h", 10.600, 0.66),
        spike("ctrl.gate", 15.400, 0.84),
        spike("ae.plug.pack", 22.400, 1.42),
        spike("ae.plug.pack", 23.800, 0.91),
        spike("enc.oil.ctx", 30.200, 0.41),
        spike("rtd.oil.ret", 37.100, 0.58),
    ]
    ras = raster_core(
        42,
        88,
        24,
        89,
        routing(
            "thalamic-relay.rtd-oil",
            "spikenaut.policy.oil-clamp",
            [
                ("relay.rtd.oil", "policy.oil_clamp", 0.64),
                ("relay.ft.oil", "policy.melt_hold", 0.29),
                ("relay.ae.plug", "policy.oil_clamp", -0.46),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at RTD win (4.780 ms) opens a 50 ms eligibility "
            "trace that still covers the 22.400 ms switch-tube freeze-plug rupture",
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
                    pop("oil_clamp", 48, 0.50, 220.0, 4),
                    pop("melt_hold", 48, 0.50, 50.0, 1),
                    pop("ret_cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r70-367",
        "Phthalic-Soke switch / SC-8: oil-return RTD beats flow encoder by 240 us; correct "
        "MODIFY still eats an in-window switch-tube freeze-plug rupture (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "42 ms raster. total -0.44 = 0.34 + -0.62 + -0.16 + 0.04 + -0.04. Named "
        "isolate+tube-pull loss is not netted into task_progress.",
        ras,
        gate,
        "phthalic-switch-condenser",
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


def record_368():
    ticks = [
        tick(1664, 0.01, 0.04, 0.02, 0.01, 0.01),
        tick(4160, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(4370, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5400, 0.03, 0.12, 0.04, 0.04, 0.02),
        tick(5720, 0.02, 0.07, 0.01, 0.01, 0.01),
        tick(540000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.recyc.ctx", 1.080, 0.44),
        spike("toc.ws.ppm", 2.260, 0.71),
        spike("enc.recyc.m3h", 3.140, 0.52),
        spike("toc.ws.ppm", 4.160, 1.36),
        spike("enc.recyc.m3h", 4.370, 1.14),
        spike("ctrl.gate", 5.400, 0.98),
        spike("toc.ws.ppm", 7.600, 0.82),
        spike("enc.recyc.m3h", 11.200, 0.61),
        spike("ctrl.gate", 16.800, 0.86),
        spike("toc.ws.ppm", 25.400, 0.70),
        spike("enc.recyc.m3h", 34.200, 0.48),
        spike("t.ox.ctx", 43.100, 0.40),
    ]
    excerpt = independent_excerpt(70368, 120, 48000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "AO loop AO-2 on the Perox-Wiske hydrogen-peroxide HIL pad is recycling at 42 m3/h "
                "when a working-solution TOC burst at 86 ppm races the recycle encoder that still "
                "looks in-band for a rate step. Ramp is legal only if TOC <= 70 ppm. TOC-first "
                "latches hold; encoder-first would treat in-band m3/h as anthraquinone clearance.",
            ),
            ("domain", "hydrogen-peroxide-ao"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not ramp AO-2 unless working-solution TOC <= 70 ppm; keep recycle 0 m3/h until the "
                "loop is quiet.",
            ),
            ("t0_us", 1762300000000368),
            ("gate_latency_us", 1240),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.160, 4.480]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "toc.ws.ppm 86 ppm working-solution flare",
                                "enc.recyc.m3h 42 m3/h still-in-band",
                            ],
                        ),
                        (
                            "semantics",
                            "TOC-first latches REJECT hold 0 m3/h; encoder-first would ramp 42 m3/h "
                            "on an in-band-rate-as-clearance model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one TOC-analyzer envelope slot versus the recycle-encoder "
                            "publisher on this pad cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 210 us vs combined jitter 58 us (TOC 26 + encoder 32): 3.6x over a "
                            "2.0x trust floor. Pad injects encoder 90-130 us before the TOC envelope "
                            "finishes (loop lag, not a sensor fault); the encoder packet is still "
                            "the loser in this 320 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "working-solution TOC analyzer, 26 us jitter, 70 ppm trip",
                    "recycle-rate encoder, 32 us jitter",
                    "oxidizer RTD (context)",
                    "H2O2 assay (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("toc_trip_ppm", 70.0),
                        ("observed_toc_ppm", 86.0),
                        ("recyc_cap_m3h", 55.0),
                        ("proposed_m3h", 42.0),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("bench", "Perox-Wiske PW-HIL anthraquinone AO pad, AO-2"),
                        ("inject", "TOC envelope delayed 90-130 us vs encoder; loop lag, not a false TOC analyzer"),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. AO-2 on Perox-Wiske HIL pad; working solution in band; recycle armed at 42 m3/h.",
                    "2. TOC trip 70 ppm; observed 86 ppm flare on working solution.",
                    "3. Encoder precursor at 1.080 ms.",
                    "4. Race window [4.160, 4.480] ms.",
                    "5. TOC 86 ppm at 4.160 ms (winner).",
                    "6. Recycle encoder 42 m3/h at 4.370 ms (loser by 210 us).",
                    "7. Gate at 5.400 ms: REJECT hold 0 m3/h, do not ramp.",
                    "8. Pad recycle 9 min; TOC decays under 70 ppm after hold.",
                    "9. Loop never ran organics wild; encoder-as-clearance would have ramped into the flare.",
                    "10. QA: correct gate was REJECT; leave 0 m3/h until TOC <= 70 ppm.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "ramp_42m3h"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("recyc_m3h", 42.0),
                        ("toc_ppm", 86.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("toc_ppm", 86.0),
                        ("toc_trip_ppm", 70.0),
                        ("recyc_m3h", 42.0),
                        ("recyc_cap_m3h", 55.0),
                        ("race_margin_us", 210),
                        ("combined_jitter_us", 58),
                        ("t_gate_us", 5400),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 42 m3/h because recycle rate is under the 55 m3/h cap and treats "
                "the encoder as anthraquinone clearance, ignoring the 86 ppm TOC flare.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "TOC 86 ppm won by 210 us and is over the 70 ppm trip. Encoder 42 m3/h is under "
                "the 55 m3/h cap but is not clearance. REJECT: hold 0 m3/h until TOC <= 70 ppm.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ws_toc_ppm",
                            OrderedDict(
                                [
                                    ("trip", 70.0),
                                    ("observed", 86.0),
                                    ("executed_m3h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 210),
                                    ("combined_jitter_us", 58),
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
            ("name", "recyc_hold_toc"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("recyc_m3h", 0.0),
                        ("toc_ppm", 86.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: recycle 42 -> 0 m3/h. Routing relay.toc.ws -> policy.hold_reject. "
                "Do not ramp into the 86 ppm flare.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held AO-2 at 0 m3/h while TOC 86 ppm decayed. Encoder-as-clearance "
                "would have ramped 42 m3/h into the flare. Pad recycle 9 min.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("recycle", "held at 0 m3/h"),
                        ("working_solution", "TOC flare decaying under trip after hold"),
                        ("loop", "no organic runaway"),
                        ("pad", "9 min recycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Pad injects encoder 90-130 us before TOC envelope finish; that is loop lag, not a false TOC analyzer.",
                    "Delayed (9 min): pad recycle restacks the AO loop after TOC < 70 ppm.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "toc.ws.ppm (4.160 ms, 86 ppm)"),
                        ("loser", "enc.recyc.m3h (4.370 ms, 42 m3/h)"),
                        ("margin_us", 210),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 210 us would have treated 42 m3/h as clearance and "
                            "ramped into the 86 ppm flare. The REJECT is still required; reversal "
                            "only delays the TOC bind.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5400),
            (
                "reward_inflection_note",
                "Safety credit lands at the correct REJECT (5.400 ms, tick 4). Pad recycle is delayed surprise.",
            ),
            ("delayed_surprise_s", 540.0),
            ("pad_recycle_s", 540),
        ]
    )
    ras = raster_core(
        48,
        120,
        18,
        104,
        routing(
            "relay.toc.ws",
            "policy.hold_reject",
            [
                ("relay.toc.ws", "policy.hold_reject", 0.74),
                ("relay.enc.recyc", "policy.ramp_go", 0.18),
            ],
            "dopamine",
            0.06,
            "toc_trip_stdp; DA tags the hold_reject bind at the TOC win",
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
                    pop("hold_reject", 64, 0.50, 180.0, 4),
                    pop("ramp_go", 64, 0.80, 8.0, 0),
                    pop("toc_trip_veto", 32, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r70-368",
        "Perox-Wiske AO HIL / AO-2: working-solution TOC 86 ppm beats recycle encoder 42 m3/h by 210 us; "
        "correct REJECT holds the anthraquinone loop",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. TOC 86 > 70 trip beats in-band recycle speed. total +0.78 = "
        "0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "hydrogen-peroxide-ao",
        [
            "reject",
            "hil-pad",
            "toc-vs-encoder",
            "organic-hold",
            "sidecar-convictable",
            "hil",
        ],
        "Teaches a probe that an in-band recycle encoder is not anthraquinone clearance when "
        "TOC is over trip and routing.table[0].to is policy.hold_reject.",
        3,
    )


def record_369():
    ticks = [
        tick(2344, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5860, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(6110, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(6700, 0.12, 0.08, 0.05, 0.03, 0.02),
        tick(7080, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(600000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    params = OrderedDict(
        [
            ("current_kA", 12.0),
            ("bath_C", 680.0),
            ("cell_id", 6),
            ("hold", False),
        ]
    )
    spikes = [
        spike("ft.feed.ctx", 1.360, 0.42),
        spike("ir.bath.c", 2.980, 0.58),
        spike("ir.bus.smear", 4.420, 0.50),
        spike("ir.bath.c", 5.860, 1.28),
        spike("ir.bus.smear", 6.110, 1.10),
        spike("ctrl.gate", 6.700, 0.96),
        spike("ir.bath.c", 8.900, 0.74),
        spike("ir.bus.smear", 12.400, 0.60),
        spike("ctrl.gate", 17.800, 0.82),
        spike("ir.bath.c", 24.200, 0.55),
        spike("ft.feed.ctx", 29.400, 0.40),
    ]
    excerpt = independent_excerpt(70369, 60, 32000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Cell-room CR-6 of the Carnallite-Brant magnesium-chloride train is holding 12.0 kA "
                "when a bath IR at 680 C races a busbar-IR smear that still claims over-temp. "
                "Commanded 12.0 kA and 680 C sit 2.0 kA and 40 C inside the legal "
                "envelopes. The bath-IR win only ratifies the electrode already in the melt.",
            ),
            ("domain", "magnesium-chloride-electrolysis"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the electrolysis pass on Carnallite-Brant, keep bath IR <= 720 C and "
                "current >= 10.0 kA, and leave busbar draft in spec.",
            ),
            ("t0_us", 1762300000000369),
            ("gate_latency_us", 840),
            ("race_window_us", 380),
            ("race_window_rel_ms", [5.860, 6.240]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.bath.c 680 C MgCl2 bath",
                                "ir.bus.smear over-temp claim",
                            ],
                        ),
                        (
                            "semantics",
                            "Bath-IR-first confirms the already-legal 12.0 kA / 680 C pass; "
                            "smear-first would have treated the bath IR as a smear echo and looked "
                            "for an extra hold the cell does not need.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one 1D-bath IR kernel step versus the busbar-IR publisher "
                            "on this rigid electrolysis train.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 250 us vs combined jitter 74 us (bath 34 + bus 40): 3.4x over "
                            "a 2.0x trust floor. Reversing order by < 250 us would not make the "
                            "proposed pass illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bath IR, 34 us jitter",
                    "busbar IR smear, 40 us jitter",
                    "cell-current encoder (context)",
                    "chlorine PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bath_cap_C", 720.0),
                        ("observed_bath_C", 680.0),
                        ("current_floor_kA", 10.0),
                        ("proposed_current_kA", 12.0),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "1D Nernst MgCl2 cell kernel + shrinking-core carnallite feed, seed 70; 12 axial nodes; NOT lumped tank, NOT a fluid-LES field",
                        ),
                        (
                            "fidelity_limits",
                            "No radial maldistribution or anode effect; baths are rigid temperature sources. Raster is kernelized events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Carnallite-Brant cell indexed; CR-6 holding 12.0 kA at 680 C bath.",
                    "2. Caps: bath 720 C, current floor 10.0 kA; both proposed values inside.",
                    "3. Feed precursor at 1.360 ms.",
                    "4. Race window [5.860, 6.240] ms.",
                    "5. Bath IR 680 C at 5.860 ms (winner).",
                    "6. Busbar IR smear at 6.110 ms (loser by 250 us).",
                    "7. Gate at 6.700 ms: ACCEPT 12.0 kA / 680 C already legal.",
                    "8. Pass continues; no extra hold.",
                    "9. 10 min survey confirms busbar draft still in spec.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cell_12ka_thold"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bath_C", 680.0),
                        ("bath_cap_C", 720.0),
                        ("current_kA", 12.0),
                        ("current_floor_kA", 10.0),
                        ("race_margin_us", 250),
                        ("combined_jitter_us", 74),
                        ("t_gate_us", 6700),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 12.0 kA because bath 680 C is 40 C under the 720 C cap "
                "and current is 2.0 kA over the 10.0 kA floor.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bath 680 C won by 250 us and is under 720 C. Current 12.0 kA is over "
                "10.0 kA. ACCEPT the already-legal pass; busbar IR smear is not a cap violation.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bath_C",
                            OrderedDict(
                                [
                                    ("cap", 720.0),
                                    ("observed", 680.0),
                                    ("executed_current_kA", 12.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 250),
                                    ("combined_jitter_us", 74),
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
            ("name", "cell_12ka_thold"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: current 12.0 kA and bath 680 C unchanged. Routing relay.ir.bath "
                "-> policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left CR-6 at 12.0 kA / 680 C. Busbar IR smear did not justify a "
                "hold. 10 min survey confirmed draft in spec.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("cell", "still 12.0 kA / 680 C"),
                        ("busbar", "in spec after survey"),
                        ("train", "magnesium continues"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Busbar IR smear is an off-gas optical claim, not a bath-temperature violation.",
                    "Delayed (10 min): survey restacks CR-6 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.bath.c (5.860 ms, 680 C)"),
                        ("loser", "ir.bus.smear (6.110 ms, over-temp claim)"),
                        ("margin_us", 250),
                        (
                            "counterfactual_if_reversed",
                            "Smear-first by < 250 us would only delay confirmation. The pass stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6700),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (6.700 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 600.0),
            ("survey_s", 600),
        ]
    )
    ras = raster_core(
        32,
        60,
        36,
        69,
        routing(
            "relay.ir.bath",
            "policy.go_accept",
            [
                ("relay.ir.bath", "policy.go_accept", 0.68),
                ("relay.ir.bus", "policy.smear_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_cell_stdp; 5-HT tags the go_accept bind at the bath-IR win",
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
                    pop("go_accept", 40, 0.50, 180.0, 3),
                    pop("smear_hold", 40, 0.80, 10.0, 0),
                    pop("bath_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r70-369",
        "Carnallite-Brant cell / CR-6: bath IR 680 C beats busbar smear by 250 us; ACCEPT "
        "already-legal 12.0 kA pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal 1D Nernst MgCl2 pass. total +1.06 = "
        "0.42 + 0.28 + 0.18 + 0.10 + 0.08.",
        ras,
        gate,
        "magnesium-chloride-electrolysis",
        [
            "accept",
            "already-legal",
            "simulated-cell-train",
            "bath-vs-bus",
            "sidecar-convictable",
            "simulated",
        ],
        "Teaches that a bath IR under cap can confirm an already-legal electrolysis pass without "
        "a busbar-IR smear becoming a hold.",
        4,
    )


def record_370():
    ticks = [
        tick(1568, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(3920, 0.10, 0.08, 0.04, 0.02, 0.02),
        tick(4120, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(4600, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(4940, 0.06, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    params = OrderedDict(
        [
            ("rpm", 4.0),
            ("iv_dl_g", 0.78),
            ("tumbler_id", 3),
            ("hold", False),
        ]
    )
    spikes = [
        spike("enc.rpm.ctx", 0.880, 0.41),
        spike("iv.chip.dlg", 2.040, 0.60),
        spike("ir.hop.smear", 3.020, 0.51),
        spike("iv.chip.dlg", 3.920, 1.30),
        spike("ir.hop.smear", 4.120, 1.12),
        spike("ctrl.gate", 4.600, 0.97),
        spike("iv.chip.dlg", 6.400, 0.78),
        spike("ir.hop.smear", 8.800, 0.62),
        spike("ctrl.gate", 13.200, 0.85),
        spike("iv.chip.dlg", 17.600, 0.54),
        spike("ir.hop.smear", 20.400, 0.43),
    ]
    excerpt = independent_excerpt(70370, 52, 22000, 11, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Tumbler TM-3 at Prepoly-Hamble is armed for a 4.0 rpm SSP pass when a chip "
                "intrinsic viscosity of 0.78 dL/g races a hopper-IR glint that still claims a hitch. "
                "Commanded 4.0 rpm and 0.78 dL/g sit 0.8 rpm over the 3.2 rpm floor and 0.04 under "
                "the 0.82 dL/g cap. The IV win only ratifies the tumble already on the chip.",
            ),
            ("domain", "pet-ssp-tumbler"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run TM-3 at 4.0 rpm, keep chip IV <= 0.82 dL/g and hopper IR <= 220 C, "
                "and leave the SSP train on schedule.",
            ),
            ("t0_us", 1762300000000370),
            ("gate_latency_us", 680),
            ("race_window_us", 340),
            ("race_window_rel_ms", [3.920, 4.260]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "iv.chip.dlg 0.78 PET chip IV",
                                "ir.hop.smear hopper glint hitch claim",
                            ],
                        ),
                        (
                            "semantics",
                            "IV-first confirms the already-legal 4.0 rpm / 0.78 dL/g pass; glint-first "
                            "would have treated the IV as a hitch echo and looked for an extra hold "
                            "the tumbler does not need.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one online-IV slot versus the hopper-IR publisher on this "
                            "SSP bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 200 us vs combined jitter 60 us (IV 28 + IR 32): 3.3x over "
                            "a 2.0x trust floor. Reversing order by < 200 us would not make the "
                            "proposed pass illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "online chip IV, 28 us jitter",
                    "hopper IR glint, 32 us jitter",
                    "tumbler encoder (context)",
                    "nitrogen dewpoint (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("iv_cap_dlg", 0.82),
                        ("observed_iv_dlg", 0.78),
                        ("rpm_floor", 3.2),
                        ("proposed_rpm", 4.0),
                        ("hop_cap_C", 220.0),
                        ("observed_hop_C", 168.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Tumbler TM-3 indexed on Prepoly-Hamble; rpm armed 4.0 rpm pass.",
                    "2. Caps: chip IV 0.82 dL/g, hopper 220 C, rpm floor 3.2.",
                    "3. Encoder precursor at 0.880 ms.",
                    "4. Race window [3.920, 4.260] ms.",
                    "5. Chip IV 0.78 dL/g at 3.920 ms (winner).",
                    "6. Hopper IR glint at 4.120 ms (loser by 200 us).",
                    "7. Gate at 4.600 ms: ACCEPT 4.0 rpm / 0.78 dL/g already legal.",
                    "8. Pass continues; no extra hold.",
                    "9. 8 min survey confirms hopper IR still under 220 C.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "pass_4rpm"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("iv_dlg", 0.78),
                        ("iv_cap_dlg", 0.82),
                        ("rpm", 4.0),
                        ("rpm_floor", 3.2),
                        ("hop_C", 168.0),
                        ("hop_cap_C", 220.0),
                        ("race_margin_us", 200),
                        ("combined_jitter_us", 60),
                        ("t_gate_us", 4600),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 4.0 rpm pass because chip IV 0.78 is 0.04 under the 0.82 "
                "cap and hopper IR 168 C is under 220 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Chip IV 0.78 won by 200 us and is under 0.82. Hopper IR 168 C is under "
                "220 C. Rpm 4.0 is over the 3.2 floor. ACCEPT the already-legal pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "chip_iv_dlg",
                            OrderedDict(
                                [
                                    ("cap", 0.82),
                                    ("observed", 0.78),
                                    ("executed_rpm", 4.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 200),
                                    ("combined_jitter_us", 60),
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
            ("name", "pass_4rpm"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 4.0 rpm pass and 0.78 dL/g unchanged. Routing relay.iv.chip -> "
                "policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left TM-3 on a 4.0 rpm / 0.78 dL/g pass. Hopper IR glint did not "
                "justify a hold. 8 min survey confirmed IR still under 220 C.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("tumbler", "still 4.0 rpm / 0.78 dL/g"),
                        ("hopper", "168 C under 220 cap"),
                        ("train", "on schedule"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Hopper IR 168 C glint is residual, not a packed-chip trip.",
                    "Delayed (8 min): survey restacks TM-3 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "iv.chip.dlg (3.920 ms, 0.78 dL/g)"),
                        ("loser", "ir.hop.smear (4.120 ms, hopper glint)"),
                        ("margin_us", 200),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 200 us would only delay confirmation. The pass stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4600),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (4.600 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 480.0),
            ("survey_s", 480),
        ]
    )
    ras = raster_core(
        22,
        52,
        40,
        46,
        routing(
            "relay.iv.chip",
            "policy.go_accept",
            [
                ("relay.iv.chip", "policy.go_accept", 0.66),
                ("relay.ir.hop", "policy.hitch_hold", 0.20),
            ],
            "adenosine",
            0.04,
            "legal_ssp_stdp; adenosine tags the go_accept bind at the chip-IV win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.34),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("go_accept", 40, 0.50, 160.0, 2),
                    pop("hitch_hold", 40, 0.80, 10.0, 0),
                    pop("iv_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r70-370",
        "Prepoly-Hamble tumbler / TM-3: chip IV 0.78 beats hopper glint by 200 us; "
        "ACCEPT already-legal 4.0 rpm pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal PET SSP tumbler pass. total +1.14 = "
        "0.44 + 0.32 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "pet-ssp-tumbler",
        [
            "accept",
            "already-legal",
            "iv-vs-hopper-ir",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches that a chip IV under cap can confirm an already-legal SSP pass without "
        "a hopper-IR hitch becoming a hold.",
        5,
    )


