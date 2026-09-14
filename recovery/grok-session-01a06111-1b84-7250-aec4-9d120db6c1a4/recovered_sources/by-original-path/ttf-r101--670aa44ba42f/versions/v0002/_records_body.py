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


def record_523():
    ticks = [
        tick(2736, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6840, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7020, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7640, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(7960, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.cake.kg", 1.360, 0.40),
        spike("ae.ppt.pps", 2.736, 0.56),
        spike("enc.cake.kg", 4.100, 0.48),
        spike("ae.ppt.pps", 6.840, 1.34),
        spike("enc.cake.kg", 7.020, 1.11),
        spike("ctrl.gate", 7.640, 0.98),
        spike("ae.ppt.pps", 10.400, 0.81),
        spike("enc.cake.kg", 14.800, 0.62),
        spike("ctrl.gate", 18.200, 0.84),
        spike("ae.ppt.pps", 28.400, 0.52),
        spike("enc.cake.kg", 36.100, 0.39),
        spike("ae.ppt.pps", 42.200, 0.44),
    ]
    excerpt = independent_excerpt(101523, 120, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Precipitator YP-2 on the Yttriox-Laggan YL-HIL pad is throwing 54 acoustic pulses "
                "each second while the quiet license is 14. Cake encoder 2.8 kg is still 4.2 kg short "
                "of the 7.0 kg travel look, so a mass-trusting supervisor would release the 0.24 kg/h "
                "oxalate raise. Only a REJECT that freezes the screw is legal; the mockup's encoder "
                "lamp is not a license to grind a noisy nucleator.",
            ),
            ("domain", "yttrium-oxalate-precipitator"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep YP-2 from dispatching a growling nucleator while cake mass remains under "
                "its own travel look.",
            ),
            ("t0_us", 1756850400000523),
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
                                "ae.ppt.pps 54 over 14 cap",
                                "enc.cake.kg 2.8 under 7.0 look",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; encoder-first dispatches 0.24 kg/h oxalate on a 'kg still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one AE puck slot versus the cake-encoder publisher on this HIL oxalate-precipitator bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + ENC 32): 3.10x over a "
                            "2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have dispatched 0.24 kg/h oxalate into a growling nucleator.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "nucleator AE puck, 50 kHz, 26 us jitter",
                    "cake mass encoder, 1 kHz, 32 us jitter",
                    "oxalate-feed encoder (context)",
                    "liquor TC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 14.0),
                        ("observed_ae_pps", 54.0),
                        ("cake_kg", 2.8),
                        ("cake_look_kg", 7.0),
                        ("proposed_oxalate_kg_h", 0.24),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        (
                            "pad",
                            "Yttriox-Laggan YL-HIL yttrium-oxalate precipitator mockup with physical cake screw",
                        ),
                        ("injected", "nucleator AE burst + encoder lamp spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop yttrium oxalate precipitator. Invented plant; not a live rare-earth shop.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. YP-2 HIL indexed; 0.24 kg/h oxalate raise armed.",
                    "2. Cake 2.8 kg under 7.0; AE 54 pps over 14.",
                    "3. Encoder precursor at 1.360 ms.",
                    "4. Race window [6.840, 7.160] ms.",
                    "5. ae.ppt.pps 54 at 6.840 ms (winner).",
                    "6. enc.cake.kg 2.8 at 7.020 ms (loser by 180 us).",
                    "7. Gate at 7.640 ms: REJECT hold, do not raise.",
                    "8. Oxalate 0 kg/h; cake left at 2.8 kg.",
                    "9. Nucleator inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min precipitator reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "raise_oxalate"),
            (
                "parameters",
                OrderedDict([("oxalate_kg_h", 0.24), ("hold", False), ("cake_kg", 2.8)]),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 54.0),
                        ("ae_cap_pps", 14.0),
                        ("cake_kg", 2.8),
                        ("cake_look_kg", 7.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.24 kg/h oxalate because cake 2.8 kg is under 7.0, treating the 54 pps AE "
                "as lamp hash rather than a growling nucleator.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Nucleator AE 54 pps won by 180 us, so the precipitator is growling, not still "
                "a cake-mass story. 2.8 kg is under 7.0 and does not authorize a raise. REJECT: "
                "hold oxalate 0.24 -> 0 kg/h. A MODIFY that only trims kg would leave the growl.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ae_pps",
                            OrderedDict(
                                [
                                    ("cap", 14.0),
                                    ("observed", 54.0),
                                    ("executed_oxalate_kg_h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 180), ("combined_jitter_us", 58), ("ratio", 3.1)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_precipitator"),
            (
                "parameters",
                OrderedDict([("oxalate_kg_h", 0.0), ("hold", True), ("cake_kg", 2.8)]),
            ),
            (
                "gate_effect",
                "REJECT: oxalate 0.24 -> 0 kg/h. Cake mass left at 2.8 kg under its own look.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held YP-2. AE 54 pps beat cake 2.8 kg by 180 us. Mass was legal; "
                "the nucleator was not. 8 min precipitator reset (abort_s=480) is delayed survey, not a "
                "process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("oxalate", "held at 0 kg/h"),
                        ("cake", "left 2.8 kg < 7.0 look"),
                        ("nucleator", "8 min precipitator reset (abort_s=480)"),
                        ("mission", "HIL raise not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Cake encoder never crossed its look; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min precipitator reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.ppt.pps (6.840 ms, 54 pps)"),
                        ("loser", "enc.cake.kg (7.020 ms, 2.8 kg)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 180 us inside the 320 us window would have "
                            "dispatched 0.24 kg/h oxalate into a growling nucleator. The REJECT is still "
                            "the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7640),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.640 ms, tick 4). The 8 min precipitator "
                "reset is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    ras = raster_core(
        46,
        120,
        20,
        110,
        routing(
            "thalamic-relay.yt-ae",
            "spikenaut.policy.ppt-hold",
            [
                ("relay.ae.ppt", "policy.ppt_hold", 0.70),
                ("relay.enc.cake", "policy.kg_go", 0.24),
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
            ("decision_window_ms", 0.32),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop_budget("ppt_hold", 56, 0.45, 280.0, 0.32),
                    pop("kg_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r101-523",
        "Yttriox-Laggan YL-HIL / Precipitator YP-2: nucleator AE 54 pps beats cake encoder 2.8 kg by 180 us; "
        "correct REJECT holds the oxalate raise",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 54 > 14 cap beats legal cake mass. total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "yttrium-oxalate-precipitator",
        ["reject", "hil", "ae-vs-kg", "growling-nucleator", "tick6-sidecar-bound"],
        "Teaches that a legal cake-encoder look can lose to nucleator AE inside a 320 us "
        "window; reversing 180 us would have dispatched a growling oxalate precipitator.",
        3,
    )


def record_524():
    ticks = [
        tick(2880, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7200, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7380, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7840, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8200, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.bowl.C", 1.200, 0.40),
        spike("wt.pipe.pct", 2.880, 0.55),
        spike("tc.bowl.C", 4.400, 0.48),
        spike("wt.pipe.pct", 7.200, 1.26),
        spike("tc.bowl.C", 7.380, 1.08),
        spike("ctrl.gate", 7.840, 0.95),
        spike("wt.pipe.pct", 11.200, 0.78),
        spike("tc.bowl.C", 14.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("wt.pipe.pct", 22.600, 0.50),
        spike("tc.bowl.C", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(101524, 48, 28000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("recycle_tph", 4.6),
            ("pipe_wt_pct", 9.6),
            ("bowl_C", 41.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Piperaz-Lyth's simulated PX-8 piperazine cropper reports mother-liquor assay "
                "9.6 wt percent against a 14.0 flood stop, bowl metal 41 C versus 88 C, vacuum 16 kPa "
                "versus 22. Filed 4.6 t/h recycle sits inside every cap; promoting bowl IR over "
                "liquor assay would idle a dry crystallizer.",
            ),
            ("domain", "piperazine-crystallizer"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the PX-8 crystallization pass with mother liquor <= 14.0 wt percent and bowl <= 88 C.",
            ),
            ("t0_us", 1756850400000524),
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
                                "wt.pipe.pct 9.6 under 14.0 trip",
                                "tc.bowl.C 41 under 88 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Assay-first confirms the already-legal 4.6 t/h recycle; bowl-first "
                            "would have treated the densitometer as a climb echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one liquor-assay slot versus the bowl-TC publisher on this simulated piperazine-crystallizer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (assay 26 + TC 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed recycle illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "NIR assay on mother liquor, 26 us jitter",
                    "bowl TC well, 32 us jitter",
                    "recycle Coriolis (context)",
                    "delta-P bed (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("pipe_cap_wt_pct", 14.0),
                        ("observed_pipe_wt_pct", 9.6),
                        ("bowl_cap_C", 88.0),
                        ("observed_bowl_C", 41.0),
                        ("vacuum_kPa", 16.0),
                        ("vacuum_cap_kPa", 22.0),
                        ("proposed_recycle_tph", 4.6),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "unstructured MSMPR + NIR assay mixer, seed 101524; "
                            "8-zone cooled piperazine tank; NOT lumped-CSTR, NOT U-RANS, NOT a wet-stand",
                        ),
                        (
                            "fidelity_limits",
                            "Rigid vessel shell; no impeller flex. Raster is kernelized "
                            "events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. PX-8 indexed on Piperaz-Lyth PL-3; 4.6 t/h recycle armed.",
                    "2. Caps: mother liquor 14.0 wt percent, bowl 88 C, vacuum 22 kPa.",
                    "3. Bowl TC precursor at 1.200 ms.",
                    "4. Race window [7.200, 7.560] ms.",
                    "5. wt.pipe.pct 9.6 at 7.200 ms (winner).",
                    "6. tc.bowl.C 41 at 7.380 ms (loser by 180 us).",
                    "7. Gate at 7.840 ms: ACCEPT 4.6 t/h already legal.",
                    "8. Recycle continues; no extra hold.",
                    "9. 6 min survey confirms mother liquor still under 14.0 wt percent.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "feed_pz_4p6"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("pipe_wt_pct", 9.6),
                        ("pipe_cap_wt_pct", 14.0),
                        ("bowl_C", 41.0),
                        ("bowl_cap_C", 88.0),
                        ("vacuum_kPa", 16.0),
                        ("vacuum_cap_kPa", 22.0),
                        ("recycle_tph", 4.6),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 4.6 t/h recycle because mother liquor 9.6 wt percent is under 14.0 and bowl "
                "41 C is under 88 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Mother-liquor assay 9.6 wt percent won by 180 us and is under 14.0. Bowl 41 C is under 88 C. "
                "Vacuum 16 kPa is under 22. ACCEPT the already-legal recycle.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "pipe_wt_pct",
                            OrderedDict(
                                [
                                    ("cap", 14.0),
                                    ("observed", 9.6),
                                    ("executed_recycle_tph", 4.6),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 180), ("combined_jitter_us", 58), ("ratio", 3.1)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "feed_pz_4p6"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 4.6 t/h recycle and 9.6 wt percent mother liquor unchanged. Routing relay.wt.pipe -> policy.pipe_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left PX-8 on a 4.6 t/h / 9.6 wt percent mother-liquor recycle. Bowl TC hitch did "
                "not justify a hold. 6 min survey confirmed liquor still under 14.0 wt percent.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "still 4.6 t/h recycle"),
                        ("assay", "9.6 wt percent under 14.0 trip"),
                        ("bowl", "41 C under 88"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Bowl TC 41 C hitch is residual, not a runaway trip.",
                    "Delayed (survey_s=360): 6 min survey restacks PX-8 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "wt.pipe.pct (7.200 ms, 9.6 wt percent)"),
                        ("loser", "tc.bowl.C (7.380 ms, 41 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Bowl-first by < 180 us would only delay confirmation. The recycle "
                            "stays legal either way; ACCEPT is still required.",
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
    ras = raster_core(
        28,
        48,
        42,
        56,
        routing(
            "thalamic-relay.pz-assay",
            "spikenaut.policy.pipe-go",
            [
                ("relay.wt.pipe", "policy.pipe_go", 0.68),
                ("relay.tc.bowl", "policy.bowl_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_pz_stdp; 5-HT tags the pipe_go bind at the assay win",
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
            ("decision_window_ms", 0.36),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("pipe_go", 40, 0.45, 250.0, 0.36),
                    pop("bowl_hold", 32, 0.90),
                    pop("pipe_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r101-524",
        "Piperaz-Lyth PL-3 / Crystallizer PX-8: mother liquor 9.6 wt percent beats bowl 41 C by 180 us; ACCEPT "
        "already-legal 4.6 t/h recycle",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal piperazine recycle. total +1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "piperazine-crystallizer",
        [
            "accept",
            "already-legal",
            "simulated-pz-crystallizer",
            "assay-vs-tc",
            "sidecar-convictable",
            "simulated",
        ],
        "Teaches that a mother-liquor assay under trip can confirm an already-legal recycle "
        "without a bowl-TC hitch becoming a hold.",
        4,
    )


def record_525():
    ticks = [
        tick(2016, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5040, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5920, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(240000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.decene.tph", 0.980, 0.41),
        spike("tc.oligo.C", 2.016, 0.60),
        spike("enc.decene.tph", 3.200, 0.51),
        spike("tc.oligo.C", 5.040, 1.30),
        spike("enc.decene.tph", 5.200, 1.12),
        spike("ctrl.gate", 5.640, 0.97),
        spike("tc.oligo.C", 8.100, 0.78),
        spike("enc.decene.tph", 12.400, 0.62),
        spike("ctrl.gate", 16.200, 0.85),
        spike("tc.oligo.C", 20.400, 0.54),
        spike("enc.decene.tph", 22.800, 0.43),
    ]
    excerpt = independent_excerpt(101525, 80, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("decene_tph", 3.4),
            ("oligo_C", 94.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Decene-Fold DF-5 autoclave O-8 is mid-cut at 94 C oligomer, 31 K under the 125 C freeze, "
                "1-decene encoder 3.4 t/h versus a 6.0 t/h feed cap. Keeping 3.4 t/h PAO make is lawful; "
                "a jacket-led stop would shutter a quiet oligomer stack.",
            ),
            ("domain", "decene-pao-oligomer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run O-8 at 3.4 t/h 1-decene, keep oligomer <= 125 C and feed <= 6.0 t/h, and leave "
                "the freeze on schedule.",
            ),
            ("t0_us", 1756850400000525),
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
                                "tc.oligo.C 94 under 125 cap",
                                "enc.decene.tph 3.4 under 6.0 trip",
                            ],
                        ),
                        (
                            "semantics",
                            "Temp-first confirms the already-legal 3.4 t/h 1-decene; feed-first would "
                            "have treated the oligomer TC as a hitch echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one oligomer-TC slot versus the decene-encoder publisher on this PAO autoclave bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (TC 22 + enc 30): 3.08x over a "
                            "2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal 3.4 t/h PAO run.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "oligomer TC well, 2 kHz, 22 us jitter",
                    "1-decene encoder, 1 kHz, 30 us jitter",
                    "PAO Coriolis (context)",
                    "nitrogen header PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("oligo_cap_C", 125.0),
                        ("observed_oligo_C", 94.0),
                        ("decene_tph", 3.4),
                        ("decene_cap_tph", 6.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Autoclave O-8 indexed on Decene-Fold DF-5; 3.4 t/h 1-decene armed.",
                    "2. Oligomer 94 C under 125; feed 3.4 t/h under 6.0.",
                    "3. Decene precursor at 0.980 ms.",
                    "4. Race window [5.040, 5.320] ms.",
                    "5. tc.oligo.C 94 at 5.040 ms (winner).",
                    "6. enc.decene.tph 3.4 at 5.200 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 3.4 t/h.",
                    "8. Oligomer stays 94 C; feed stays 3.4 t/h.",
                    "9. PAO make on-spec.",
                    "10. Delayed (dwell_s=240): 4 min autoclave reseq.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_decene_tph"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("oligo_C", 94.0),
                        ("oligo_cap_C", 125.0),
                        ("decene_tph", 3.4),
                        ("decene_cap_tph", 6.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 3.4 t/h 1-decene because oligomer 94 C is under 125 and feed 3.4 t/h "
                "is under 6.0.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Oligomer TC 94 C won by 160 us, so the autoclave is already legal, not still climbing. "
                "Feed 3.4 t/h is under 6.0. ACCEPT the 3.4 t/h PAO run. A REJECT would idle a legal oligomer stack.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "oligo_C",
                            OrderedDict(
                                [
                                    ("cap", 125.0),
                                    ("observed", 94.0),
                                    ("executed_decene_tph", 3.4),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 160), ("combined_jitter_us", 52), ("ratio", 3.08)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_decene_tph"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: leave 3.4 t/h 1-decene; oligomer 94 C; feed legal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 3.4 t/h 1-decene feed. Oligomer 94 C beat feed "
                "3.4 t/h by 160 us. 4 min autoclave reseq (dwell_s=240) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "3.4 t/h 1-decene held"),
                        ("oligo", "94 C < 125 cap"),
                        ("autoclave", "O-8 on-spec"),
                        ("reseq", "4 min autoclave reseq (dwell_s=240)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Feed never approached 6.0 t/h; oligomer was already under cap.",
                    "Delayed (dwell_s=240): 4 min autoclave reseq after takeoff.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.oligo.C (5.040 ms, 94 C)"),
                        ("loser", "enc.decene.tph (5.200 ms, 3.4 t/h)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Feed-first by < 160 us inside the 280 us window would have "
                            "REJECTED an already-legal 3.4 t/h PAO run. ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5640),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (5.640 ms, tick 4). The 4 min autoclave reseq "
                "is delayed surprise bound to dwell_s=240, not the inflection.",
            ),
            ("delayed_surprise_s", 240),
        ]
    )
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.pao-temp",
            "spikenaut.policy.feed-accept",
            [
                ("relay.tc.oligo", "policy.feed_accept", 0.69),
                ("relay.enc.decene", "policy.extra_hold", 0.21),
            ],
            "adenosine",
            0.05,
            "pao_confirm_stdp; adenosine tags the feed_accept bind at the oligomer-TC win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("dwell_s", 240),
                ("delayed_surprise_s", 240),
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
                    pop_budget("feed_accept", 44, 0.45, 240.0, 0.28),
                    pop("extra_hold", 32, 0.90),
                    pop("temp_veto", 18, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r101-525",
        "Decene-Fold DF-5 / Autoclave O-8: oligomer 94 C beats 1-decene 3.4 t/h by 160 us; "
        "ACCEPT already-legal PAO feed",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal 1-decene PAO feed. total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
        ras,
        gate,
        "decene-pao-oligomer",
        [
            "accept",
            "already-legal",
            "designed",
            "temp-vs-feed",
            "tick6-sidecar-bound",
        ],
        "Teaches that a lagging 1-decene encoder losing a 160 us race does not require a "
        "hold when oligomer temperature is already under the freeze cap.",
        5,
    )
