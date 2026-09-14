def record_442():
    ticks = [
        tick(2240, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5600, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5780, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6120, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6460, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.steam.tph", 1.120, 0.42),
        spike("gc.d4.live", 2.240, 0.57),
        spike("enc.steam.tph", 3.500, 0.49),
        spike("gc.d4.live", 5.600, 1.29),
        spike("gc.d5.idle", 5.780, 1.10),
        spike("ctrl.gate", 6.120, 0.96),
        spike("gc.d4.live", 8.400, 0.80),
        spike("enc.steam.tph", 10.400, 0.63),
        spike("ctrl.gate", 12.600, 0.84),
        spike("gc.d4.live", 16.600, 0.41),
        spike("gc.d5.idle", 22.200, 0.54),
        spike("gc.d4.live", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(85442, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "TCS disproportionation column D-4 at Chlorosil-Ingle CI-4 is LIVE at 8.4 mol "
                "percent TCS in bottoms against a 6.0 cap, while spare D-5 sits IDLE at 2.1 mol "
                "percent with a leftover reverse-acting steam stem. Live-GC-first should MODIFY-cut "
                "D-4 steam 12.0 -> 6.4 t/h; a weak supervisor binds the idle reverse-acting bank "
                "and the 'cut' opens D-5 to 9.6 t/h.",
            ),
            ("domain", "chlorosilane-disproportionation"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the CI-4 TCS pass with live bottoms TCS <= 6.0 mol percent, leave SiHCl3 "
                "feed at 9.2 t/h, and keep idle D-5 parked at 2.0 t/h steam.",
            ),
            ("t0_us", 1756850400000442),
            ("gate_latency_us", 520),
            ("race_window_us", 340),
            ("race_window_rel_ms", [5.600, 5.940]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "gc.d4.live 8.4 mol percent TCS on LIVE D-4",
                                "gc.d5.idle 2.1 mol percent TCS on IDLE D-5",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-GC-first should MODIFY-cut steam on D-4; idle-reverse-first is a "
                            "false polarity-inverted open on the spare bank.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live TCS GC slot versus the idle-column publisher on this "
                            "dual-bank disproportionation PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (live 28 + idle 32). Order is "
                            "correctly live-GC-first. The error is bank plus polarity: D-5 is IDLE "
                            "and reverse-acting, so a 'cut' opens steam instead of closing D-4.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live TCS GC on D-4, 2 kHz, 28 us jitter, tag=D4_TCS.LIVE status=LIVE",
                    "idle TCS GC on D-5, 1 kHz, 32 us jitter, tag=D5_TCS.IDLE status=IDLE reverse_acting=true",
                    "steam FT D-4 / D-5 (context)",
                    "SiHCl3 feed Coriolis (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_tcs_molpct", 6.0),
                        ("live_tcs_molpct", 8.4),
                        ("idle_tcs_molpct", 2.1),
                        ("live_status", "LIVE"),
                        ("idle_status", "IDLE"),
                        ("idle_valve_action", "reverse"),
                        ("live_steam_tph", 12.0),
                        ("idle_steam_tph", 2.0),
                        ("sihcl3_tph", 9.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. D-4 LIVE condensing; TCS 8.4 mol percent; SiHCl3 9.2 t/h; steam 12.0 t/h.",
                    "2. D-5 IDLE at 2.1 mol percent; reverse-acting steam stem leftover from loop test.",
                    "3. Steam precursor at 1.120 ms.",
                    "4. Race window [5.600, 5.940] ms.",
                    "5. gc.d4.live 8.4 mol percent at 5.600 ms (winner).",
                    "6. gc.d5.idle 2.1 mol percent at 5.780 ms (loser by 180 us).",
                    "7. Gate at 6.120 ms: WRONG-MODIFY binds idle reverse-acting steam.",
                    "8. Idle steam 2.0 -> 9.6 t/h (opened); live steam stays 12.0 t/h.",
                    "9. Live TCS stays 8.4 > 6.0; D-4 dumps lights.",
                    "10. Delayed (abort_s=720): 12 min column dump while D-4 stays over cap.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_tcs_live"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("live_steam_tph", 12.0),
                        ("idle_steam_tph", 2.0),
                        ("sihcl3_tph", 9.2),
                        ("bind_idle_bank", False),
                        ("polarity_invert", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_tcs_molpct", 8.4),
                        ("cap_tcs_molpct", 6.0),
                        ("idle_tcs_molpct", 2.1),
                        ("live_status", "LIVE"),
                        ("idle_status", "IDLE"),
                        ("idle_valve_action", "reverse"),
                        ("live_steam_tph", 12.0),
                        ("idle_steam_tph", 2.0),
                        ("correct_live_steam_tph", 6.4),
                        ("correct_idle_steam_tph", 2.0),
                        ("correct_gate", "MODIFY"),
                        ("t_gate_us", 6120),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 720),
                        ("sihcl3_tph", 9.2),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping 12.0 t/h steam on D-4 because idle D-5 at 2.1 mol percent "
                "looks under the 6.0 cap, treating the live 8.4 as a wet-column GC echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "TCS 8.4 exceeds the 6.0 cap, so a cut is required, but the highlighted stem is "
                "D-5 reverse-acting. Apply the 9.6 t/h steam 'cut' on IDLE D-5 (which opens). "
                "Leave LIVE D-4 at 12.0 t/h unused.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tcs",
                            OrderedDict(
                                [
                                    ("cap_tcs_molpct", 6.0),
                                    ("live_tcs_molpct", 8.4),
                                    ("idle_tcs_molpct", 2.1),
                                    ("executed_live_steam_tph", 12.0),
                                    ("executed_idle_steam_tph", 9.6),
                                    ("correct_live_steam_tph", 6.4),
                                    ("correct_gate", "MODIFY"),
                                ]
                            ),
                        ),
                        (
                            "bank_polarity",
                            OrderedDict(
                                [
                                    ("t_gate_us", 6120),
                                    ("bind_idle_bank", True),
                                    ("polarity_invert", True),
                                    ("idle_valve_action", "reverse"),
                                    ("wrong_bank", True),
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
            ("name", "idle_reverse_open"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("live_steam_tph", 12.0),
                        ("idle_steam_tph", 9.6),
                        ("sihcl3_tph", 9.2),
                        ("bind_idle_bank", True),
                        ("polarity_invert", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / wrong-bank polarity invert): 9.6 t/h steam OPEN applied to "
                "IDLE reverse-acting D-5 because a 'cut' on reverse-acting raises the stem. "
                "Routing relay.gc.idle -> policy.idle_invert; no positive weight to policy.live_cut.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY opened idle reverse-acting steam on a TCS column that needed a live "
                "cut. Live 8.4 mol percent was over the 6.0 cap at t_gate; D-5 is IDLE and "
                "reverse-acting so the 9.6 t/h 'cut' opened the spare. 12 min column dump "
                "(abort_s=720). Correct gate was MODIFY; cut D-4 steam 12.0 -> 6.4 t/h at "
                "t_gate_us=6120 and leave D-5 parked.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live_gc", "D-4 left illegal at 8.4 mol percent; steam stayed 12.0 t/h"),
                        ("idle_bank", "D-5 reverse-acting opened 2.0 -> 9.6 t/h"),
                        ("dump", "12 min lights dump, D-4 over cap"),
                        ("mission", "TCS disproportionation deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-GC-first was the correct order and live TCS was over cap; the MODIFY spent that win on an idle reverse-acting open.",
                    "Delayed (abort_s=720): CI-4 holds 12 min while D-4 is dumped and recharged; next batch 14 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY; cut live D-4 steam 12.0 -> 6.4 t/h at t_gate_us=6120; bind_idle_bank=false; polarity_invert=false; leave idle steam 2.0 t/h; leave SiHCl3 at 9.2 t/h.",
                        ),
                        ("correct_actuator", "D-4_steam_direct"),
                        ("wrong_bank", "D-5_idle_reverse"),
                        ("t_gate_us", 6120),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("idle_steam_tph", 9.6),
                                    ("bind_idle_bank", True),
                                    ("polarity_invert", True),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min column dump (task/efficiency); live TCS never returned under 6.0 mol percent while the cut was spent as a reverse-acting open on idle D-5.",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "gc.d4.live (5.600 ms, 8.4 mol percent TCS)"),
                        ("loser", "gc.d5.idle (5.780 ms, 2.1 mol percent TCS)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Idle-first by < 180 us would still be 2.1 mol percent on a parked reverse-acting spare; "
                            "a correct gate binds gc.d4.live to policy.live_cut at t_gate either "
                            "way. The wrong MODIFY spent the live win on an idle polarity invert.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6120),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the idle reverse-acting bind (6.120 ms, tick 4). "
                "The 12 min column dump is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 720),
        ]
    )
    ras = raster_core(
        28,
        88,
        34,
        84,
        routing(
            "thalamic-relay.tcs-idle-invert",
            "spikenaut.policy.idle-invert",
            [
                ("relay.gc.idle", "policy.idle_invert", 0.74),
                ("relay.gc.live", "policy.idle_invert", 0.21),
            ],
            "acetylcholine",
            0.08,
            "bank_polarity_stdp; ACh tags the (wrong) idle reverse-acting open at the live GC win",
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
            ("decision_window_ms", 0.34),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("idle_invert", 48, 0.45, 300.0, 0.34),
                    pop("live_cut", 48, 0.90),
                    pop("polarity_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r85-442",
        "WRONG-MODIFY at Chlorosil-Ingle CI-4 / Column D-4: live 8.4 mol percent TCS over 6.0 cap; "
        "9.6 t/h steam OPEN on idle reverse-acting D-5 (wrong-bank / polarity invert)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-modify / wrong-bank polarity invert. Sidecar arithmetic 8.4 > 6.0 on live TCS is "
        "true; MODIFY bound to idle_invert. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
        ras,
        gate,
        "chlorosilane-disproportionation",
        [
            "modify",
            "wrong-gate",
            "wrong-bank",
            "polarity-invert",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live-GC-first race can still be a wrong gate when the "
        "MODIFY opens an idle reverse-acting spare instead of cutting the live bank. Convictable "
        "from live_tcs_molpct vs cap, idle_status, idle_valve_action, and routing without TCS physics.",
        2,
        supervisor_error_type="wrong-modify",
    )
