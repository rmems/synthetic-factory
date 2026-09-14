def record_521():
    excerpt, extra = lif_521_excerpt()
    ticks = [
        tick(2080, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5200, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5380, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5900, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22400, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    spikes = [
        spike("pt.bath.V", 1.040, 0.41),
        spike("sc.mist.vol", 2.080, 0.58),
        spike("pt.bath.V", 3.400, 0.50),
        spike("sc.mist.vol", 5.200, 1.31),
        spike("pt.bath.V", 5.380, 1.12),
        spike("ctrl.gate", 5.900, 0.97),
        spike("sc.mist.vol", 8.100, 0.82),
        spike("pt.bath.V", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.crust.snap", 22.400, 1.48),
        spike("ae.crust.snap", 24.100, 0.93),
        spike("pt.bath.V", 30.200, 0.40),
        spike("sc.mist.vol", 36.400, 0.55),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Cell SC-9 at Scandyl-Cleugh SC-4 is driving 16.8 kA through a ScCl3 melt while "
                "optical mist sits at 7.8 vol percent against a 5.5 license. Mist-first cuts current "
                "16.8 kA to 10.2; a bath-voltage-first cruise would keep 16.8 kA because 3.7 V still "
                "looks under a 4.9 V idle envelope. Cathode crust already seated on the freeze ring "
                "does not appear on mist or bath V until the AE dump.",
            ),
            ("domain", "scandium-chloride-electrolyzer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep SC-9 optical mist <= 5.5 vol percent and finish the Sc metal pass without "
                "dumping freeze-ring crust into the melt.",
            ),
            ("t0_us", 1756850400000521),
            ("gate_latency_us", 700),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.200, 5.560]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "sc.mist.vol 7.8 over 5.5 cap",
                                "pt.bath.V 3.7 with header under 4.9",
                            ],
                        ),
                        (
                            "semantics",
                            "Mist-first latches current clamp 16.8 -> 10.2 kA; bath-first keeps 16.8 "
                            "on a 'still under idle-voltage look' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one optical-mist slot versus the bath-voltage PT publisher on this "
                            "ScCl3-cell bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (mist 28 + bath 34): 2.90x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 16.8 kA; predicted next-sample 6.6 vol "
                            "percent > 5.5 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "optical mist cell, 2 kHz, 28 us jitter",
                    "bath-voltage PT, 1 kHz, 34 us jitter",
                    "cathode-crust AE puck (context)",
                    "ScCl3 melt Coriolis (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("mist_cap_vol_pct", 5.5),
                        ("observed_mist_vol_pct", 7.8),
                        ("cell_kA", 16.8),
                        ("bath_V", 3.7),
                        ("bath_cap_V", 4.9),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. SC-9 indexed on Scandyl-Cleugh SC-4; current 16.8 kA; optical mist 7.8 vol percent.",
                    "2. Bath 3.7 V under 4.9 cap; Sc metal pass armed.",
                    "3. Bath-voltage PT precursor at 1.040 ms.",
                    "4. Race window [5.200, 5.560] ms.",
                    "5. sc.mist.vol 7.8 at 5.200 ms (winner).",
                    "6. pt.bath.V 3.7 at 5.380 ms (loser by 180 us).",
                    "7. Gate at 5.900 ms: MODIFY clamp current 16.8 -> 10.2 kA.",
                    "8. After clamp mist 5.1 vol percent <= 5.5; bath still 3.7 V.",
                    "9. At 22.400 ms a cathode-crust snap dumps 0.4 t ScCl3 freeze-ring.",
                    "10. 15 min crust isolate (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_sc_current"),
            (
                "parameters",
                OrderedDict(
                    [("cell_kA", 16.8), ("mist_vol_pct", 7.8), ("bath_V", 3.7)]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("mist_vol_pct", 7.8),
                        ("mist_cap_vol_pct", 5.5),
                        ("predicted_unclamped_next_vol_pct", 6.6),
                        ("cell_kA", 16.8),
                        ("bath_V", 3.7),
                        ("bath_cap_V", 4.9),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 16.8 kA because bath 3.7 V is under 4.9, treating "
                "the 7.8 vol percent mist as a still-fogged optic rather than an off-gas-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Optical mist 7.8 vol percent won by 180 us, so the cell is off-spec, not still "
                "a bath-voltage story. Holding 16.8 kA predicts next-sample 6.6 vol percent > 5.5 "
                "cap. MODIFY: current 16.8 -> 10.2 kA. Observed after clamp 5.1 vol percent <= 5.5. "
                "A full REJECT is not indicated: a clean Sc pass accepts 10.2 kA.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "mist_vol_pct",
                            OrderedDict(
                                [
                                    ("cap", 5.5),
                                    ("observed", 7.8),
                                    ("predicted_unclamped_next", 6.6),
                                    ("clamped_cell_kA", 10.2),
                                    ("observed_after_clamp", 5.1),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 180), ("combined_jitter_us", 62), ("ratio", 2.9)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "clamped_sc_current"),
            (
                "parameters",
                OrderedDict(
                    [("cell_kA", 10.2), ("mist_vol_pct", 5.1), ("bath_V", 3.7)]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: current 16.8 -> 10.2 kA. Process-correct vs the 5.5 vol percent mist cap. "
                "Crust still snaps at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held optical mist at 5.1 vol percent. At 22.400 ms a crust "
                "already seated on the freeze ring dumped 0.4 t of ScCl3. Clamp reduced dump "
                "energy; it did not prevent the snap. Partnered negative: process heads stay "
                "honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("mist", "clamp executed; peak 5.1 vol percent <= 5.5 cap"),
                        ("crust", "snapped at 22.400 ms; 0.4 t ScCl3"),
                        ("repair", "15 min crust isolate (abort_s=900)"),
                        ("mission", "SC-4 Sc pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither optical mist nor bath PT predicted the seated cathode crust; ae.crust.snap is a new channel at 22.400 ms, 16.500 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min crust isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min crust isolate after the cathode-crust snap. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the current clamp completed under the 5.5 vol "
                "percent cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "sc.mist.vol (5.200 ms, 7.8 vol percent)"),
                        ("loser", "pt.bath.V (5.380 ms, 3.7 V)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Bath-first by < 180 us inside the 360 us window would have kept "
                            "16.8 kA; predicted next-sample 6.6 vol percent would have missed "
                            "the 5.5 cap even without the snap. The MODIFY is still the correct "
                            "process. The snap is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms cathode-crust snap (tick t_us=22400), inside the "
                "42 ms raster. The correct MODIFY at 5.900 ms is in the same excerpt. Do not "
                "put inflection on the abort_s=900 isolation tick.",
            ),
            ("delayed_surprise_s", 900),
        ]
    )
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.sc-mist",
            "spikenaut.policy.ka-clamp",
            [
                ("relay.sc.mist", "policy.ka_clamp", 0.68),
                ("relay.pt.bath", "policy.header_hold", 0.29),
                ("relay.ae.crust", "policy.ka_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at mist win (5.200 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.400 ms cathode-crust snap",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("ka_clamp", 50, 0.5, 220.0, 0.36),
                    pop_budget("header_hold", 40, 0.8, 50.0, 0.36),
                    pop("crust_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r101-521",
        "Scandyl-Cleugh SC-4 / Cell SC-9: optical mist beats bath voltage by 180 us; correct "
        "MODIFY still eats an in-window cathode-crust snap (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the 42 ms "
        "raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named crust isolate "
        "(abort_s=900) is not netted into task_progress.",
        ras,
        gate,
        "scandium-chloride-electrolyzer",
        [
            "modify",
            "partnered-negative-total",
            "independent-lif-raster",
            "sidecar-sim-only",
            "in-window-world-charge",
            "designed",
        ],
        "A critic can see the world-charge as a LIF burst inside the raster while process "
        "heads stay honest. Credit assignment is spikes, not prose across a 15 min crust isolate.",
        1,
    )


def record_522():
    ticks = [
        tick(2240, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5600, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5780, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6120, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6460, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("ft.steam.ff", 1.120, 0.42),
        spike("dens.cs.fb", 2.240, 0.57),
        spike("ft.steam.ff", 3.500, 0.49),
        spike("dens.cs.fb", 5.600, 1.29),
        spike("ft.steam.ff", 5.780, 1.10),
        spike("ctrl.gate", 6.120, 0.96),
        spike("dens.cs.fb", 8.400, 0.80),
        spike("ft.steam.ff", 10.400, 0.63),
        spike("ctrl.gate", 12.600, 0.84),
        spike("dens.cs.fb", 16.600, 0.41),
        spike("ft.steam.ff", 22.200, 0.54),
        spike("dens.cs.fb", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(101522, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "DTB C-4 at Cesial-Swang CW-7 still prints live feedback mother-liquor cesium at "
                "91.0 g/L against a 75.0 g/L cap, while the steam feedforward tag sits at 5.8 t/h "
                "under an 8.5 t/h load look. Feedback-first must cut steam 5.8 -> 4.1 t/h so liquor "
                "falls. A weak supervisor binds the feedforward tag as if it were the PV, reads "
                "headroom under 8.5, and MODIFY-opens steam 5.8 -> 10.4 t/h.",
            ),
            ("domain", "cesium-alum-crystallizer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the CW-7 cesium-alum pass with live liquor Cs <= 75.0 g/L by cutting "
                "evaporation on the LIVE feedback densitometer; do not bind the steam feedforward tag as PV.",
            ),
            ("t0_us", 1756850400000522),
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
                                "dens.cs.fb 91.0 g/L on LIVE feedback liquor",
                                "ft.steam.ff 5.8 t/h on LIVE feedforward steam",
                            ],
                        ),
                        (
                            "semantics",
                            "Feedback-first should MODIFY-cut steam on the live liquor EU; "
                            "feedforward-first is a false 'FF is the PV' bind that opens steam.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live liquor-Cs densitometer slot versus the steam-FF publisher "
                            "on this DTB PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (fb 28 + ff 32). Order is "
                            "correctly feedback-first. The error is pairing: FF is not the PV, but "
                            "the edit opens steam while liquor stays over 75.0 g/L.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live mother-liquor Cs densitometer on C-4, 2 kHz, 28 us jitter, tag=C4_CS.FB status=LIVE role=feedback",
                    "steam feedforward FT on C-4, 1 kHz, 32 us jitter, tag=C4_STM.FF status=LIVE role=feedforward",
                    "DTB body PT (context)",
                    "alum crystal Coriolis (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_fb_g_L", 75.0),
                        ("live_fb_g_L", 91.0),
                        ("ff_steam_tph", 5.8),
                        ("ff_look_tph", 8.5),
                        ("ff_is_pv", False),
                        ("bound_tag", "none"),
                        ("fb_status", "LIVE"),
                        ("ff_status", "LIVE"),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. C-4 LIVE; liquor Cs 91.0 g/L; steam FF 5.8 t/h; FB over cap; FF under look.",
                    "2. Caps: liquor 75.0 g/L; steam look 8.5 t/h; FF is not PV.",
                    "3. Steam FF precursor at 1.120 ms.",
                    "4. Race window [5.600, 5.940] ms.",
                    "5. dens.cs.fb 91.0 at 5.600 ms (winner).",
                    "6. ft.steam.ff 5.8 at 5.780 ms (loser by 180 us).",
                    "7. Gate at 6.120 ms: WRONG-MODIFY binds the feedforward tag as PV.",
                    "8. Steam 5.8 -> 10.4 t/h; liquor climbs; Cs stays over 75.0.",
                    "9. Live liquor stays 91.0 then 117.2 > 75.0; C-4 dumps alum.",
                    "10. Delayed (abort_s=720): 12 min off-spec cesium-alum dump.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_cs_ff_fb"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_tph", 5.8),
                        ("liquor_g_L", 91.0),
                        ("bound_tag", "none"),
                        ("ff_is_pv", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_fb_g_L", 91.0),
                        ("cap_fb_g_L", 75.0),
                        ("ff_steam_tph", 5.8),
                        ("ff_look_tph", 8.5),
                        ("ff_is_pv", False),
                        ("fb_status", "LIVE"),
                        ("ff_status", "LIVE"),
                        ("fb_tag", "dens.cs.fb"),
                        ("ff_tag", "ft.steam.ff"),
                        ("correct_steam_tph", 4.1),
                        ("correct_liquor_g_L", 68.0),
                        ("correct_gate", "MODIFY"),
                        ("t_gate_us", 6120),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping 5.8 t/h steam because the feedforward tag already looks "
                "'under 8.5', treating the live 91.0 g/L densitometer as a header smear.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Liquor 91.0 g/L exceeds the 75.0 cap, so a cut is required, but the highlighted "
                "stem is the steam feedforward FT. Open steam 5.8 -> 10.4 t/h because 5.8 looks "
                "under 8.5. Leave the feedback densitometer unused as PV.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "liquor_cs",
                            OrderedDict(
                                [
                                    ("cap_fb_g_L", 75.0),
                                    ("live_fb_g_L", 91.0),
                                    ("executed_steam_tph", 10.4),
                                    ("executed_liquor_g_L", 117.2),
                                    ("correct_steam_tph", 4.1),
                                    ("correct_gate", "MODIFY"),
                                ]
                            ),
                        ),
                        (
                            "ff_fb_pair",
                            OrderedDict(
                                [
                                    ("t_gate_us", 6120),
                                    ("bound_tag", "feedforward"),
                                    ("ff_is_pv", False),
                                    ("ff_open", True),
                                    ("fb_status", "LIVE"),
                                    ("ff_status", "LIVE"),
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
            ("name", "ff_steam_open"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_tph", 10.4),
                        ("liquor_g_L", 117.2),
                        ("bound_tag", "feedforward"),
                        ("ff_is_pv", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / feedforward-as-feedback): steam opened 5.8 -> 10.4 t/h because "
                "the FF tag was bound as PV. Routing relay.ft.steam -> policy.ff_open; no positive "
                "weight to policy.fb_cut. Live liquor stays over 75.0 g/L and climbs.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY opened steam on a cesium-alum DTB that needed a feedback cut. "
                "Live 91.0 g/L was over the 75.0 cap at t_gate; FF is not PV. "
                "12 min off-spec dump (abort_s=720). Correct gate was MODIFY; cut steam "
                "5.8 -> 4.1 t/h at t_gate_us=6120 and bind the live densitometer.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live_fb", "C-4 left illegal at 91.0 then 117.2 g/L"),
                        ("ff_leg", "steam opened 5.8 -> 10.4 t/h on the feedforward tag"),
                        ("dump", "12 min off-spec alum dump, C-4 over cap"),
                        ("mission", "cesium-alum crop deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Feedback-first was the correct order and live liquor was over cap; the MODIFY spent that win on the steam feedforward tag.",
                    "Delayed (abort_s=720): CW-7 holds 12 min while C-4 is dumped and recharged; next crop 14 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY; cut live C-4 steam 5.8 -> 4.1 t/h at t_gate_us=6120; bound_tag=feedback; ff_is_pv=false; do not open steam because the FF tag is under its look.",
                        ),
                        ("correct_actuator", "C-4_cs_feedback"),
                        ("wrong_ff_leg", "C-4_steam_feedforward"),
                        ("t_gate_us", 6120),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("steam_tph", 10.4),
                                    ("bound_tag", "feedforward"),
                                    ("ff_open", True),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min off-spec cesium-alum dump (task/efficiency); live liquor never returned under 75.0 g/L while the edit opened the feedforward steam.",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "dens.cs.fb (5.600 ms, 91.0 g/L liquor)"),
                        ("loser", "ft.steam.ff (5.780 ms, 5.8 t/h)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Steam-first by < 180 us would still be 5.8 t/h on a legal FF look; "
                            "a correct gate binds dens.cs.fb to policy.fb_cut at t_gate either "
                            "way. The wrong MODIFY spent the live win on a feedforward-as-feedback open.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6120),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the FF-open bind (6.120 ms, tick 4). "
                "The 12 min alum dump is delayed surprise, not the inflection.",
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
            "thalamic-relay.cs-ff-as-fb",
            "spikenaut.policy.ff-open",
            [
                ("relay.ft.steam", "policy.ff_open", 0.74),
                ("relay.dens.cs", "policy.ff_open", 0.21),
            ],
            "acetylcholine",
            0.08,
            "ff_as_fb_stdp; ACh tags the (wrong) steam-FF open at the live densitometer win",
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
                    pop_budget("ff_open", 48, 0.45, 300.0, 0.34),
                    pop("fb_cut", 48, 0.90),
                    pop("fb_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r101-522",
        "WRONG-MODIFY at Cesial-Swang CW-7 / DTB C-4: live 91.0 g/L Cs over 75.0 cap; "
        "steam opened 5.8 -> 10.4 t/h on the feedforward tag (feedforward-as-feedback)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-modify / feedforward-as-feedback. Sidecar arithmetic 91.0 > 75.0 on live liquor is "
        "true; MODIFY bound to ff_open. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
        ras,
        gate,
        "cesium-alum-crystallizer",
        [
            "modify",
            "wrong-gate",
            "feedforward-as-feedback",
            "ff-open",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live-FB-first race can still be a wrong gate when the "
        "MODIFY opens the steam feedforward tag as if it were the PV. Convictable "
        "from live_fb_g_L vs cap, executed steam vs liquor, and routing without cesium chemistry.",
        2,
        supervisor_error_type="wrong-modify",
    )
