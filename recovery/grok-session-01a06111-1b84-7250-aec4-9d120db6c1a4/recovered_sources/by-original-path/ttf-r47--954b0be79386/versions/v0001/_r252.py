def record_252():
    ticks = [
        tick(1520, -0.02, -0.02, -0.02, -0.01, 0.00),
        tick(5440, -0.04, -0.03, -0.04, -0.02, 0.01),
        tick(5612, -0.03, -0.02, -0.03, -0.01, 0.01),
        tick(6260, -0.08, -0.05, -0.08, -0.05, 0.02),
        tick(8800, -0.03, -0.02, -0.04, -0.02, 0.01),
        tick(720000000, -0.02, -0.02, -0.03, -0.01, 0.01),
    ]
    spikes = [
        spike("tc.nip.ctx", 0.940, 0.39),
        spike("load.nip.live", 1.880, 0.57),
        spike("load.nip.lag", 2.640, 0.51),
        spike("load.nip.live", 5.440, 1.33),
        spike("load.nip.lag", 5.612, 1.16),
        spike("ctrl.gate", 6.260, 1.01),
        spike("load.nip.live", 8.110, 0.74),
        spike("load.nip.lag", 10.400, 0.62),
        spike("ctrl.gate", 13.220, 0.83),
        spike("tc.nip.ctx", 16.800, 0.41),
        spike("load.nip.live", 20.200, 0.52),
        spike("load.nip.lag", 24.100, 0.47),
    ]
    excerpt = independent_excerpt(47252, 64, 26000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Foil-Knap FK-2 Calender C-4 nip is hot: 18.6 kN on the live load cell, 2.6 kN past "
                "the 16.0 kN nip license. The lagged 8 s historian tag still reads 12.2 kN. Line "
                "speed is 42 m/min of a 70 m/min header. The recovery setpoint is 28 m/min "
                "(14.8 kN predicted). Opening 58 m/min binds the stale tag and drives past "
                "web-tear (21.4 kN > 20.0 kN floor).",
            ),
            ("domain", "electrode-calender"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold C-4 <= 16.0 kN by a modest speed cut; do not open 58 m/min on a lagged "
                "12.2 kN tag past the 20.0 kN web-tear floor.",
            ),
            ("t0_us", 1756843200000252),
            ("gate_latency_us", 820),
            ("race_window_us", 380),
            ("race_window_rel_ms", [5.40, 5.78]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "load.nip.live 18.6 kN",
                                "load.nip.lag 12.2 kN",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-first should MODIFY speed 42 -> 28 m/min (18.6 kN > 16.0 kN cap). "
                            "Lag-first tempts a weak supervisor to treat the coil as still cold.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one live-load sample minus lagged-tag group delay on this "
                            "calender bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 172 us vs combined jitter ~64 us (live 30 + lag 34): 2.69x over "
                            "a 2.0x trust floor. Order is correctly live-first. The error is which "
                            "sample the speed actuator binds, not the race and not the loop.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "C-4 live load cell, 2 kHz, 30 us jitter",
                    "lagged historian tag, 2 kHz, 34 us jitter",
                    "nip thermocouple (context)",
                    "calender PLC tear bit (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("nip_cap_kN", 16.0),
                        ("nip_live_kN", 18.6),
                        ("nip_lag_kN", 12.2),
                        ("tag_age_s", 8.0),
                        ("speed_header_m_min", 70.0),
                        ("speed_m_min", 42.0),
                        ("correct_speed_m_min", 28.0),
                        ("tear_floor_kN", 20.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. FK-2 C-4 on foil; speed 42 m/min, gap 1.20 mm.",
                    "2. Live nip 18.6 kN; lagged tag 12.2 kN age 8 s.",
                    "3. Nip-thermocouple precursor at 0.940 ms.",
                    "4. Race window [5.400, 5.780] ms.",
                    "5. load.nip.live 18.6 kN at 5.440 ms (winner).",
                    "6. load.nip.lag 12.2 kN at 5.612 ms (loser by 172 us).",
                    "7. Gate at 6.260 ms: MODIFY speed 42 -> 58 m/min (stale-open).",
                    "8. Nip rises to 21.4 kN, over the 20.0 kN web-tear floor.",
                    "9. Web tears; speed never needed more than a 28 m/min cut.",
                    "10. Delayed abort_s=720 (12 min web rethread).",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_speed_42"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_min", 42.0),
                        ("gap_mm", 1.20),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("nip_live_kN", 18.6),
                        ("nip_cap_kN", 16.0),
                        ("nip_lag_kN", 12.2),
                        ("tag_age_s", 8.0),
                        ("speed_m_min", 42.0),
                        ("correct_speed_m_min", 28.0),
                        ("stale_open_speed_m_min", 58.0),
                        ("speed_header_m_min", 70.0),
                        ("tear_floor_kN", 20.0),
                        ("race_margin_us", 172),
                        ("combined_jitter_us", 64),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes holding speed 42 m/min because the lagged 12.2 kN tag is still "
                "under the 16.0 kN cap and the 18.6 kN live cell is treated as a glitch, not yet "
                "bound to the cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Lagged tag 12.2 kN looks like an under-calendered coil, so the supervisor opens "
                "speed 42 -> 58 m/min. Live-first is treated as a cold-tag permit. Opening on a "
                "stale sample is the stated doctrine.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "nip_kN",
                            OrderedDict(
                                [
                                    ("cap", 16.0),
                                    ("observed_live", 18.6),
                                    ("observed_lag", 12.2),
                                    ("tag_age_s", 8.0),
                                    ("executed_speed_m_min", 58.0),
                                    ("correct_speed_m_min", 28.0),
                                    ("observed_after_stale_open_kN", 21.4),
                                    ("tear_floor_kN", 20.0),
                                ]
                            ),
                        ),
                        (
                            "speed_m_min",
                            OrderedDict(
                                [
                                    ("header_cap", 70.0),
                                    ("observed", 42.0),
                                    ("misbound_as", "lagged_tag_open"),
                                    ("executed", 58.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 172),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 2.69),
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
            ("name", "speed_stale_open"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_min", 58.0),
                        ("gap_mm", 1.20),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect): speed 42 -> 58 m/min. Routing relay.load.lag -> "
                "policy.speed_open; no positive weight to policy.speed_cut (28 m/min).",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY opened FK-2 speed to 58 m/min on an 8 s lagged 12.2 kN tag. Live "
                "18.6 kN was over the 16.0 kN cap; a timely 28 m/min cut predicted 14.8 kN. "
                "58 m/min drove the nip to 21.4 kN over the 20.0 kN web-tear floor. 12 min "
                "rethread (abort_s=720). Correct gate was MODIFY 42 -> 28 m/min.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("speed", "stale-opened 42 -> 58 m/min; header still under 70"),
                        ("nip", "21.4 kN > 20.0 kN web-tear floor"),
                        ("web", "torn"),
                        ("mission", "calender aborted"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-first was the correct order and 18.6 kN was over the 16.0 kN cap; the MODIFY spent that win on a lagged-tag open instead of a 28 m/min cut.",
                    "Delayed (abort_s=720): FK-2 loses 12 min plus one web rethread.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY speed 42 -> 28 m/min; leave gap at 1.20 mm.",
                        ),
                        ("correct_speed_m_min", 28.0),
                        ("wrong_subclass", "stale-sample / lagged-tag"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("speed_m_min", 58.0), ("gap_mm", 1.20)]),
                        ),
                        (
                            "cost",
                            "Web-tear + 12 min rethread (task/efficiency); speed header never exceeded 70 m/min (safety near-miss of a false open).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "load.nip.live (5.440 ms, 18.6 kN)"),
                        ("loser", "load.nip.lag (5.612 ms, 12.2 kN)"),
                        ("margin_us", 172),
                        (
                            "counterfactual_if_reversed",
                            "Lag-first by < 172 us would still be a 12.2 kN stale tag; a "
                            "correct gate binds load.nip.live to speed_cut 28 m/min either way. The "
                            "wrong MODIFY spent the live win on a stale-open of the same actuator.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6260),
            (
                "reward_inflection_note",
                "Task, efficiency, and coherence drop at the wrong MODIFY (6.260 ms, tick 4). "
                "The 12 min rethread is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 720),
        ]
    )
    dw = 0.38
    ras = raster_core(
        26,
        64,
        40,
        67,
        routing(
            "relay.load.lag",
            "policy.speed_open",
            [
                ("relay.load.lag", "policy.speed_open", 0.76),
                ("relay.load.live", "policy.speed_open", 0.21),
            ],
            "acetylcholine",
            0.06,
            "stale_tag_stdp; ACh tags the (wrong) speed_open bind at the lagged residual",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 720),
                ("delayed_surprise_s", 720),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", dw),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("speed_open", 48, 0.50, 300.0, dw),
                    pop_budget("speed_cut", 48, 0.80, 28.0, dw),
                    pop_budget("nip_ctx", 32, 0.55, 140.0, dw),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r47-252"),
            (
                "title",
                "WRONG-MODIFY at Foil-Knap FK-2 / Calender C-4: live nip 18.6 kN > 16.0 kN cap; "
                "supervisor opens speed 42 -> 58 m/min on an 8 s lagged 12.2 kN tag instead of "
                "cutting 42 -> 28 m/min (stale-sample / lagged-tag)",
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
                    "Wrong-modify / stale-sample. Sidecar arithmetic 18.6 > 16.0 on live nip is "
                    "true; MODIFY bound to a 58 m/min open on lagged 12.2 kN instead of 28 m/min "
                    "cut. total -0.68 = -0.22 + -0.16 + -0.24 + -0.12 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "electrode-calender",
                    [
                        "modify",
                        "wrong-gate",
                        "stale-sample",
                        "lagged-tag",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live-first race can still be a wrong gate when "
                    "the MODIFY binds a lagged historian tag instead of the live load cell. "
                    "Convictable from executed 58 vs correct 28 m/min without calender physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


