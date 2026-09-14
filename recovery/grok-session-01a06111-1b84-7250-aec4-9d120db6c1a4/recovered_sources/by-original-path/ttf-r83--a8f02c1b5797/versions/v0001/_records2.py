def record_433():
    ticks = [
        tick(2736, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6840, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7020, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7640, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(7960, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("ir.wall.C", 1.360, 0.40),
        spike("ae.coil.pps", 2.736, 0.56),
        spike("ir.wall.C", 4.100, 0.48),
        spike("ae.coil.pps", 6.840, 1.34),
        spike("ir.wall.C", 7.020, 1.11),
        spike("ctrl.gate", 7.640, 0.98),
        spike("ae.coil.pps", 10.400, 0.81),
        spike("ir.wall.C", 14.800, 0.62),
        spike("ctrl.gate", 18.200, 0.84),
        spike("ae.coil.pps", 28.400, 0.52),
        spike("ir.wall.C", 36.100, 0.39),
        spike("ae.coil.pps", 42.200, 0.44),
    ]
    excerpt = independent_excerpt(83433, 120, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "On the KQ-HIL bench at Ketene-Quoin the seed puck on cracker C-4 is already "
                "clicking 52 pps over a 15 pps quiet-band, while wall IR still shows 680 C under "
                "740. Parking the 9 t/h acetic feed is the legal gate; riding the IR would have "
                "energized a noisy ketene coil. Production-furnace amps are not the authority here.",
            ),
            ("domain", "ketene-acetic-anhydride"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep C-4 from dispatching a growling ketene coil while wall IR remains under "
                "its own cap.",
            ),
            ("t0_us", 1756850400000433),
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
                                "ae.coil.pps 52 over 15 cap",
                                "ir.wall.C 680 under 740 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; IR-first dispatches 9 t/h acetic on a 'wall still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one AE puck slot versus the wall-IR publisher on this HIL ketene-cracker bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + IR 32): 3.10x over a "
                            "2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have dispatched 9 t/h into a growling coil.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "cracker-coil AE puck, 50 kHz, 26 us jitter",
                    "wall IR pyrometer, 1 kHz, 32 us jitter",
                    "acetic feed Coriolis (context)",
                    "diketene GC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 15.0),
                        ("observed_ae_pps", 52.0),
                        ("wall_C", 680.0),
                        ("wall_cap_C", 740.0),
                        ("proposed_acetic_tph", 9.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. C-4 HIL indexed; 9 t/h acetic armed.",
                    "2. Wall 680 C under 740; AE 52 pps over 15.",
                    "3. IR precursor at 1.360 ms.",
                    "4. Race window [6.840, 7.160] ms.",
                    "5. ae.coil.pps 52 at 6.840 ms (winner).",
                    "6. ir.wall.C 680 at 7.020 ms (loser by 180 us).",
                    "7. Gate at 7.640 ms: REJECT hold, do not dispatch.",
                    "8. Acetic 0 t/h; wall left at 680 C.",
                    "9. Coil inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min cracker reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_acetic"),
            (
                "parameters",
                OrderedDict([("acetic_tph", 9.0), ("hold", False), ("wall_C", 680.0)]),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 52.0),
                        ("ae_cap_pps", 15.0),
                        ("wall_C", 680.0),
                        ("wall_cap_C", 740.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 9 t/h acetic because wall 680 C is under 740, treating the "
                "52 pps AE as burner hash rather than a growling ketene coil.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Coil AE 52 pps won by 180 us, so the ketene cracker is growling, not still "
                "a wall-IR story. 680 C is under 740 and does not authorize dispatch. REJECT: "
                "hold acetic 9 -> 0 t/h. A MODIFY that only trims feed would leave the growl.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ae_pps",
                            OrderedDict(
                                [
                                    ("cap", 15.0),
                                    ("observed", 52.0),
                                    ("executed_acetic_tph", 0.0),
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
            ("name", "hold_cracker"),
            (
                "parameters",
                OrderedDict([("acetic_tph", 0.0), ("hold", True), ("wall_C", 680.0)]),
            ),
            (
                "gate_effect",
                "REJECT: acetic 9 -> 0 t/h. Wall IR left at 680 C under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held C-4. AE 52 pps beat wall 680 C by 180 us. IR was legal; "
                "the coil was not. 8 min cracker reset (abort_s=480) is delayed survey, not a "
                "process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held at 0 t/h acetic"),
                        ("wall", "left 680 C < 740 cap"),
                        ("coil", "8 min cracker reset (abort_s=480)"),
                        ("mission", "HIL ketene not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Wall IR never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min cracker reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.coil.pps (6.840 ms, 52 pps)"),
                        ("loser", "ir.wall.C (7.020 ms, 680 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 180 us inside the 320 us window would have "
                            "dispatched 9 t/h into a growling ketene coil. The REJECT is still "
                            "the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7640),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.640 ms, tick 4). The 8 min cracker "
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
            "thalamic-relay.ketene-ae",
            "spikenaut.policy.ketene-hold",
            [
                ("relay.ae.coil", "policy.ketene_hold", 0.70),
                ("relay.ir.wall", "policy.ir_go", 0.24),
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
                    pop_budget("ketene_hold", 56, 0.45, 280.0, 0.32),
                    pop("ir_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r83-433",
        "Ketene-Quoin KQ-HIL / Cracker C-4: coil AE 52 pps beats wall IR 680 C by 180 us; "
        "correct REJECT holds acetic",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 52 > 15 cap beats legal wall IR. total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "ketene-acetic-anhydride",
        ["reject", "hil", "ae-vs-ir", "growling-coil", "tick6-sidecar-bound"],
        "Teaches that a legal wall-IR header can lose to coil AE inside a 320 us "
        "window; reversing 180 us would have dispatched a growling ketene cracker.",
        3,
    )


def record_434():
    ticks = [
        tick(2880, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7200, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7380, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7840, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8200, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.jacket.C", 1.200, 0.40),
        spike("conv.vcm.pct", 2.880, 0.55),
        spike("tc.jacket.C", 4.400, 0.48),
        spike("conv.vcm.pct", 7.200, 1.26),
        spike("tc.jacket.C", 7.380, 1.08),
        spike("ctrl.gate", 7.840, 0.95),
        spike("conv.vcm.pct", 11.200, 0.78),
        spike("tc.jacket.C", 14.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("conv.vcm.pct", 22.600, 0.50),
        spike("tc.jacket.C", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(83434, 48, 28000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("vcm_tph", 11.0),
            ("conv_pct", 78.0),
            ("jacket_C", 62.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Suspension autoclave R-11 at Pvc-Lynchet PL-2 is already at 78 percent VCM "
                "conversion under a 92 percent drop-out, jacket 62 C vs 80. Confirming the "
                "11 t/h VCM charge is legal; treating the conversion GC as a runaway echo would "
                "have parked a healthy batch.",
            ),
            ("domain", "pvc-suspension-reactor"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the PL-2 suspension batch with conversion <= 92 percent and jacket <= 80 C.",
            ),
            ("t0_us", 1756850400000434),
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
                                "conv.vcm.pct 78 under 92 trip",
                                "tc.jacket.C 62 under 80 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Conversion-first confirms the already-legal 11.0 t/h VCM feed; jacket-first "
                            "would have treated the GC as a runaway echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one conversion-GC slot versus the jacket-TC publisher on this simulated PVC autoclave bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (GC 26 + TC 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed VCM feed illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "batch conversion GC, 26 us jitter",
                    "jacket TC well, 32 us jitter",
                    "VCM Coriolis (context)",
                    "agitator kW (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("conv_cap_pct", 92.0),
                        ("observed_conv_pct", 78.0),
                        ("jacket_cap_C", 80.0),
                        ("observed_jacket_C", 62.0),
                        ("pressure_bar", 9.4),
                        ("pressure_cap_bar", 12.0),
                        ("proposed_vcm_tph", 11.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. R-11 indexed on Pvc-Lynchet PL-2; 11.0 t/h VCM armed.",
                    "2. Caps: conversion 92 percent, jacket 80 C, pressure 12 bar.",
                    "3. Jacket-TC precursor at 1.200 ms.",
                    "4. Race window [7.200, 7.560] ms.",
                    "5. conv.vcm.pct 78 at 7.200 ms (winner).",
                    "6. tc.jacket.C 62 at 7.380 ms (loser by 180 us).",
                    "7. Gate at 7.840 ms: ACCEPT 11.0 t/h already legal.",
                    "8. VCM continues; no extra hold.",
                    "9. 6 min survey confirms conversion still under 92 percent.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "feed_vcm_11"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("conv_pct", 78.0),
                        ("conv_cap_pct", 92.0),
                        ("jacket_C", 62.0),
                        ("jacket_cap_C", 80.0),
                        ("pressure_bar", 9.4),
                        ("pressure_cap_bar", 12.0),
                        ("vcm_tph", 11.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes an 11.0 t/h VCM feed because conversion 78 percent is under "
                "92 and jacket 62 C is under 80 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Conversion 78 percent won by 180 us and is under 92. Jacket 62 C is under 80 C. "
                "Pressure 9.4 bar is under 12. ACCEPT the already-legal VCM feed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "conv_pct",
                            OrderedDict(
                                [
                                    ("cap", 92.0),
                                    ("observed", 78.0),
                                    ("executed_vcm_tph", 11.0),
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
            ("name", "feed_vcm_11"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 11.0 t/h VCM and 78 percent conversion unchanged. Routing relay.conv.vcm -> policy.vcm_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left R-11 on an 11.0 t/h / 78 percent conversion VCM feed. Jacket "
                "hitch did not justify a hold. 6 min survey confirmed conversion still under 92 percent.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "still 11.0 t/h VCM"),
                        ("conversion", "78 percent under 92 trip"),
                        ("jacket", "62 C under 80"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Jacket TC 62 C hitch is residual, not a runaway trip.",
                    "Delayed (survey_s=360): 6 min survey restacks R-11 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "conv.vcm.pct (7.200 ms, 78 percent)"),
                        ("loser", "tc.jacket.C (7.380 ms, 62 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Jacket-first by < 180 us would only delay confirmation. The VCM feed "
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
            "thalamic-relay.vcm-conv",
            "spikenaut.policy.vcm-go",
            [
                ("relay.conv.vcm", "policy.vcm_go", 0.68),
                ("relay.tc.jacket", "policy.jacket_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_vcm_stdp; 5-HT tags the vcm_go bind at the conversion-GC win",
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
                    pop_budget("vcm_go", 40, 0.45, 250.0, 0.36),
                    pop("jacket_hold", 32, 0.90),
                    pop("conv_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r83-434",
        "Pvc-Lynchet PL-2 / Autoclave R-11: conversion 78 percent beats jacket 62 C by 180 us; "
        "ACCEPT already-legal 11.0 t/h VCM",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal suspension VCM feed. total +1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "pvc-suspension-reactor",
        [
            "accept",
            "already-legal",
            "simulated-autoclave",
            "conv-vs-jacket",
            "sidecar-convictable",
            "simulated",
        ],
        "Teaches that a conversion GC under trip can confirm an already-legal VCM feed "
        "without a jacket-TC hitch becoming a hold.",
        4,
    )


def record_435():
    ticks = [
        tick(2016, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5040, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5920, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(240000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.meoh.tph", 0.980, 0.41),
        spike("tc.bed.C", 2.016, 0.60),
        spike("ft.meoh.tph", 3.200, 0.51),
        spike("tc.bed.C", 5.040, 1.30),
        spike("ft.meoh.tph", 5.200, 1.12),
        spike("ctrl.gate", 5.640, 0.97),
        spike("tc.bed.C", 8.100, 0.78),
        spike("ft.meoh.tph", 12.400, 0.62),
        spike("ctrl.gate", 16.200, 0.85),
        spike("tc.bed.C", 20.400, 0.54),
        spike("ft.meoh.tph", 22.800, 0.43),
    ]
    excerpt = independent_excerpt(83435, 80, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("meoh_tph", 9.6),
            ("bed_C", 248.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "DME converter D-3 on Dme-Wath DW-6 already sits at 248 C against a 270 C bed "
                "limit with methanol 9.6 t/h under a 12.0 t/h trip. Holding 9.6 t/h is already "
                "legal; a feed-first veto would have idled a quiet alumina bed.",
            ),
            ("domain", "dme-reactor"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run D-3 at 9.6 t/h methanol, keep bed <= 270 C and methanol <= 12.0 t/h, and "
                "leave the DME make on schedule.",
            ),
            ("t0_us", 1756850400000435),
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
                                "tc.bed.C 248 under 270 cap",
                                "ft.meoh.tph 9.6 under 12.0 trip",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first confirms the already-legal 9.6 t/h run; feed-first would "
                            "have treated the bed TC as a hitch echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one bed-TC slot versus the methanol-FT publisher on this DME converter bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (TC 22 + FT 30): 3.08x over a "
                            "2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal 9.6 t/h run.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed TC well, 2 kHz, 22 us jitter",
                    "methanol Coriolis, 1 kHz, 30 us jitter",
                    "DME GC (context)",
                    "recycle dP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 270.0),
                        ("observed_bed_C", 248.0),
                        ("meoh_tph", 9.6),
                        ("meoh_cap_tph", 12.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Converter D-3 indexed on Dme-Wath DW-6; 9.6 t/h methanol armed.",
                    "2. Bed 248 C under 270; methanol 9.6 t/h under 12.0.",
                    "3. Feed precursor at 0.980 ms.",
                    "4. Race window [5.040, 5.320] ms.",
                    "5. tc.bed.C 248 at 5.040 ms (winner).",
                    "6. ft.meoh.tph 9.6 at 5.200 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 9.6 t/h.",
                    "8. Bed stays 248 C; methanol stays 9.6 t/h.",
                    "9. DME make on-spec.",
                    "10. Delayed (dwell_s=240): 4 min recycle reseq.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_meoh_tph"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 248.0),
                        ("bed_cap_C", 270.0),
                        ("meoh_tph", 9.6),
                        ("meoh_cap_tph", 12.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 9.6 t/h methanol because bed 248 C is under 270 and methanol "
                "9.6 t/h is under 12.0.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed TC 248 C won by 160 us, so the converter is already legal, not still climbing. "
                "Methanol 9.6 t/h is under 12.0. ACCEPT the 9.6 t/h run. A REJECT would idle a legal DME bed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 270.0),
                                    ("observed", 248.0),
                                    ("executed_meoh_tph", 9.6),
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
            ("name", "hold_meoh_tph"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: leave 9.6 t/h methanol; bed 248 C; feed legal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 9.6 t/h DME run. Bed 248 C beat methanol "
                "9.6 t/h by 160 us. 4 min recycle reseq (dwell_s=240) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "9.6 t/h methanol held"),
                        ("bed", "248 C < 270 cap"),
                        ("converter", "D-3 on-spec"),
                        ("reseq", "4 min recycle reseq (dwell_s=240)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Methanol never approached 12.0 t/h; bed was already under cap.",
                    "Delayed (dwell_s=240): 4 min recycle reseq after make.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bed.C (5.040 ms, 248 C)"),
                        ("loser", "ft.meoh.tph (5.200 ms, 9.6 t/h)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Feed-first by < 160 us inside the 280 us window would have "
                            "REJECTED an already-legal 9.6 t/h run. The ACCEPT is still the "
                            "correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5640),
            (
                "reward_inflection_note",
                "Task and safety rise at the correct ACCEPT (5.640 ms, tick 4). The 4 min reseq "
                "is delayed surprise, not the inflection.",
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
            "thalamic-relay.dme-bed",
            "spikenaut.policy.dme-go",
            [
                ("relay.tc.bed", "policy.dme_go", 0.67),
                ("relay.ft.meoh", "policy.dme_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the bed-TC win as an already-legal DME run",
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
                    pop_budget("dme_go", 40, 0.45, 250.0, 0.28),
                    pop("dme_hold", 32, 0.90),
                    pop("bed_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r83-435",
        "Dme-Wath DW-6 / Converter D-3: bed 248 C beats methanol 9.6 t/h by 160 us; correct "
        "ACCEPT of an already-legal 9.6 t/h run",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Bed 248 < 270; methanol 9.6 < 12.0. total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
        ras,
        gate,
        "dme-reactor",
        ["accept", "designed", "bed-vs-feed", "already-legal-converter", "tick6-sidecar-bound"],
        "Teaches that a legal methanol header can lose to bed TC inside a 280 us window; "
        "reversing 160 us would have REJECTED an already-legal DME run.",
        5,
    )
