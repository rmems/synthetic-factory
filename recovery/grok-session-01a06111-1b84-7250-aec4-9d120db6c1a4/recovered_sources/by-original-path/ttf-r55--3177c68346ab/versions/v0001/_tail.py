def record_291():
    excerpt, extra = lif_291_excerpt()
    ticks = [
        tick(2112, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5280, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5460, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5980, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22600, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Chip column D-7 at Lignin-Naze LN-4 is already at 180 ppm extraction H2S against "
                "an 80 ppm cap while liquor still reads a legal 12.4 L/s. H2S-first clamps liquor "
                "12.4 -> 9.6 L/s; flow-first would keep cruise because extraction pressure 8.4 bar "
                "is still under the 10.0 bar shell cap. A blow-line gasket tear already seated on "
                "the upper strainer does not appear on H2S or liquor until the AE dump.",
            ),
            ("domain", "kamyr-chip-digester"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep D-7 extraction H2S <= 80 ppm and finish the cook without dumping liquor "
                "through a torn blow-line gasket.",
            ),
            ("t0_us", 1756850400000291),
            ("gate_latency_us", 700),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.280, 5.640]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "h2s.extract.ppm 180 over 80 cap",
                                "ft.liquor.lps 12.4 with shell 8.4 under 10.0",
                            ],
                        ),
                        (
                            "semantics",
                            "H2S-first latches liquor clamp 12.4 -> 9.6 L/s; flow-first keeps "
                            "12.4 on a 'still under shell-pressure cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one UV H2S slot versus the liquor-orifice publisher on this "
                            "Kamyr extraction bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (H2S 28 + liquor 34): 2.90x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 12.4 L/s; predicted next-sample 140 ppm "
                            "> 80 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "extraction UV H2S cell, 2 kHz, 28 us jitter",
                    "liquor-orifice DP + shell PT, 1 kHz, 34 us jitter",
                    "blow-line AE puck (context)",
                    "chip-meter tach (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("h2s_cap_ppm", 80.0),
                        ("observed_h2s_ppm", 180.0),
                        ("liquor_lps", 12.4),
                        ("shell_bar", 8.4),
                        ("shell_cap_bar", 10.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. D-7 indexed on Lignin-Naze LN-4; liquor 12.4 L/s; extraction H2S 180 ppm.",
                    "2. Shell 8.4 bar under 10.0 bar cap; cook armed.",
                    "3. Orifice precursor at 1.180 ms.",
                    "4. Race window [5.280, 5.640] ms.",
                    "5. h2s.extract.ppm 180 at 5.280 ms (winner).",
                    "6. ft.liquor.lps 12.4 at 5.460 ms (loser by 180 us).",
                    "7. Gate at 5.980 ms: MODIFY clamp 12.4 -> 9.6 L/s.",
                    "8. After clamp H2S 64 ppm <= 80; shell still 8.4 bar.",
                    "9. At 22.600 ms a blow-line gasket tear dumps 0.3 t liquor.",
                    "10. 15 min gasket isolate (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_liquor_flow"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("liquor_lps", 12.4),
                        ("h2s_ppm", 180.0),
                        ("shell_bar", 8.4),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("h2s_ppm", 180.0),
                        ("h2s_cap_ppm", 80.0),
                        ("predicted_unclamped_next_ppm", 140.0),
                        ("liquor_lps", 12.4),
                        ("shell_bar", 8.4),
                        ("shell_cap_bar", 10.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 12.4 L/s because shell 8.4 bar is under 10.0, treating the "
                "180 ppm H2S as a still-wet UV cell rather than an extraction-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Extraction H2S 180 ppm won by 180 us, so the column is off-spec, not still a "
                "shell-pressure story. Holding 12.4 L/s predicts next-sample 140 ppm > 80 cap. "
                "MODIFY: liquor 12.4 -> 9.6 L/s. Observed after clamp 64 ppm <= 80. A full REJECT "
                "is not indicated: a clean cook accepts 9.6 L/s.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "h2s_ppm",
                            OrderedDict(
                                [
                                    ("cap", 80.0),
                                    ("observed", 180.0),
                                    ("predicted_unclamped_next", 140.0),
                                    ("clamped_liquor_lps", 9.6),
                                    ("observed_after_clamp", 64.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 2.90),
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
            ("name", "clamped_liquor_flow"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("liquor_lps", 9.6),
                        ("h2s_ppm", 64.0),
                        ("shell_bar", 8.4),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: liquor 12.4 -> 9.6 L/s. Process-correct vs the 80 ppm H2S cap. "
                "Blow-line gasket still tears at 22.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held extraction H2S at 64 ppm. At 22.600 ms a blow-line "
                "gasket tear already seated on the upper strainer dumped 0.3 t of liquor. Clamp "
                "reduced dump energy; it did not prevent the tear. Partnered negative: process "
                "heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("extraction", "clamp executed; peak 64 ppm <= 80 cap"),
                        ("gasket", "tore at 22.600 ms; 0.3 t liquor"),
                        ("repair", "15 min gasket isolate (abort_s=900)"),
                        ("mission", "LN-4 cook incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither extraction H2S nor liquor FT predicted the seated blow-line gasket tear; ae.gasket.tear is a new channel at 22.600 ms, 16.620 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min gasket isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min gasket isolate after the blow-line tear. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the liquor clamp completed under the 80 ppm "
                "cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "h2s.extract.ppm (5.280 ms, 180 ppm)"),
                        ("loser", "ft.liquor.lps (5.460 ms, 12.4 L/s)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Flow-first by < 180 us inside the 360 us window would have kept "
                            "12.4 L/s; predicted next-sample 140 ppm would have missed the 80 "
                            "cap even without the gasket tear. The MODIFY is still the correct "
                            "process. The tear is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22600),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.600 ms gasket tear (tick t_us=22600), inside the 42 ms "
                "raster. The correct MODIFY at 5.980 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=900 isolation tick.",
            ),
            ("delayed_surprise_s", 900),
        ]
    )
    spikes = [
        spike("ft.liquor.lps", 1.180, 0.41),
        spike("h2s.extract.ppm", 2.112, 0.58),
        spike("ft.liquor.lps", 3.400, 0.50),
        spike("h2s.extract.ppm", 5.280, 1.31),
        spike("ft.liquor.lps", 5.460, 1.12),
        spike("ctrl.gate", 5.980, 0.97),
        spike("h2s.extract.ppm", 8.100, 0.82),
        spike("ft.liquor.lps", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.gasket.tear", 22.600, 1.48),
        spike("ae.gasket.tear", 24.100, 0.93),
        spike("ft.liquor.lps", 30.200, 0.40),
        spike("h2s.extract.ppm", 36.400, 0.55),
    ]
    dw = 0.36
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.kamyr-h2s",
            "spikenaut.policy.liq-clamp",
            [
                ("relay.h2s.extract", "policy.liq_clamp", 0.68),
                ("relay.ft.liquor", "policy.flow_hold", 0.29),
                ("relay.ae.gasket", "policy.liq_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at H2S win (5.280 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.600 ms gasket tear",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", dw),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("liq_clamp", 50, 0.50, 220.0, dw),
                    pop_budget("flow_hold", 40, 0.80, 50.0, dw),
                    pop("tear_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r55-291"),
            (
                "title",
                "Lignin-Naze LN-4 / Digester D-7: extraction H2S beats liquor flow by 180 us; "
                "correct MODIFY still eats an in-window blow-line gasket tear (partnered negative "
                "total -0.44)",
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
                    "42 ms raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named "
                    "gasket isolate (abort_s=900) is not netted into task_progress.",
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
                    "15 min gasket isolate.",
                    1,
                ),
            ),
        ]
    )


def record_292():
    ticks = [
        tick(2160, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5400, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5580, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5920, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6260, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.o2.pct", 1.080, 0.42),
        spike("tc.bed.live", 2.160, 0.57),
        spike("enc.o2.pct", 3.400, 0.49),
        spike("tc.bed.live", 5.400, 1.29),
        spike("tc.bed.lag", 5.580, 1.10),
        spike("ctrl.gate", 5.920, 0.96),
        spike("tc.bed.live", 8.200, 0.80),
        spike("enc.o2.pct", 10.200, 0.63),
        spike("ctrl.gate", 10.880, 0.84),
        spike("tc.bed.live", 16.400, 0.41),
        spike("tc.bed.lag", 22.100, 0.54),
        spike("tc.bed.live", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(55292, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Contact bed C-2 at Oleum-Howe OH-3 reads live catalyst 612 C against a 580 C "
                "cap while a lagged historian tag still prints 548 C. Live-first should cut "
                "quench air 4.2 -> 1.2 t/h at t_gate; a weak supervisor waits for the STALE "
                "lagged tag to catch up and applies the same 1.2 t/h cut late.",
            ),
            ("domain", "sulfuric-contact-bed"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the OH-3 conversion with bed TC <= 580 C, leave SO2 feed at the planned "
                "12.0 t/h, and keep quench air legal.",
            ),
            ("t0_us", 1756850400000292),
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
                                "tc.bed.live 612 C on pass 2",
                                "tc.bed.lag 548 C STALE historian",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-first should latch a timely quench cut 4.2 -> 1.2 t/h at t_gate; "
                            "lag-first is a false 'still approaching 580' wait for the historian.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live-TC slot versus the lagged historian publisher on "
                            "this contact-bed PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (live 28 + lag 32). Order is "
                            "correctly live-first. The error is when the clamp is applied, not "
                            "which actuator or how far: the lagged tag is STALE.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live bed TC, 2 kHz, 28 us jitter, tag=BED_TC.LIVE",
                    "lagged historian TC, 1 kHz, 32 us jitter, tag=BED_TC.HIST quality=STALE",
                    "quench-air FT (context)",
                    "SO2 feed FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 580.0),
                        ("observed_bed_C", 612.0),
                        ("lagged_bed_C", 548.0),
                        ("lagged_tag", "BED_TC.HIST"),
                        ("lagged_quality", "STALE"),
                        ("sample_age_s", 42.0),
                        ("so2_tph", 12.0),
                        ("latest_legal_clamp_us", 5920),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. C-2 already on pass 2; live bed 612 C; SO2 12.0 t/h.",
                    "2. Lagged historian 548 C, quality STALE, sample_age_s=42.",
                    "3. O2 precursor at 1.080 ms.",
                    "4. Race window [5.400, 5.740] ms.",
                    "5. tc.bed.live 612 C at 5.400 ms (winner).",
                    "6. tc.bed.lag 548 C STALE at 5.580 ms (loser by 180 us).",
                    "7. Gate at 5.920 ms: WRONG-MODIFY waits for lagged-tag reconcile (latest_legal_clamp_us=5920).",
                    "8. Same 1.2 t/h quench applied late at 10.880 ms; bed peaked 628 C.",
                    "9. Converter trip; bed recycle.",
                    "10. Delayed (abort_s=720): 12 min bed recycle while C-2 is quenched and reseeded.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_quench_air"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("quench_tph", 4.2),
                        ("bed_C", 612.0),
                        ("extra_lag_reconcile", False),
                        ("so2_tph", 12.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 612.0),
                        ("bed_cap_C", 580.0),
                        ("lagged_C", 548.0),
                        ("lagged_tag", "BED_TC.HIST"),
                        ("lagged_quality", "STALE"),
                        ("sample_age_s", 42.0),
                        ("so2_tph", 12.0),
                        ("latest_legal_clamp_us", 5920),
                        ("t_gate_us", 5920),
                        ("t_exec_us", 10880),
                        ("correct_quench_tph", 1.2),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 4.2 t/h quench: lagged historian 548 C is under the "
                "580 C cap, so the 612 C live bed is treated as an unvalidated spike, not an over-cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Live bed 612 C exceeds the 580 C cap (true). Confirm on the lagged historian "
                "before cutting quench, because BED_TC.HIST still prints 548 C. Apply the same "
                "1.2 t/h quench after the STALE tag catches up.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 580.0),
                                    ("observed", 612.0),
                                    ("lagged", 548.0),
                                    ("lagged_quality", "STALE"),
                                    ("correct_at_t_gate", 1.2),
                                    ("executed_t_exec_us", 10880),
                                    ("latest_legal_clamp_us", 5920),
                                ]
                            ),
                        ),
                        (
                            "timing",
                            OrderedDict(
                                [
                                    ("t_gate_us", 5920),
                                    ("lag_reconcile_us", 4960),
                                    ("t_exec_us", 10880),
                                    ("late", True),
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
            ("name", "quench_after_lag_reconcile"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("quench_tph", 1.2),
                        ("bed_C", 612.0),
                        ("extra_lag_reconcile", True),
                        ("t_exec_us", 10880),
                        ("so2_tph", 12.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / stale-sample lagged-tag): correct 1.2 t/h quench applied at "
                "10.880 ms after latest_legal_clamp_us=5920. Routing relay.tc.lagged -> "
                "policy.wait_lag; no positive weight to policy.quench_now.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY waited for a STALE lagged tag and applied the correct 1.2 t/h "
                "quench late. Live 612 C was over the 580 C cap at t_gate; lagged 548 C was "
                "already stale. Peak 628 C tripped the converter. 12 min bed recycle "
                "(abort_s=720). Correct gate was MODIFY quench 4.2 -> 1.2 t/h at t_gate_us=5920.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bed", "late quench 1.2 t/h; peak 628 > 580 cap"),
                        ("historian", "STALE 548 C never validated the live over-cap"),
                        ("recycle", "12 min bed recycle, C-2 reseed"),
                        ("mission", "pass 2 deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-first was the correct order and the temperature number was over cap; the MODIFY spent that win waiting for a STALE historian tag.",
                    "Delayed (abort_s=720): OH-3 holds 12 min while C-2 is quenched and reseeded; next pass 14 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY quench 4.2 -> 1.2 t/h at t_gate_us=5920; extra_lag_reconcile=false; leave SO2 at 12.0 t/h.",
                        ),
                        ("correct_actuator", "quench_air"),
                        ("wrong_timing", "extra_lag_reconcile"),
                        ("latest_legal_clamp_us", 5920),
                        ("t_exec_us", 10880),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("quench_tph", 1.2),
                                    ("extra_lag_reconcile", True),
                                    ("t_exec_us", 10880),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min bed recycle (task/efficiency); bed peaked 628 C during the lag reconcile (safety near-miss of a late-but-correct-magnitude quench).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bed.live (5.400 ms, 612 C)"),
                        ("loser", "tc.bed.lag (5.580 ms, 548 C STALE)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Lag-first by < 180 us would still be a STALE 548 C under the 580 C "
                            "cap; a correct gate binds tc.bed.live to policy.quench_now at t_gate "
                            "either way. The wrong MODIFY spent the live win on a lagged tag.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5920),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the lag-wait bind (5.920 ms, tick 4). "
                "The 12 min bed recycle is delayed surprise, not the inflection.",
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
            "thalamic-relay.bed-lag",
            "spikenaut.policy.wait-lag",
            [
                ("relay.tc.lagged", "policy.wait_lag", 0.73),
                ("relay.tc.live", "policy.wait_lag", 0.22),
            ],
            "acetylcholine",
            0.08,
            "timing_cap_stdp; ACh tags the (wrong) wait_lag bind at the live win",
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
                    pop_budget("wait_lag", 48, 0.45, 300.0, dw),
                    pop("quench_now", 48, 0.90),
                    pop("stale_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r55-292"),
            (
                "title",
                "WRONG-MODIFY at Oleum-Howe OH-3 / Converter C-2: live 612 C read correctly; "
                "correct 1.2 t/h quench applied after latest_legal_clamp_us (stale-sample / lagged-tag)",
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
                    "Wrong-modify / stale-sample lagged-tag. Sidecar arithmetic 612 > 580 on live "
                    "is true; MODIFY bound to wait_lag. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "sulfuric-contact-bed",
                    [
                        "modify",
                        "wrong-gate",
                        "stale-sample",
                        "lagged-tag",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live-first race can still be a wrong gate "
                    "when the MODIFY waits for a STALE lagged tag past latest_legal_clamp_us. "
                    "Convictable from timestamps, tag quality, and routing to without contact-bed physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_293():
    ticks = [
        tick(2736, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6840, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7020, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7640, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(7960, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.plunger.bar", 1.360, 0.40),
        spike("ae.blank.pps", 2.736, 0.56),
        spike("enc.plunger.bar", 4.100, 0.48),
        spike("ae.blank.pps", 6.840, 1.34),
        spike("enc.plunger.bar", 7.020, 1.11),
        spike("ctrl.gate", 7.640, 0.98),
        spike("ae.blank.pps", 10.400, 0.81),
        spike("enc.plunger.bar", 14.800, 0.62),
        spike("ctrl.gate", 18.200, 0.84),
        spike("ae.blank.pps", 28.400, 0.52),
        spike("enc.plunger.bar", 36.100, 0.39),
        spike("ae.blank.pps", 42.200, 0.44),
    ]
    excerpt = independent_excerpt(55293, 120, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Blank mold M-8 on the Goblet-Fen GF-HIL IS-machine sees AE at 48 pps while "
                "plunger hydraulics sit at 6.2 bar under an 8.0 bar cap. AE-first holds the gob; "
                "plunger-first would dispatch 12 cpm because the ram looks legal. The HIL blank "
                "mockup is the authority, not the hot-end floor.",
            ),
            ("domain", "container-glass-IS"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep M-8 from dispatching a cracked blank while plunger pressure remains under "
                "its own cap.",
            ),
            ("t0_us", 1756850400000293),
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
                                "ae.blank.pps 48 over 12 cap",
                                "enc.plunger.bar 6.2 under 8.0 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; plunger-first dispatches 12 cpm on a "
                            "'ram still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one AE puck slot versus the plunger-PT publisher on this "
                            "HIL blank-mold bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + plunger 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have dispatched 12 cpm into a cracked blank.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "blank-mold AE puck, 50 kHz, 26 us jitter",
                    "plunger hydraulic PT, 1 kHz, 32 us jitter",
                    "gob tach (context)",
                    "forehearth IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 12.0),
                        ("observed_ae_pps", 48.0),
                        ("plunger_bar", 6.2),
                        ("plunger_cap_bar", 8.0),
                        ("proposed_cpm", 12.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. M-8 HIL indexed; 12 cpm armed.",
                    "2. Plunger 6.2 bar under 8.0; AE 48 pps over 12.",
                    "3. Plunger precursor at 1.360 ms.",
                    "4. Race window [6.840, 7.160] ms.",
                    "5. ae.blank.pps 48 at 6.840 ms (winner).",
                    "6. enc.plunger.bar 6.2 at 7.020 ms (loser by 180 us).",
                    "7. Gate at 7.640 ms: REJECT hold, do not dispatch.",
                    "8. Cycle 0 cpm; plunger left at 6.2 bar.",
                    "9. Blank inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min mold reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_gob"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cpm", 12.0),
                        ("hold", False),
                        ("plunger_bar", 6.2),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 48.0),
                        ("ae_cap_pps", 12.0),
                        ("plunger_bar", 6.2),
                        ("plunger_cap_bar", 8.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 12 cpm because plunger 6.2 bar is under 8.0, treating the "
                "48 pps AE as mold-ring noise rather than a cracked blank.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Blank AE 48 pps won by 180 us, so the mold is cracked, not still a plunger-pressure "
                "story. Plunger 6.2 bar is under 8.0 and does not authorize dispatch. REJECT: hold "
                "cycle 12 -> 0 cpm. A MODIFY that only trims plunger would leave the cracked blank.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ae_pps",
                            OrderedDict(
                                [
                                    ("cap", 12.0),
                                    ("observed", 48.0),
                                    ("executed_cpm", 0.0),
                                ]
                            ),
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
            ("name", "hold_blank_mold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cpm", 0.0),
                        ("hold", True),
                        ("plunger_bar", 6.2),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: cycle 12 -> 0 cpm. Plunger left at 6.2 bar under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held M-8. AE 48 pps beat plunger 6.2 bar by 180 us. Plunger was "
                "legal; the blank was not. 8 min mold reset (abort_s=480) is delayed survey, "
                "not a process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("cycle", "held at 0 cpm"),
                        ("plunger", "left 6.2 bar < 8.0 cap"),
                        ("mold", "8 min mold reset (abort_s=480)"),
                        ("mission", "HIL blank not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Plunger PT never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min mold reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.blank.pps (6.840 ms, 48 pps)"),
                        ("loser", "enc.plunger.bar (7.020 ms, 6.2 bar)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Plunger-first by < 180 us inside the 320 us window would have dispatched "
                            "12 cpm into a cracked blank. The REJECT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7640),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.640 ms, tick 4). The 8 min mold "
                "reset is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    dw = 0.32
    ras = raster_core(
        46,
        120,
        20,
        110,
        routing(
            "thalamic-relay.blank-ae",
            "spikenaut.policy.mold-hold",
            [
                ("relay.ae.blank", "policy.mold_hold", 0.70),
                ("relay.enc.plunger", "policy.plunger_go", 0.24),
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
            ("decision_window_ms", dw),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop_budget("mold_hold", 56, 0.45, 280.0, dw),
                    pop("plunger_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r55-293"),
            (
                "title",
                "Goblet-Fen GF-HIL / IS-machine M-8: blank AE 48 pps beats plunger 6.2 bar by "
                "180 us; correct REJECT holds the gob",
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
                    "Correct REJECT. AE 48 > 12 cap beats legal plunger. "
                    "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "container-glass-IS",
                    [
                        "reject",
                        "hil",
                        "ae-vs-plunger",
                        "cracked-blank",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal plunger header can lose to blank-mold AE inside a 320 us "
                    "window; reversing 180 us would have dispatched a cracked blank.",
                    3,
                ),
            ),
        ]
    )


def record_294():
    ticks = [
        tick(2880, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7200, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7380, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7840, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8200, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("ir.ladle.C", 1.200, 0.40),
        spike("gc.o.ppm", 2.880, 0.55),
        spike("ir.ladle.C", 4.400, 0.48),
        spike("gc.o.ppm", 7.200, 1.26),
        spike("ir.ladle.C", 7.380, 1.08),
        spike("ctrl.gate", 7.840, 0.95),
        spike("gc.o.ppm", 11.200, 0.78),
        spike("ir.ladle.C", 14.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("gc.o.ppm", 22.600, 0.50),
        spike("ir.ladle.C", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(55294, 48, 28000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("circulate_min", 4.2),
            ("o_ppm", 18.0),
            ("snorkel_mbar", 0.8),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Snorkel V-11 at Snorkel-Weir SW-5 is already circulating at 0.8 mbar with "
                "dissolved oxygen 18 ppm against a 25 ppm cap. Ladle IR leftover is 1580 C under "
                "a 1640 C cap. Oxygen-first accepts the 4.2 min circulate; IR-first would have "
                "rejected a legal degas on a 'still climbing' model.",
            ),
            ("domain", "rh-vacuum-degasser"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the SW-5 circulate with dissolved oxygen <= 25 ppm and ladle IR <= 1640 C.",
            ),
            ("t0_us", 1756850400000294),
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
                                "gc.o.ppm 18 under 25 cap",
                                "ir.ladle.C 1580 under 1640 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Oxygen-first confirms the already-legal 4.2 min circulate; IR-first "
                            "would have treated the GC as a climb echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one dissolved-oxygen GC slot versus the ladle-IR publisher "
                            "on this simulated RH bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (GC 26 + IR 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed circulate illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "dissolved-oxygen GC, 26 us jitter",
                    "ladle IR pyrometer, 32 us jitter",
                    "snorkel PT (context)",
                    "lift-gas FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("o_cap_ppm", 25.0),
                        ("observed_o_ppm", 18.0),
                        ("ladle_cap_C", 1640.0),
                        ("observed_ladle_C", 1580.0),
                        ("h_cap_ppm", 2.0),
                        ("observed_h_ppm", 1.4),
                        ("proposed_circulate_min", 4.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. V-11 indexed on Snorkel-Weir SW-5; 4.2 min circulate armed.",
                    "2. Caps: O 25 ppm, H 2.0 ppm, ladle 1640 C.",
                    "3. IR precursor at 1.200 ms.",
                    "4. Race window [7.200, 7.560] ms.",
                    "5. gc.o.ppm 18 at 7.200 ms (winner).",
                    "6. ir.ladle.C 1580 at 7.380 ms (loser by 180 us).",
                    "7. Gate at 7.840 ms: ACCEPT 4.2 min already legal.",
                    "8. Circulate continues; no extra hold.",
                    "9. 6 min survey confirms O still under 25 ppm.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "circulate_4p2"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("o_ppm", 18.0),
                        ("o_cap_ppm", 25.0),
                        ("ladle_C", 1580.0),
                        ("ladle_cap_C", 1640.0),
                        ("h_ppm", 1.4),
                        ("h_cap_ppm", 2.0),
                        ("circulate_min", 4.2),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 4.2 min circulate because O 18 ppm is under 25 and ladle "
                "1580 C is under 1640 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Dissolved oxygen 18 ppm won by 180 us and is under 25 ppm. Ladle 1580 C is under "
                "1640 C. Hydrogen 1.4 ppm is under 2.0. ACCEPT the already-legal circulate.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "o_ppm",
                            OrderedDict(
                                [
                                    ("cap", 25.0),
                                    ("observed", 18.0),
                                    ("executed_circulate_min", 4.2),
                                ]
                            ),
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
            ("name", "circulate_4p2"),
            ("parameters", OrderedDict(params.items())),
            (
                "gate_effect",
                "ACCEPT: 4.2 min circulate and 18 ppm O unchanged. Routing relay.gc.o -> "
                "policy.circ_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left V-11 on a 4.2 min / 18 ppm circulate. Ladle IR hitch did not "
                "justify a hold. 6 min survey confirmed O still under 25 ppm.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("snorkel", "still 4.2 min / 0.8 mbar"),
                        ("oxygen", "18 ppm under 25 cap"),
                        ("ladle", "1580 C under 1640"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Ladle IR 1580 C hitch is residual, not a superheat trip.",
                    "Delayed (survey_s=360): 6 min survey restacks V-11 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "gc.o.ppm (7.200 ms, 18 ppm)"),
                        ("loser", "ir.ladle.C (7.380 ms, 1580 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 180 us would only delay confirmation. The circulate stays "
                            "legal either way; ACCEPT is still required.",
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
    dw = 0.36
    ras = raster_core(
        28,
        48,
        42,
        56,
        routing(
            "thalamic-relay.o-gc",
            "spikenaut.policy.circ-go",
            [
                ("relay.gc.o", "policy.circ_go", 0.68),
                ("relay.ir.ladle", "policy.ir_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_circ_stdp; 5-HT tags the circ_go bind at the GC win",
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
            ("decision_window_ms", dw),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("circ_go", 40, 0.45, 250.0, dw),
                    pop("ir_hold", 32, 0.90),
                    pop("o_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r55-294"),
            (
                "title",
                "Snorkel-Weir SW-5 / Vessel V-11: dissolved oxygen 18 ppm beats ladle IR 1580 C "
                "by 180 us; ACCEPT already-legal 4.2 min circulate",
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
                    "Correct ACCEPT of an already-legal RH circulate. total +1.06 = "
                    "0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "rh-vacuum-degasser",
                    [
                        "accept",
                        "already-legal",
                        "simulated-rh-loop",
                        "gc-vs-ir",
                        "sidecar-convictable",
                        "simulated",
                    ],
                    "Teaches that a dissolved-oxygen GC under cap can confirm an already-legal "
                    "circulate without a ladle-IR hitch becoming a hold.",
                    4,
                ),
            ),
        ]
    )


def record_295():
    ticks = [
        tick(2016, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5040, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5920, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(300000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.chain.mpm", 0.980, 0.41),
        spike("ir.tow.C", 2.016, 0.60),
        spike("enc.chain.mpm", 3.200, 0.51),
        spike("ir.tow.C", 5.040, 1.30),
        spike("enc.chain.mpm", 5.200, 1.12),
        spike("ctrl.gate", 5.640, 0.97),
        spike("ir.tow.C", 8.100, 0.78),
        spike("enc.chain.mpm", 12.400, 0.62),
        spike("ctrl.gate", 16.200, 0.85),
        spike("ir.tow.C", 20.400, 0.54),
        spike("enc.chain.mpm", 22.800, 0.43),
    ]
    excerpt = independent_excerpt(55295, 80, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("chain_m_min", 1.8),
            ("tow_C", 248.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Oxidation zone Z-3 at Panox-Holt PH-9 is already at 248 C tow IR against a 265 C "
                "cap with chain 1.8 m/min under 2.4. IR-first accepts the dwell; chain-first would "
                "have rejected a legal oxidation on a 'still accelerating' model.",
            ),
            ("domain", "carbon-fiber-oxi-oven"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run Z-3 at 1.8 m/min, keep tow IR <= 265 C and oven O2 in 16-21 percent, and "
                "leave the line on schedule.",
            ),
            ("t0_us", 1756850400000295),
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
                                "ir.tow.C 248 C under 265 cap",
                                "enc.chain.mpm 1.8 under 2.4 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "IR-first confirms the already-legal 1.8 m/min dwell; chain-first "
                            "would have treated the IR as a hitch echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one tow-IR slot versus the chain-encoder publisher on this "
                            "oxidation-oven bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (IR 22 + chain 30): 3.08x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal dwell.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "tow IR pyrometer, 2 kHz, 22 us jitter",
                    "chain encoder, 1 kHz, 30 us jitter",
                    "oven O2 cell (context)",
                    "exhaust humidity (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("tow_cap_C", 265.0),
                        ("observed_tow_C", 248.0),
                        ("chain_m_min", 1.8),
                        ("chain_cap_m_min", 2.4),
                        ("o2_pct", 18.0),
                        ("o2_band_pct", [16.0, 21.0]),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Zone Z-3 indexed on Panox-Holt PH-9; chain 1.8 m/min armed.",
                    "2. Tow IR 248 C under 265; chain under 2.4; O2 18 percent.",
                    "3. Chain precursor at 0.980 ms.",
                    "4. Race window [5.040, 5.320] ms.",
                    "5. ir.tow.C 248 at 5.040 ms (winner).",
                    "6. enc.chain.mpm 1.8 at 5.200 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 1.8 m/min.",
                    "8. Tow stays 248 C; chain stays 1.8 m/min.",
                    "9. Tow exits zone 3 on-spec.",
                    "10. Delayed (dwell_s=300): 5 min creel reseq.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_chain_dwell"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("tow_C", 248.0),
                        ("tow_cap_C", 265.0),
                        ("chain_m_min", 1.8),
                        ("chain_cap_m_min", 2.4),
                        ("o2_pct", 18.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.8 m/min because tow 248 C is under 265 and chain 1.8 is "
                "under 2.4.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Tow IR 248 C won by 160 us, so the dwell is already legal, not still "
                "accelerating. Chain 1.8 m/min is under 2.4. ACCEPT the 1.8 m/min dwell. A REJECT "
                "would idle a legal oxidation zone.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tow_C",
                            OrderedDict(
                                [
                                    ("cap", 265.0),
                                    ("observed", 248.0),
                                    ("executed_chain_m_min", 1.8),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 160),
                                    ("combined_jitter_us", 52),
                                    ("ratio", 3.08),
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
            ("name", "hold_chain_dwell"),
            ("parameters", OrderedDict(params.items())),
            ("gate_effect", "ACCEPT: leave 1.8 m/min; tow 248 C; chain legal."),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 1.8 m/min dwell. Tow 248 C beat chain 1.8 "
                "m/min by 160 us. 5 min creel reseq (dwell_s=300) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("chain", "1.8 m/min held"),
                        ("tow", "248 C < 265 cap"),
                        ("zone", "Z-3 on-spec"),
                        ("reseq", "5 min creel reseq (dwell_s=300)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Chain encoder never approached 2.4 m/min; tow was already under cap.",
                    "Delayed (dwell_s=300): 5 min creel reseq after zone 3.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.tow.C (5.040 ms, 248 C)"),
                        ("loser", "enc.chain.mpm (5.200 ms, 1.8 m/min)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Chain-first by < 160 us inside the 280 us window would have REJECTED "
                            "an already-legal dwell. The ACCEPT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5640),
            (
                "reward_inflection_note",
                "Task and safety rise at the correct ACCEPT (5.640 ms, tick 4). The 5 min reseq "
                "is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 300),
        ]
    )
    dw = 0.28
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.tow-ir",
            "spikenaut.policy.chain-go",
            [
                ("relay.ir.tow", "policy.chain_go", 0.67),
                ("relay.enc.chain", "policy.chain_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the tow-IR win as an already-legal dwell",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("dwell_s", 300),
                ("delayed_surprise_s", 300),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", dw),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("chain_go", 40, 0.45, 250.0, dw),
                    pop("chain_hold", 32, 0.90),
                    pop("ir_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r55-295"),
            (
                "title",
                "Panox-Holt PH-9 / Zone Z-3: tow IR 248 C beats chain 1.8 m/min by 160 us; "
                "correct ACCEPT of an already-legal 1.8 m/min dwell",
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
                    "Correct ACCEPT. Tow 248 < 265; chain 1.8 < 2.4. "
                    "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "carbon-fiber-oxi-oven",
                    [
                        "accept",
                        "designed",
                        "tow-vs-chain",
                        "already-legal-dwell",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal chain encoder can lose to tow IR inside a 280 us "
                    "window; reversing 160 us would have REJECTED an already-legal dwell.",
                    5,
                ),
            ),
        ]
    )


def tokenize(text: str) -> set[str]:
    return {tok for tok in re.split(r"[^a-z0-9]+", text.lower()) if tok}


def jaccard(a: str, b: str) -> float:
    sa, sb = tokenize(a), tokenize(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def check_refractory(events, min_ms=0.8):
    last = {}
    for ev in events:
        ch, t = ev["channel"], ev["t_rel_ms"]
        if ch in last and t - last[ch] < min_ms - 1e-12:
            return f"{ch} gap {t - last[ch]} ms"
        last[ch] = t
    return None


def check_race(rec):
    start, end = rec["state"]["race_window_rel_ms"]
    in_win = {}
    for ev in rec["spike_events"]:
        if start <= ev["t_rel_ms"] <= end:
            in_win.setdefault(ev["channel"], 0)
            in_win[ev["channel"]] += 1
    if len(in_win) < 2:
        return f"race window has {len(in_win)} channels: {in_win}"
    return None


def excerpt_vs_spikes(rec):
    spike_us = {int(round(ev["t_rel_ms"] * 1000.0)) for ev in rec["spike_events"]}
    ex_us = {item["t_us"] for item in rec["raster"]["excerpt"]}
    if not spike_us:
        return 0.0
    return len(spike_us & ex_us) / len(spike_us)


def expected_m6_prefix(rec):
    st = rec["state"]
    events = rec["spike_events"]
    race = st["race_window_rel_ms"]
    in_win = [e for e in events if race[0] - 1e-9 <= e["t_rel_ms"] <= race[1] + 1e-9]
    ordered = sorted(in_win, key=lambda e: e["t_rel_ms"])
    win_e = next(e for e in ordered if e["channel"] != "ctrl.gate")
    lose_e = next(
        e for e in ordered if e["channel"] not in {win_e["channel"], "ctrl.gate"}
    )
    t_win = round(win_e["t_rel_ms"] * 1000)
    t_lose = round(lose_e["t_rel_ms"] * 1000)
    t_gate = t_win + int(st["gate_latency_us"])
    t_race = int(st["race_window_us"])
    tick1 = round(0.40 * t_win)
    if rec["id"] == "ttf-r55-291":
        tick5 = 22600
    else:
        tick5 = t_gate + t_race
    return [tick1, t_win, t_lose, t_gate, tick5], t_win, t_lose, t_gate


def walk_keys(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            if str(k).lower() in THOUGHT_KEYS:
                found.append(p)
            found.extend(walk_keys(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(walk_keys(v, f"{path}[{i}]"))
    return found


def prior_domains_and_descs():
    domains = set()
    descs = []
    blobs = []
    for path in sorted(Path("/tmp").glob("ttf-r*/batch-r*.jsonl")):
        if path.resolve() == BATCH_PATH.resolve():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        blobs.append(text)
        for line in text.split("\n"):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            d = rec.get("state", {}).get("domain") or rec.get("meta", {}).get("domain")
            if d:
                domains.add(str(d))
            desc = rec.get("state", {}).get("description")
            if isinstance(desc, str):
                descs.append(desc)
    return domains, descs, "\n".join(blobs)


def self_check(records):
    issues = []
    descs = [r["state"]["description"] for r in records]
    opens = [d.split(".")[0] for d in descs]
    if len(set(opens)) != 5:
        issues.append("opening sentences not unique")
    jmax = 0.0
    for i in range(5):
        for j in range(i + 1, 5):
            val = jaccard(descs[i], descs[j])
            jmax = max(jmax, val)
            if val >= 0.4:
                issues.append(f"Jaccard {records[i]['id']}/{records[j]['id']} = {val:.3f}")
    prior_doms, prior_descs, prior_blob = prior_domains_and_descs()
    for plant in THIS_PLANTS:
        if plant in prior_blob:
            issues.append(f"plant {plant} collides prior jsonl")
    jprior = 0.0
    for desc in descs:
        for other in prior_descs:
            jprior = max(jprior, jaccard(desc, other))
    if jprior >= 0.4:
        issues.append(f"Jaccard vs prior {jprior:.3f}")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domain collision {domains}")
    overlap = set(domains) & prior_doms
    if overlap:
        issues.append(f"prior domain reuse {overlap}")
    if set(domains) != THIS_DOMAINS:
        issues.append(f"unexpected domains {domains}")
    banned_hit = set(domains) & BANNED_DOMAINS
    if banned_hit:
        issues.append(f"banned domains {banned_hit}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r55-292":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-modify":
        issues.append("expected wrong-modify")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    if hil != ["ttf-r55-293"]:
        issues.append(f"hil set {hil}")
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if sim != ["ttf-r55-294"]:
        issues.append(f"simulated set {sim}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if (
        decisions.count("ACCEPT") != 2
        or decisions.count("MODIFY") != 2
        or decisions.count("REJECT") != 1
    ):
        issues.append(f"gate mix {decisions}")
    ids = [r["id"] for r in records]
    if ids != [f"ttf-r55-{n}" for n in range(291, 296)]:
        issues.append(f"ids {ids}")
    for rec in records:
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rec['id']} training_ready present")
        if "outputs/raw" in blob:
            issues.append(f"{rec['id']} mentions outputs/raw")
        hidden = walk_keys(rec)
        if hidden:
            issues.append(f"{rec['id']} hidden keys {hidden}")
        err = check_refractory(rec["spike_events"])
        if err:
            issues.append(f"{rec['id']} refractory {err}")
        err = check_race(rec)
        if err:
            issues.append(f"{rec['id']} {err}")
        n = rec["raster"]["neurons"]
        rate = rec["raster"]["mean_rate_hz"]
        window_s = rec["raster"]["window_s"]
        expected = round(n * rate * window_s)
        if abs(rec["raster"]["spikes"] - expected) > 1:
            issues.append(f"{rec['id']} spike budget {rec['raster']['spikes']} vs {expected}")
        overlap_ex = excerpt_vs_spikes(rec)
        if rec["id"] == "ttf-r55-291":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("291 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("291 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("291 partnered-neg total not negative")
        elif overlap_ex >= 0.8:
            issues.append(f"{rec['id']} excerpt overlap {overlap_ex:.2f}")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_times = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_times:
            issues.append(f"{rec['id']} inflection {inf} not a tick")
        if len(rec["reward_components"]["ticks"]) != 6:
            issues.append(f"{rec['id']} tick count")
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rec['id']} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rec['id']} gate_snn decision mismatch")
        if rec["meta"]["round"] != 55:
            issues.append(f"{rec['id']} meta.round")
        if rec["meta"]["rights"]["intended_use"] != "research_only":
            issues.append(f"{rec['id']} rights")
        if rec["meta"]["rights"]["linear_issue"] != "RM-793":
            issues.append(f"{rec['id']} RM-793")
        if rec["meta"]["domain"] != rec["state"]["domain"]:
            issues.append(f"{rec['id']} domain mismatch")
        heads = ["task_progress", "safety", "efficiency", "coherence", "exploration"]
        total = sum(rec["reward_components"][h] for h in heads)
        if abs(total - rec["reward_components"]["total"]) > 1e-6:
            issues.append(f"{rec['id']} total mismatch {total}")
        for h in heads:
            s = sum(t[h] for t in rec["reward_components"]["ticks"])
            if abs(s - rec["reward_components"][h]) > 1e-6:
                issues.append(f"{rec['id']} {h} tick sum {s} vs {rec['reward_components'][h]}")
        prefix, t_win, t_lose, t_gate = expected_m6_prefix(rec)
        if tick_times[:5] != prefix:
            issues.append(f"{rec['id']} TTF-M6 prefix {tick_times[:5]} != {prefix}")
        nspk = len(rec["spike_events"])
        if not (5 <= nspk <= 40):
            issues.append(f"{rec['id']} spike count {nspk}")
        times = [e["t_rel_ms"] for e in rec["spike_events"]]
        if times != sorted(times):
            issues.append(f"{rec['id']} spike order")
        if not (8 <= len(rec["raster"]["excerpt"]) <= 16):
            issues.append(f"{rec['id']} excerpt n={len(rec['raster']['excerpt'])}")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rec['id']} ACCEPT params differ")
        if rec["id"] == "ttf-r55-292":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["bed_C"] > ev["bed_cap_C"]):
                issues.append("292 live bed not over cap")
            if not (ev["lagged_C"] < ev["bed_cap_C"]):
                issues.append("292 lagged not under cap")
            if ev.get("lagged_quality") != "STALE":
                issues.append("292 lagged quality not STALE")
            if not (ev["t_exec_us"] > ev["latest_legal_clamp_us"]):
                issues.append("292 t_exec not after latest_legal_clamp")
            if rec["executed_action"]["parameters"].get("extra_lag_reconcile") is not True:
                issues.append("292 extra_lag_reconcile not true")
            if rec["executed_action"]["parameters"].get("t_exec_us") != 10880:
                issues.append("292 expected t_exec_us=10880")
            if rec["executed_action"]["parameters"].get("quench_tph") != 1.2:
                issues.append("292 expected late-but-correct 1.2 t/h quench")
            if "recovery" not in rec["future_outcome"]:
                issues.append("292 missing recovery")
            table_to = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.quench_now" in table_to:
                issues.append("292 routing still has quench_now")
            if "policy.wait_lag" not in table_to:
                issues.append("292 routing missing wait_lag")
            if "stale-sample" not in rec["meta"]["tags"] or "lagged-tag" not in rec["meta"]["tags"]:
                issues.append("292 missing stale-sample/lagged-tag tags")
        blob_l = blob.lower()
        for frag in BANNED_PLANT_FRAGMENTS:
            if frag.lower() in blob_l:
                issues.append(f"{rec['id']} banned plant {frag}")
        delay = rec["future_outcome"].get("delayed_surprise_s") or rec["raster"].get(
            "delayed_surprise_s"
        )
        if delay is not None:
            expected_t6 = int(round(float(delay) * 1e6))
            if rec["reward_components"]["ticks"][-1]["t_us"] != expected_t6:
                issues.append(
                    f"{rec['id']} tick6 {rec['reward_components']['ticks'][-1]['t_us']} "
                    f"vs delayed_surprise {expected_t6}"
                )
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for popu in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in popu:
                exp = round(popu["neurons"] * popu["mean_rate_hz"] * dw_s)
                if abs(popu["spikes"] - exp) > 1:
                    issues.append(
                        f"{rec['id']} gate_snn {popu['name']} spikes {popu['spikes']} vs {exp}"
                    )
        t6 = rec["reward_components"]["ticks"][-1]["t_us"]
        if t6 <= rec["raster"]["window_ms"] * 1000:
            issues.append(f"{rec['id']} tick6 inside raster")
        gl, rw = rec["state"]["gate_latency_us"], rec["state"]["race_window_us"]
        if not (50 <= gl <= 2000):
            issues.append(f"{rec['id']} gate_latency")
        if not (50 <= rw <= 1000):
            issues.append(f"{rec['id']} race_window")
        if rec["raster"]["energy_pJ"] != rec["raster"]["spikes"] * 23:
            issues.append(f"{rec['id']} energy_pJ")
        if not (20 <= rec["raster"]["window_ms"] <= 50):
            issues.append(f"{rec['id']} window_ms")
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= rec["raster"]["window_ms"] * 1000):
                issues.append(f"{rec['id']} excerpt t_us {item['t_us']}")
            if not (0 <= item["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rec['id']} neuron_id {item['neuron_id']}")
    return issues, jmax, jprior


def notes_text(jmax: float, jprior: float) -> str:
    return f"""# Thalamic Trajectory Factory — NOTES-r55

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r55-291` … `ttf-r55-295`
- Domains this batch: `kamyr-chip-digester`, `sulfuric-contact-bed`, `container-glass-IS`, `rh-vacuum-degasser`, `carbon-fiber-oxi-oven`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r44 occupancy (jsonl SoT, including r33 `spiral-freezer` / `offset-web-press`, r34 `coke-oven-battery` / `chlor-alkali-membrane`, r35 `geothermal-binary-ORC` / `ammonia-converter`, r38 `ore-sinter-strand` / `fcc-riser`, r39 `sulfur-claus-furnace` / `pvc-suspension-kettle`, r44 `esr-ingot-melt` / `hip-isostatic-press`). All five plants are invented (Lignin-Naze, Oleum-Howe, Goblet-Fen, Snorkel-Weir, Panox-Holt). Do not restack prior TTF plants (Marrow-Dock, Vesper-Lattice, Brine-Well, Saddle-Arc, Ashlar-Gait, Nacre-Well, Quern-Forge, Tinder-Box, Whimbrel-Stack, Cinder-Loft, Suture-Isle, Kiln-Spur, Oxbow-Switch, Pitch-Kettle, Shale-Quay, Polder-Rye, Flint-Mask, Gyre-Tokamak, Quarry-Bowl, Orpiment, Gorse-Weir, Haber-Knoll, Loam-Hurst, Lamina-Kame, Prill-Flue, Floe-Helix, Ink-Noll, Leaf-Pike, Crucible-Wold, Cab-Moor, Gable-Retort, Soda-Weir, Argon-Cist, Hearth-Knap, Slurry-Crown, Argon-Fell, Cachet-Croft, Boron-Veld, Nahcolite-Kettle, Smelt-Spur, Ingot-Cairn, Spume-Rack, Looper-Holt, Pyrite-Hood, Zeolite-Riser, Laterite-Vat, Adiabat-Sieve, Finisher-Coil, Pyrite-Gill, Vinyl-Garth, Flute-Wick, Otter-Brae, Tenter-Howe, Thoria-Kettle, Nitrid-Fell, Riser-Wold, Crepe-Noll, Zinc-Fen).

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
| ttf-r55-291 | kamyr-chip-digester | MODIFY | correct | designed | **−0.44** | process-correct liquor clamp; blow-line gasket tear inside 42 ms raster; independent LIF |
| ttf-r55-292 | sulfuric-contact-bed | MODIFY | **incorrect (wrong-modify / stale-sample lagged-tag)** | designed | −0.68 | live 612 C > 580 cap; correct 1.2 t/h quench applied after latest_legal_clamp_us waiting on STALE historian |
| ttf-r55-293 | container-glass-IS | REJECT | correct | hil | +0.80 | AE 48 pps beats plunger 6.2 bar; hold gob |
| ttf-r55-294 | rh-vacuum-degasser | ACCEPT | correct | simulated | +1.06 | O 18 ppm vs ladle 1580 C; proposed 4.2 min already legal |
| ttf-r55-295 | carbon-fiber-oxi-oven | ACCEPT | correct | designed | +1.14 | tow 248 C vs chain 1.8 m/min; proposed 1.8 m/min already legal |

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 incorrect MODIFY (stale-sample / lagged-tag), 1 correct REJECT. Provenance: designed×3, simulated×1, hil×1 (Goblet-Fen GF-HIL IS-machine stand). Intra-batch Jaccard on `state.description` {jmax:.3f} (max vs prior staged {jprior:.3f}).

## Wrong-modify

**ttf-r55-292** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-modify`). Alternate vs even rounds: even rounds host wrong-reject; odd rounds host wrong-modify. This is **stale-sample / lagged-tag** (correct actuator, correct magnitude, applied after `latest_legal_clamp_us` because a STALE historian tag was treated as the validating PV). Not r13/r19 wrong-axis, not r14/r23 wrong-loop, not r21 wrong-polarity, not r24 under-clamp, not r25/r29/r31 wrong-phase, not r33/r35 over-clamp, not r39 extra-PLC-scan clamp-too-late. Do not emit a wrong-ACCEPT.

Oleum-Howe OH-3 / Converter C-2 reads live bed TC **612 C** against a **580 C** cap. Lagged historian `BED_TC.HIST` still prints **548 C** with `quality=STALE` and `sample_age_s=42`. Sidecar arithmetic `612 > 580` is true and `548 < 580` is true. A timely MODIFY at `t_gate_us=5920` cuts quench **4.2 → 1.2 t/h**. A weak supervisor waits for the lagged tag to catch up and applies the same 1.2 t/h cut at **10.880 ms**. Bed peaks **628 C** and trips the converter. Convictable without contact-process physics: `evidence.bed_C > evidence.bed_cap_C`, `evidence.lagged_quality == STALE`, `evidence.t_exec_us > evidence.latest_legal_clamp_us`, `executed_action` sets `extra_lag_reconcile=true` and `t_exec_us=10880`, `raster.routing.table` sends `relay.tc.lagged` → `policy.wait_lag` (weight 0.73) with no positive weight to `policy.quench_now`, and `gate_snn` has `wait_lag` above threshold while `quench_now` is not. Recovery: MODIFY quench 4.2 → 1.2 t/h at t_gate; leave SO2 at 12.0 t/h. Cost: 12 min bed recycle (`abort_s=720`).

## Partnered-negative in-window (291)

**ttf-r55-291** is the partnered negative: process-correct MODIFY (liquor held 9.6 L/s; extraction H2S 64 ppm <= 80 cap) while the world still charges. Safety −0.60 prices the blow-line gasket tear at **22.600 ms**; `task_progress` stays +0.32 because the clamp completed. Inflection `t_us=22600` is tick 5 and is **inside** the 42 ms raster (`22600 ≤ 42000`). Named un-netted loss: 15 min gasket isolate (`abort_s=900`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 55291, stim `[22000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.tear` 22–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks). Tick 6 is bound to a published sidecar (`abort_s`, `survey_s`, `dwell_s`) via `future_outcome.delayed_surprise_s` and is strictly after the raster window. Inflection `t_us` is an actual tick.

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
| 291 | 6 | +0.32 | −0.60 | −0.16 | +0.04 | −0.04 | −0.44 | 5 (22600) |
| 292 | 6 | −0.22 | −0.24 | −0.18 | −0.10 | +0.06 | −0.68 | 4 (5920) |
| 293 | 6 | +0.10 | +0.42 | +0.12 | +0.10 | +0.06 | +0.80 | 4 (7640) |
| 294 | 6 | +0.40 | +0.28 | +0.18 | +0.12 | +0.08 | +1.06 | 4 (7840) |
| 295 | 6 | +0.44 | +0.30 | +0.20 | +0.12 | +0.08 | +1.14 | 4 (5640) |

Tick-6 sidecar bind: 291 `abort_s=900`, 292 `abort_s=720`, 293 `abort_s=480`, 294 `survey_s=360`, 295 `dwell_s=300`.

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
| 291 | kamyr-chip-digester | 76 | 26 | 42 | 83 | 1909 | 0.001909 |
| 292 | sulfuric-contact-bed | 88 | 34 | 28 | 84 | 1932 | 0.001932 |
| 293 | container-glass-IS | 120 | 20 | 46 | 110 | 2530 | 0.002530 |
| 294 | rh-vacuum-degasser | 48 | 42 | 28 | 56 | 1288 | 0.001288 |
| 295 | carbon-fiber-oxi-oven | 80 | 28 | 24 | 54 | 1242 | 0.001242 |

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (NA / ACh / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms. Non-291 excerpts are kernelized and independent of `spike_events` times (overlap < 0.8).

## Local checks (staging, not raw)

See generator stdout: `check_jsonl` FactoryStaging, `validate_run.check_line`, `dumps_exact_json`, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`, tick sums, refractory, Jaccard.

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (291). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. Tick-6 sidecar bind is standing machinery (r14+), not a new class.
4. Five domain slugs leave the prompt's 8-item pool; a later round that must stay inside the pool will have to rotate sit-outs instead.
5. 294 and 295 are both already-legal ACCEPTs; a later round could pair one ACCEPT with a world charge that does not go negative.

## Next densification target

Labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-MODIFY subclasses include **wrong-string (live vs idle parallel bank)**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 17.0%
"""


def run_pipelines(records):
    sys.path.insert(0, str(PIPELINES))
    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from exact_json import dumps_exact_json
    from round_txn import validate_novel_coverage
    from validate_run import check_line
    from verify_execution import verify_batch_for_frontier

    report = []
    errors, warnings, kinds, nrec = check_jsonl(
        BATCH_PATH, "batch-r55.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r55.jsonl:{i}", factory_staging=True)
        if errs:
            line_errs.append((i, kind, errs))
        try:
            dumps_exact_json(rec, ensure_ascii=False, sort_keys=False)
        except Exception as exc:
            line_errs.append((i, "exact_json", [str(exc)]))
    report.append(("check_line+exact_json", line_errs, None, None, None))
    raster_fail = []
    for rec in records:
        st = raster_status(rec, require_raster=True, require_routing_table=True)
        if not st.get("raster_valid") or not st.get("gate_snn_valid"):
            raster_fail.append((rec["id"], st))
    report.append(("raster_status", raster_fail, None, None, None))
    counts, findings, blocked = verify_batch_for_frontier(BATCH_PATH, strict=True)
    report.append(("verify_batch_for_frontier", counts, findings, blocked, None))
    cov = validate_novel_coverage(
        NOTES_PATH,
        Path("thalamic-trajectory-factory"),
        notes_text=NOTES_PATH.read_text(),
        required=True,
    )
    report.append(("validate_novel_coverage", cov, None, None, None))
    probe = subprocess.run(
        [sys.executable, str(PIPELINES / "spike_probe.py"), "--strict", str(BATCH_PATH)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    report.append(("spike_probe", probe.returncode, probe.stdout[-2000:], probe.stderr[-2000:], None))
    return report


def main() -> int:
    if "outputs/raw" in str(BATCH_PATH) or "outputs/raw" in str(NOTES_PATH):
        print("refusing to write outputs/raw")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_291(), record_292(), record_293(), record_294(), record_295()]
    issues, jmax, jprior = self_check(records)
    notes = notes_text(jmax, jprior)
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    NOTES_PATH.write_text(notes, encoding="utf-8")
    print(f"wrote {BATCH_PATH} lines={len(lines)} bytes={BATCH_PATH.stat().st_size} jmax={jmax:.3f} jprior={jprior:.3f}")
    print(f"wrote {NOTES_PATH} bytes={NOTES_PATH.stat().st_size}")
    if issues:
        print("SELF_CHECK_ISSUES:")
        for item in issues:
            print(" -", item)
        return 1
    print("SELF_CHECK_OK")
    report = run_pipelines(records)
    failed = False
    for item in report:
        name = item[0]
        print(f"PIPELINE {name}: {item[1:]}")
        if name == "check_jsonl FactoryStaging":
            errors, warnings, kinds, nrec = item[1], item[2], item[3], item[4]
            print(f"  kinds={kinds} n={nrec} errors={len(errors)} warnings={len(warnings)}")
            for e in errors:
                print("  ERR", e)
                failed = True
            for w in warnings[:20]:
                print("  WARN", w)
        elif name == "check_line+exact_json":
            if item[1]:
                failed = True
                print("  LINE_ERRS", item[1])
        elif name == "raster_status":
            if item[1]:
                failed = True
                print("  RASTER_FAIL", item[1])
        elif name == "verify_batch_for_frontier":
            print("  counts", item[1], "blocked", item[3])
            if item[3]:
                failed = True
                print("  findings", item[2][:8])
        elif name == "validate_novel_coverage":
            if item[1]:
                failed = True
        elif name == "spike_probe":
            if item[1] != 0:
                failed = True
                print("  PROBE_FAIL", item[2], item[3])
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
