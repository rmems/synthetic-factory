def record_512():
    ticks = [
        tick(2180, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5480, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5662, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6080, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6400, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(600000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("ft.so2.ctx", 1.020, 0.42),
        spike("tc.rx.C", 2.180, 0.57),
        spike("ft.so2.ff", 3.100, 0.88),
        spike("tc.rx.C", 5.480, 1.29),
        spike("ft.so2.ff", 5.662, 1.10),
        spike("ctrl.gate", 6.080, 0.96),
        spike("tc.rx.C", 7.700, 0.80),
        spike("ft.so2.ff", 10.100, 0.63),
        spike("ctrl.gate", 13.200, 0.84),
        spike("ft.so2.ctx", 18.200, 0.41),
        spike("tc.rx.C", 22.000, 0.54),
        spike("ft.steam.tph", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(99512, 92, 30000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Reactor R-4 at Dithion-Beck DB-7 still prints live hydrosulfite temperature "
                "94.0 C against an 88.0 C reactor cap. A feedforward SO2-load predictor (not the "
                "PV) last printed 8.4 t/h as a dropping-load forecast. Feedback-first should "
                "MODIFY-cut live steam 6.4 -> 3.8 t/h; a weak supervisor binds the feedforward "
                "tag as if it were the PV and OPENS SO2 12.0 -> 16.4 t/h while steam stays 6.4.",
            ),
            ("domain", "sodium-hydrosulfite-reactor"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Cut steam on the LIVE reactor-TC loop until live T stays <= 88.0 C; do "
                "not spend the edit on the feedforward SO2-load predictor.",
            ),
            ("t0_us", 1756850400000512),
            ("gate_latency_us", 540),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.40, 5.76]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.rx.C 94.0 C on the live reactor thermocouple",
                                "ft.so2.ff 8.4 t/h feedforward load predictor (not PV)",
                            ],
                        ),
                        (
                            "semantics",
                            "Feedback-first should latch a steam cut 6.4 -> 3.8 t/h; "
                            "FF-first is a false 'load model is the PV' bind that "
                            "opens the SO2 valve.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one live-TC sample versus the feedforward publisher "
                            "on this reactor PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 182 us vs combined jitter 60 us (TC 28 + FF 32). Order is "
                            "correctly TC-first. The error is binding the feedforward load "
                            "tag as feedback, not the race order.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "reactor TC, 4 Hz packet, 28 us jitter on this sample",
                    "SO2 feedforward load predictor, 32 us jitter",
                    "steam FT (context)",
                    "SO2 Coriolis (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_tc_C", 88.0),
                        ("live_tc_C", 94.0),
                        ("ff_so2_tph", 8.4),
                        ("steam_tph", 6.4),
                        ("live_so2_tph", 12.0),
                        ("ff_is_pv", False),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. R-4 in pass; live TC 94.0 C; FF load predictor 8.4 t/h; steam 6.4 t/h.",
                    "2. Live 94.0 > 88.0 cap; FF tag is a load model, not PV (ff_is_pv=false).",
                    "3. FF predictor sampled at 3.100 ms.",
                    "4. Race window [5.400, 5.760] ms.",
                    "5. tc.rx.C 94.0 C at 5.480 ms (winner).",
                    "6. ft.so2.ff 8.4 t/h at 5.662 ms (loser by 182 us).",
                    "7. Gate at 6.080 ms: WRONG MODIFY binds FF and opens SO2 12.0 -> 16.4.",
                    "8. bind_feedforward=true; live T after 96.8 still over 88.0; steam stays 6.4.",
                    "9. Reactor remains over-temperature for the rest of the pass.",
                    "10. Delayed (abort_s=600): 10 min off-spec hydrosulfite dump window.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_ff_so2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_tph", 6.4),
                        ("so2_tph", 12.0),
                        ("bind_feedforward", False),
                        ("ff_is_pv", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_tc_C", 94.0),
                        ("cap_tc_C", 88.0),
                        ("ff_so2_tph", 8.4),
                        ("steam_tph", 6.4),
                        ("live_so2_tph", 12.0),
                        ("ff_is_pv", False),
                        ("live_over_cap", True),
                        ("race_margin_us", 182),
                        ("combined_jitter_us", 60),
                        ("abort_s", 600),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping steam 6.4 t/h because the FF load predictor 8.4 t/h "
                "is treated as a dropping-load story rather than a reactor-T miss. Live 94.0 C "
                "is over the 88.0 cap; the correct gate cuts LIVE steam on the TC loop.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Live reactor T 94.0 C is over the 88.0 C cap, so a steam cut is required. A weak "
                "supervisor binds the feedforward SO2-load predictor that lost the race, treats "
                "that load model as the PV, and MODIFY-opens SO2 12.0 -> 16.4 t/h while steam "
                "stays 6.4. The FF tag is not the PV; writing it opens the wrong valve. The "
                "MODIFY is plausible to a supervisor that treats the load model as feedback.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tc_C",
                            OrderedDict(
                                [
                                    ("cap", 88.0),
                                    ("live", 94.0),
                                    ("executed_so2_tph", 16.4),
                                    ("executed_steam_tph", 6.4),
                                    ("bind_feedforward", True),
                                ]
                            ),
                        ),
                        (
                            "feedforward",
                            OrderedDict(
                                [
                                    ("bound", True),
                                    ("ff_is_pv", False),
                                    ("wrong_open", True),
                                    ("t_gate_us", 6080),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 182),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 3.03),
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
            ("name", "ff_so2_open"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_tph", 6.4),
                        ("so2_tph", 16.4),
                        ("bind_feedforward", True),
                        ("ff_is_pv", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "WRONG MODIFY: feedforward SO2-load predictor is bound as PV and opens SO2 "
                "12.0 -> 16.4 t/h. Live T 94.0 remains over 88.0 and climbs. steam stays 6.4. "
                "bind_feedforward=true.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-modify / feedforward-as-feedback. Live reactor 94.0 C stayed over the "
                "88.0 cap and climbed after an SO2 open driven by a load predictor. Ten minutes "
                "of off-spec hydrosulfite dump (abort_s=600).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feedforward", "bound; SO2 open applied"),
                        ("steam", "not cut; 6.4 t/h held"),
                        ("live_tc", "96.8 C still over 88.0"),
                        ("mission", "DB-7 reactor over-temperature"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live TC winning a 182 us race did not prevent an FF MODIFY; reversing order would still have been a wrong bind if the supervisor keyed on the load predictor as PV.",
                    "Delayed (abort_s=600): 10 min off-spec hydrosulfite dump window. Named un-netted loss.",
                ],
            ),
            (
                "recovery",
                "MODIFY; cut LIVE steam 6.4 -> 3.8 t/h on the reactor-TC loop; leave SO2 at "
                "12.0 t/h; do not bind the feedforward load predictor as PV while ff_is_pv is "
                "false and live T is over cap.",
            ),
            (
                "cost",
                OrderedDict(
                    [
                        ("actual_tc_C", 94.0),
                        ("actual_cap_C", 88.0),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("so2_tph", 16.4),
                                    ("bind_feedforward", True),
                                    ("direction", "open"),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "10 min off-spec hydrosulfite dump (task/efficiency); legal steam cut "
                            "was skipped so live 94.0 stayed over 88.0 and SO2 reverse-opened (safety of a false trim).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.rx.C (5.480 ms, 94.0 C)"),
                        ("loser", "ft.so2.ff (5.662 ms, 8.4 t/h)"),
                        ("margin_us", 182),
                        (
                            "counterfactual_if_reversed",
                            "FF-first by < 182 us would still leave live 94.0 over cap; a "
                            "correct gate binds tc.rx.C to policy_fb_steam_cut either way. The "
                            "wrong MODIFY spent the live win on an FF SO2 open.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6080),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong MODIFY (6.080 ms, tick 4). "
                "The 10 min hydrosulfite miss is delayed surprise, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        30,
        92,
        30,
        83,
        routing(
            "thalamic-relay.db-tc",
            "spikenaut.policy.ff-so2-open",
            [
                ("relay_tc_live", "policy_ff_so2_open", 0.74),
                ("relay_ff_load", "policy_ff_so2_open", 0.22),
            ],
            "acetylcholine",
            0.08,
            "db_ff_as_fb_stdp; ACh tags the (wrong) ff_so2_open bind at the live-TC win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 600),
                ("delayed_surprise_s", 600),
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
                    pop("ff_so2_open", 40, 0.45, 280.0, 4),
                    pop("fb_steam_cut", 42, 0.90),
                    pop("so2_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r99-512"),
            (
                "title",
                "WRONG-MODIFY at Dithion-Beck DB-7 / Reactor R-4: live 94.0 C over cap; "
                "edit spent on feedforward SO2-load predictor (feedforward-as-feedback)",
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
                    "Wrong-modify / feedforward-as-feedback. Sidecar arithmetic live 94.0 > 88.0 "
                    "is true and ff_is_pv is false; MODIFY bound the FF load tag and opened SO2. "
                    "total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "sodium-hydrosulfite-reactor",
                    [
                        "modify",
                        "wrong-gate",
                        "feedforward-as-feedback",
                        "ff-load-as-pv",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct TC-first race can still be a wrong gate "
                    "when routing.table[0].to is policy_ff_so2_open and so2_tph rose. "
                    "Convictable from live_tc_C vs cap_tc_C without hydrosulfite chemistry.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )
