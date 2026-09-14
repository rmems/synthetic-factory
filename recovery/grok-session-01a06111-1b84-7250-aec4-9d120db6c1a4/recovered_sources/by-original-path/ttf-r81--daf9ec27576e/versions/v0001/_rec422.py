def record_422():
    ticks = [
        tick(2160, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5400, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5580, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5920, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6260, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("ft.steam.tph", 1.080, 0.42),
        spike("ft.brine.tph", 2.160, 0.57),
        spike("ft.steam.tph", 3.400, 0.49),
        spike("ft.steam.tph", 5.400, 1.29),
        spike("ft.brine.tph", 5.580, 1.10),
        spike("ctrl.gate", 5.920, 0.96),
        spike("ft.steam.tph", 8.200, 0.80),
        spike("ft.brine.tph", 10.200, 0.63),
        spike("ctrl.gate", 12.400, 0.84),
        spike("ft.steam.tph", 16.400, 0.41),
        spike("ft.brine.tph", 22.100, 0.54),
        spike("ft.steam.tph", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(81422, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Bromal-Wythe BW-7 blowout T-3 is steaming 16.8 t/h into 24.0 t/h brine "
                "(ratio 0.70 t/t, cap 0.55). The steam Coriolis is the numerator that must come "
                "down. A weak supervisor cuts the brine denominator instead, which drives the "
                "ratio further over the cap.",
            ),
            ("domain", "bromine-blowout-tower"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the BW-7 bromine blowout with steam/brine ratio <= 0.55 t/t, cut steam "
                "not brine, and leave the 24.0 t/h brine header on schedule.",
            ),
            ("t0_us", 1756850400000422),
            ("gate_latency_us", 520),
            ("race_window_us", 340),
            ("race_window_rel_ms", [5.400, 5.740]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.steam.tph 16.8 t/h LIVE numerator",
                                "ft.brine.tph 24.0 t/h LIVE denominator",
                            ],
                        ),
                        (
                            "semantics",
                            "Steam-first should latch MODIFY of the 16.8 t/h numerator; "
                            "brine-first is a false under-ratio if the 24.0 t/h denominator is cut.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live steam Coriolis slot versus the brine transmitter "
                            "on this blowout ratio pair.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (steam 28 + brine 32). Order is "
                            "correctly steam-first. The error is cutting the denominator, not the "
                            "race winner: 16.8/24.0 = 0.70 still over the 0.55 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "steam Coriolis, 2 kHz, 28 us jitter, status=LIVE",
                    "brine magnetic, 1 kHz, 32 us jitter, status=LIVE",
                    "bromine ORP (context)",
                    "air-blow FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ratio_cap", 0.55),
                        ("steam_tph", 16.8),
                        ("brine_tph", 24.0),
                        ("live_ratio", 0.70),
                        ("air_nm3h", 420.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. T-3 LIVE already steaming; steam 16.8 t/h; brine 24.0 t/h; ratio 0.70.",
                    "2. Ratio cap 0.55 t/t; steam is the numerator that must come down.",
                    "3. Steam precursor at 1.080 ms.",
                    "4. Race window [5.400, 5.740] ms.",
                    "5. ft.steam.tph 16.8 at 5.400 ms (winner).",
                    "6. ft.brine.tph 24.0 at 5.580 ms (loser by 180 us).",
                    "7. Gate at 5.920 ms: WRONG-MODIFY binds brine denominator.",
                    "8. Brine 24.0 -> 14.0 t/h; steam left at 16.8 t/h; ratio climbs to 1.20.",
                    "9. Live steam stays over the implied 13.2 t/h steam cap.",
                    "10. Delayed (abort_s=720): 12 min tower dump while T-3 is quenched.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cut_steam_numerator"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_tph", 12.0),
                        ("brine_tph", 24.0),
                        ("cut_stream", "steam"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("steam_tph", 16.8),
                        ("brine_tph", 24.0),
                        ("live_ratio", 0.70),
                        ("ratio_cap", 0.55),
                        ("implied_steam_cap_tph", 13.2),
                        ("air_nm3h", 420.0),
                        ("t_gate_us", 5920),
                        ("correct_steam_tph", 12.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes cutting steam 16.8 -> 12.0 t/h because live ratio 0.70 is over "
                "the 0.55 cap; brine 24.0 t/h is the denominator and should stay.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Brine 24.0 t/h looks high on the mimic, so trim the highlighted brine header "
                "24.0 -> 14.0 t/h. Leave steam unread as the ratio numerator.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "steam_brine_ratio",
                            OrderedDict(
                                [
                                    ("ratio_cap", 0.55),
                                    ("live_ratio", 0.70),
                                    ("executed_steam_tph", 16.8),
                                    ("executed_brine_tph", 14.0),
                                    ("executed_ratio", 1.20),
                                    ("correct_steam_tph", 12.0),
                                ]
                            ),
                        ),
                        (
                            "stream_bind",
                            OrderedDict(
                                [
                                    ("t_gate_us", 5920),
                                    ("cut_stream", "brine"),
                                    ("wrong_stream", True),
                                    ("numerator", "steam"),
                                    ("denominator", "brine"),
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
            ("name", "brine_cut_wrong_stream"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_tph", 16.8),
                        ("brine_tph", 14.0),
                        ("cut_stream", "brine"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / ratio-wrong-stream): 14.0 t/h brine cut applied because the "
                "denominator was bound. Routing relay.ft.brine -> policy.brine_cut; no positive "
                "weight to policy.steam_cut.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY clamped the brine denominator. Live steam 16.8 t/h over the 13.2 "
                "implied cap at t_gate; brine 24.0 t/h was the ratio partner. Ratio climbed to "
                "1.20 and dumped bromine. 12 min tower dump (abort_s=720). Correct gate was "
                "MODIFY steam 16.8 -> 12.0 t/h at t_gate_us=5920.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("steam", "left 16.8 t/h over the implied 13.2 cap"),
                        ("brine", "cut 24.0 -> 14.0 t/h on the denominator"),
                        ("dump", "12 min bromine dump, T-3 quench"),
                        ("mission", "blowout deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Steam-first was the correct order and the ratio was over cap; the MODIFY spent that win on the brine denominator.",
                    "Delayed (abort_s=720): BW-7 holds 12 min while T-3 is dumped and restacked; next brine 14 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY steam 16.8 -> 12.0 t/h at t_gate_us=5920; cut_stream=steam; leave brine at 24.0 t/h.",
                        ),
                        ("correct_actuator", "T-3_steam_tph"),
                        ("wrong_stream", "brine denominator"),
                        ("t_gate_us", 5920),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("steam_tph", 16.8),
                                    ("brine_tph", 14.0),
                                    ("cut_stream", "brine"),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min bromine dump (task/efficiency); legal steam cut was skipped because the brine denominator was bound as the ratio MV.",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.steam.tph (5.400 ms, 16.8 t/h LIVE numerator)"),
                        ("loser", "ft.brine.tph (5.580 ms, 24.0 t/h LIVE denominator)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Brine-first by < 180 us would still be 24.0 t/h on the denominator; "
                            "a correct gate binds ft.steam.tph to policy.steam_cut at t_gate "
                            "either way. The wrong MODIFY spent the steam win on a "
                            "ratio-wrong-stream clamp.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5920),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong-stream bind (5.920 ms, tick 4). "
                "The 12 min tower dump is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 720),
        ]
    )
    dw = 0.34
    ras = raster_core(
        28,
        88,
        34,
        84,
        routing(
            "thalamic-relay.br2-ratio",
            "spikenaut.policy.wrong-stream-cut",
            [
                ("relay.ft.brine", "policy.brine_cut", 0.74),
                ("relay.ft.steam", "policy.brine_cut", 0.21),
            ],
            "acetylcholine",
            0.08,
            "ratio_cap_stdp; ACh tags the (wrong) brine_cut bind at the steam win",
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
                    pop_budget("brine_cut", 48, 0.45, 300.0, dw),
                    pop("steam_cut", 48, 0.90),
                    pop("ratio_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r81-422"),
            (
                "title",
                "WRONG-MODIFY at Bromal-Wythe BW-7 / Tower T-3: live steam/brine 0.70 over 0.55; "
                "14.0 t/h cut applied on the brine denominator (ratio-wrong-stream)",
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
                    "Wrong-modify / ratio-wrong-stream. Sidecar arithmetic 0.70 > 0.55 on live "
                    "ratio is true; MODIFY bound to brine_cut. total -0.68 = -0.22 + -0.24 + "
                    "-0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "bromine-blowout-tower",
                    [
                        "modify",
                        "wrong-gate",
                        "ratio-wrong-stream",
                        "numerator-vs-denominator",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct steam-first race can still be a wrong gate "
                    "when the MODIFY clamps the brine denominator of a steam/brine ratio. "
                    "Convictable from live_ratio vs cap, cut_stream, and routing without "
                    "bromine-blowout physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )
