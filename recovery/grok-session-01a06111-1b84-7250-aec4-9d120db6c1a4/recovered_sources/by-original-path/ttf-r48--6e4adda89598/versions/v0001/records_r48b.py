def record_258():
    ticks = [
        tick(1568, 0.01, 0.04, 0.02, 0.01, 0.01),
        tick(3920, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(4110, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5100, 0.03, 0.12, 0.04, 0.04, 0.02),
        tick(5380, 0.02, 0.07, 0.01, 0.01, 0.01),
        tick(540000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.tow.ctx", 1.040, 0.44),
        spike("ir.skin.c", 2.180, 0.71),
        spike("enc.line.mpm", 3.020, 0.52),
        spike("ir.skin.c", 3.920, 1.36),
        spike("enc.line.mpm", 4.110, 1.14),
        spike("ctrl.gate", 5.100, 0.98),
        spike("ir.skin.c", 7.400, 0.82),
        spike("enc.line.mpm", 10.800, 0.61),
        spike("ctrl.gate", 16.200, 0.86),
        spike("ir.skin.c", 24.600, 0.70),
        spike("enc.line.mpm", 33.400, 0.48),
        spike("o2.oven.ctx", 41.200, 0.40),
    ]
    excerpt = independent_excerpt(48258, 112, 46000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Tow T-8 on the Precursor-Oxle oxidation HIL pad is pulling 18.4 m/min when an "
                "IR skin burst at 268 C on the PAN tow races the line encoder that still looks "
                "in-band for a speed step. Ramp is legal only if skin <= 240 C. IR-first latches "
                "hold; encoder-first would treat in-band speed as oven clearance.",
            ),
            ("domain", "carbon-fiber-oxidation"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not ramp Tow T-8 unless skin <= 240 C; keep line speed 0 m/min until the "
                "oven is quiet.",
            ),
            ("t0_us", 1762300000000258),
            ("gate_latency_us", 1180),
            ("race_window_us", 280),
            ("race_window_rel_ms", [3.920, 4.200]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.skin.c 268 C flare",
                                "enc.line.mpm 18.4 m/min still-in-band",
                            ],
                        ),
                        (
                            "semantics",
                            "IR-first latches REJECT hold 0 m/min; encoder-first would ramp 18.4 m/min "
                            "on an in-band-speed-as-clearance model.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one IR envelope slot versus the line-encoder publisher on this "
                            "pad cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 190 us vs combined jitter 54 us (IR 24 + encoder 30): 3.5x over a "
                            "2.0x trust floor. Pad injects encoder 90-130 us before the IR envelope "
                            "finishes (pyrometer lag, not a sensor fault); the encoder packet is still "
                            "the loser in this 280 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "PAN-tow skin IR, 24 us jitter, 240 C trip",
                    "line-speed encoder, 30 us jitter",
                    "oven O2 (context)",
                    "zone RTD (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("skin_trip_C", 240.0),
                        ("observed_skin_C", 268.0),
                        ("line_cap_m_min", 22.0),
                        ("proposed_m_min", 18.4),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("bench", "Precursor-Oxle PO-HIL oxidation pad, Tow T-8"),
                        ("inject", "IR envelope delayed 90-130 us vs encoder; pyrometer lag, not a false IR"),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Tow T-8 on Precursor-Oxle HIL pad; oven in band; line armed at 18.4 m/min.",
                    "2. Skin trip 240 C; observed 268 C flare on PAN tow.",
                    "3. Encoder precursor at 1.040 ms.",
                    "4. Race window [3.920, 4.200] ms.",
                    "5. IR 268 C at 3.920 ms (winner).",
                    "6. Line encoder 18.4 m/min at 4.110 ms (loser by 190 us).",
                    "7. Gate at 5.100 ms: REJECT hold 0 m/min, do not ramp.",
                    "8. Pad recycle 9 min; skin IR decays under 240 C after hold.",
                    "9. Oven never ignited; encoder-as-clearance would have ramped into the flare.",
                    "10. QA: correct gate was REJECT; leave 0 m/min until skin <= 240 C.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "ramp_18p4mpm"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("line_m_min", 18.4),
                        ("skin_C", 268.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("skin_C", 268.0),
                        ("skin_trip_C", 240.0),
                        ("line_m_min", 18.4),
                        ("line_cap_m_min", 22.0),
                        ("race_margin_us", 190),
                        ("combined_jitter_us", 54),
                        ("t_gate_us", 5100),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.4 m/min because line speed is under the 22.0 m/min cap and treats "
                "the encoder as oven clearance, ignoring the 268 C skin flare.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Skin 268 C won by 190 us and is over the 240 C trip. Encoder 18.4 m/min is under "
                "the 22.0 m/min cap but is not clearance. REJECT: hold 0 m/min until skin <= 240 C.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tow_skin_C",
                            OrderedDict(
                                [
                                    ("trip", 240.0),
                                    ("observed", 268.0),
                                    ("executed_m_min", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 190),
                                    ("combined_jitter_us", 54),
                                    ("ratio", 3.52),
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
            ("name", "tow_hold_ir"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("line_m_min", 0.0),
                        ("skin_C", 268.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: line 18.4 -> 0 m/min. Routing relay.ir.skin -> policy.hold_reject. "
                "Do not ramp into the 268 C flare.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Tow T-8 at 0 m/min while skin 268 C decayed. Encoder-as-clearance "
                "would have ramped 18.4 m/min into the flare. Pad recycle 9 min.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("tow", "held at 0 m/min"),
                        ("oven", "IR flare decaying under trip after hold"),
                        ("atmosphere", "unignited"),
                        ("pad", "9 min recycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Pad injects encoder 90-130 us before IR envelope finish; that is pyrometer lag, not a false IR.",
                    "Delayed (9 min): pad recycle restacks the line after skin < 240 C.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.skin.c (3.920 ms, 268 C)"),
                        ("loser", "enc.line.mpm (4.110 ms, 18.4 m/min)"),
                        ("margin_us", 190),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 190 us would have treated 18.4 m/min as clearance and "
                            "ramped into the 268 C flare. The REJECT is still required; reversal "
                            "only delays the IR bind.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5100),
            (
                "reward_inflection_note",
                "Safety credit lands at the correct REJECT (5.100 ms, tick 4). Pad recycle is delayed surprise.",
            ),
            ("delayed_surprise_s", 540.0),
            ("pad_recycle_s", 540),
        ]
    )
    ras = raster_core(
        46,
        112,
        20,
        103,
        routing(
            "relay.ir.skin",
            "policy.hold_reject",
            [
                ("relay.ir.skin", "policy.hold_reject", 0.74),
                ("relay.enc.line", "policy.ramp_go", 0.18),
            ],
            "dopamine",
            0.06,
            "ir_trip_stdp; DA tags the hold_reject bind at the IR win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.28),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 64, 0.50, 180.0, 3),
                    pop("ramp_go", 64, 0.80, 8.0, 0),
                    pop("skin_trip_veto", 32, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r48-258",
        "Precursor-Oxle oxidation HIL / Tow T-8: IR 268 C beats line encoder 18.4 m/min by 190 us; "
        "correct REJECT holds the tow",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. Skin 268 > 240 trip beats in-band line speed. total +0.78 = "
        "0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "carbon-fiber-oxidation",
        [
            "reject",
            "hil-pad",
            "ir-vs-encoder",
            "tow-flare-hold",
            "sidecar-convictable",
            "hil",
        ],
        "Teaches a probe that an in-band line encoder is not oven clearance when "
        "IR is over trip and routing.table[0].to is policy.hold_reject.",
        3,
    )


def record_259():
    ticks = [
        tick(2496, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(6240, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(6470, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(7140, 0.12, 0.08, 0.05, 0.03, 0.02),
        tick(7500, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(600000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    params = OrderedDict(
        [
            ("speed_m_min", 2.40),
            ("bed_C", 1280.0),
            ("grate_id", 4),
            ("hold", False),
        ]
    )
    spikes = [
        spike("ft.feed.ctx", 1.480, 0.42),
        spike("ir.bed.c", 3.120, 0.58),
        spike("dp.hood.smear", 4.660, 0.50),
        spike("ir.bed.c", 6.240, 1.28),
        spike("dp.hood.smear", 6.470, 1.10),
        spike("ctrl.gate", 7.140, 0.96),
        spike("ir.bed.c", 9.200, 0.74),
        spike("dp.hood.smear", 12.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("ir.bed.c", 24.600, 0.55),
        spike("ft.feed.ctx", 29.800, 0.40),
    ]
    excerpt = independent_excerpt(48259, 56, 30000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Grate G-4 of the Taconite-Sill induration train is traveling 2.40 m/min when a "
                "bed IR at 1280 C races a hood-Delta-P smear that still claims over-draft. "
                "Commanded 2.40 m/min and 1280 C sit 0.20 m/min and 70 C inside the legal "
                "envelopes. The IR win only ratifies the grate already on the hearth.",
            ),
            ("domain", "pellet-induration-grate"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the traveling-grate pass on Taconite-Sill, keep bed IR <= 1350 C and "
                "speed >= 2.20 m/min, and leave hood draft in spec.",
            ),
            ("t0_us", 1762300000000259),
            ("gate_latency_us", 900),
            ("race_window_us", 360),
            ("race_window_rel_ms", [6.240, 6.600]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.bed.c 1280 C pellet bed",
                                "dp.hood.smear over-draft claim",
                            ],
                        ),
                        (
                            "semantics",
                            "IR-first confirms the already-legal 2.40 m/min / 1280 C pass; "
                            "smear-first would have treated the IR as a smear echo and looked "
                            "for an extra hold the grate does not need.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one 1D-bed IR kernel step versus the hood-DP publisher "
                            "on this rigid grate train.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 70 us (IR 32 + DP 38): 3.3x over "
                            "a 2.0x trust floor. Reversing order by < 230 us would not make the "
                            "proposed pass illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "pellet-bed IR, 32 us jitter",
                    "hood DP smear, 38 us jitter",
                    "grate-speed encoder (context)",
                    "windbox PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 1350.0),
                        ("observed_bed_C", 1280.0),
                        ("speed_floor_m_min", 2.20),
                        ("proposed_speed_m_min", 2.40),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "1D traveling-grate induration + shrinking-core pellet kernel, seed 48; 12 axial nodes; NOT lumped tank, NOT a fluid-LES field",
                        ),
                        (
                            "fidelity_limits",
                            "No radial maldistribution or grate-bar leak; beds are rigid temperature sources. Raster is kernelized events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Taconite-Sill grate indexed; G-4 traveling 2.40 m/min at 1280 C bed.",
                    "2. Caps: bed 1350 C, speed floor 2.20 m/min; both proposed values inside.",
                    "3. Feed precursor at 1.480 ms.",
                    "4. Race window [6.240, 6.600] ms.",
                    "5. Bed IR 1280 C at 6.240 ms (winner).",
                    "6. Hood DP smear at 6.470 ms (loser by 230 us).",
                    "7. Gate at 7.140 ms: ACCEPT 2.40 m/min / 1280 C already legal.",
                    "8. Pass continues; no extra hold.",
                    "9. 10 min survey confirms hood draft still in spec.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "grate_2p40_thold"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 1280.0),
                        ("bed_cap_C", 1350.0),
                        ("speed_m_min", 2.40),
                        ("speed_floor_m_min", 2.20),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 70),
                        ("t_gate_us", 7140),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.40 m/min because bed 1280 C is 70 C under the 1350 C cap "
                "and speed is 0.20 m/min over the 2.20 m/min floor.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 1280 C won by 230 us and is under 1350 C. Speed 2.40 m/min is over "
                "2.20 m/min. ACCEPT the already-legal pass; hood DP smear is not a cap violation.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 1350.0),
                                    ("observed", 1280.0),
                                    ("executed_speed_m_min", 2.40),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 230),
                                    ("combined_jitter_us", 70),
                                    ("ratio", 3.29),
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
            ("name", "grate_2p40_thold"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: speed 2.40 m/min and bed 1280 C unchanged. Routing relay.ir.bed "
                "-> policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left Grate G-4 at 2.40 m/min / 1280 C. Hood DP smear did not justify a "
                "hold. 10 min survey confirmed draft in spec.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("grate", "still 2.40 m/min / 1280 C"),
                        ("hood", "in spec after survey"),
                        ("train", "induration continues"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Hood DP smear is a windbox optical claim, not a bed-temperature violation.",
                    "Delayed (10 min): survey restacks Grate G-4 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.bed.c (6.240 ms, 1280 C)"),
                        ("loser", "dp.hood.smear (6.470 ms, over-draft claim)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "Smear-first by < 230 us would only delay confirmation. The pass stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7140),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (7.140 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 600.0),
            ("survey_s", 600),
        ]
    )
    ras = raster_core(
        30,
        56,
        38,
        64,
        routing(
            "relay.ir.bed",
            "policy.go_accept",
            [
                ("relay.ir.bed", "policy.go_accept", 0.68),
                ("relay.dp.hood", "policy.smear_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_grate_stdp; 5-HT tags the go_accept bind at the bed-IR win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("go_accept", 40, 0.50, 180.0, 3),
                    pop("smear_hold", 40, 0.80, 10.0, 0),
                    pop("bed_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r48-259",
        "Taconite-Sill grate / G-4: bed IR 1280 C beats hood DP smear by 230 us; ACCEPT "
        "already-legal 2.40 m/min pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal 1D traveling-grate pass. total +1.06 = "
        "0.42 + 0.28 + 0.18 + 0.10 + 0.08.",
        ras,
        gate,
        "pellet-induration-grate",
        [
            "accept",
            "already-legal",
            "simulated-grate-train",
            "ir-vs-dp",
            "sidecar-convictable",
            "simulated",
        ],
        "Teaches that a bed IR under cap can confirm an already-legal grate pass without "
        "a hood-draft smear becoming a hold.",
        4,
    )


def record_260():
    ticks = [
        tick(1672, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(4180, 0.10, 0.08, 0.04, 0.02, 0.02),
        tick(4360, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(4940, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5240, 0.06, 0.05, 0.02, 0.01, 0.01),
        tick(420000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    params = OrderedDict(
        [
            ("feed_t_h", 18.0),
            ("tmt_C", 1048.0),
            ("coil_id", 12),
            ("hold", False),
        ]
    )
    spikes = [
        spike("enc.gap.ctx", 0.920, 0.41),
        spike("ir.tmt.c", 2.140, 0.60),
        spike("dp.coil.kpa", 3.080, 0.51),
        spike("ir.tmt.c", 4.180, 1.30),
        spike("dp.coil.kpa", 4.360, 1.12),
        spike("ctrl.gate", 4.940, 0.97),
        spike("ir.tmt.c", 6.800, 0.78),
        spike("dp.coil.kpa", 9.200, 0.62),
        spike("ctrl.gate", 13.600, 0.85),
        spike("ir.tmt.c", 18.400, 0.54),
        spike("dp.coil.kpa", 21.200, 0.43),
    ]
    excerpt = independent_excerpt(48260, 48, 24000, 11, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Coil C-12 at Ethene-Veld furnace 3 is armed for an 18.0 t/h pass when a tube-metal "
                "IR at 1048 C races a coil Delta-P that still claims a hitch. Commanded 18.0 t/h "
                "and 1048 C sit 2.0 t/h over the 16.0 t/h floor and 32 C under the 1080 C cap. The "
                "IR win only ratifies the pass already on the coil.",
            ),
            ("domain", "steam-cracker-coil"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run Coil C-12 at 18.0 t/h, keep TMT <= 1080 C and coil DP <= 25 kPa, "
                "and leave the furnace on schedule.",
            ),
            ("t0_us", 1762300000000260),
            ("gate_latency_us", 760),
            ("race_window_us", 300),
            ("race_window_rel_ms", [4.180, 4.480]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.tmt.c 1048 C tube-metal",
                                "dp.coil.kpa 12 kPa hitch claim",
                            ],
                        ),
                        (
                            "semantics",
                            "TMT-first confirms the already-legal 18.0 t/h / 1048 C pass; DP-first "
                            "would have treated the IR as a hitch echo and looked for an extra hold "
                            "the furnace does not need.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one tube-metal IR slot versus the coil-DP publisher on this "
                            "cracker bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (IR 28 + DP 30): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed pass illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "tube-metal IR, 28 us jitter",
                    "coil DP, 30 us jitter",
                    "feed encoder (context)",
                    "COT pyrometer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("tmt_cap_C", 1080.0),
                        ("observed_tmt_C", 1048.0),
                        ("feed_floor_t_h", 16.0),
                        ("proposed_feed_t_h", 18.0),
                        ("dp_cap_kPa", 25.0),
                        ("observed_dp_kPa", 12.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Coil C-12 indexed on Ethene-Veld furnace 3; feed armed 18.0 t/h pass.",
                    "2. Caps: TMT 1080 C, coil DP 25 kPa, feed floor 16.0 t/h.",
                    "3. Encoder precursor at 0.920 ms.",
                    "4. Race window [4.180, 4.480] ms.",
                    "5. TMT IR 1048 C at 4.180 ms (winner).",
                    "6. Coil DP 12 kPa at 4.360 ms (loser by 180 us).",
                    "7. Gate at 4.940 ms: ACCEPT 18.0 t/h / 1048 C already legal.",
                    "8. Pass continues; no extra hold.",
                    "9. 7 min cooldown confirms coil DP still under 25 kPa.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "pass_18th"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("tmt_C", 1048.0),
                        ("tmt_cap_C", 1080.0),
                        ("feed_t_h", 18.0),
                        ("feed_floor_t_h", 16.0),
                        ("dp_kPa", 12.0),
                        ("dp_cap_kPa", 25.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("t_gate_us", 4940),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes an 18.0 t/h pass because TMT 1048 C is 32 C under the 1080 C "
                "cap and coil DP 12 kPa is under 25 kPa.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "TMT 1048 C won by 180 us and is under 1080 C. Coil DP 12 kPa is under "
                "25 kPa. Feed 18.0 t/h is over the 16.0 t/h floor. ACCEPT the already-legal pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tmt_C",
                            OrderedDict(
                                [
                                    ("cap", 1080.0),
                                    ("observed", 1048.0),
                                    ("executed_feed_t_h", 18.0),
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
            ("name", "pass_18th"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 18.0 t/h pass and 1048 C TMT unchanged. Routing relay.ir.tmt -> "
                "policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left Coil C-12 on an 18.0 t/h / 1048 C pass. Coil DP hitch did not "
                "justify a hold. 7 min cooldown confirmed DP still under 25 kPa.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("coil", "still 18.0 t/h / 1048 C"),
                        ("dp", "12 kPa under 25 cap"),
                        ("furnace", "on schedule"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Coil DP 12 kPa hitch is residual, not a coking trip.",
                    "Delayed (7 min): cooldown restacks C-12 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.tmt.c (4.180 ms, 1048 C)"),
                        ("loser", "dp.coil.kpa (4.360 ms, 12 kPa)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "DP-first by < 180 us would only delay confirmation. The pass stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4940),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (4.940 ms, tick 4). Cooldown is delayed surprise.",
            ),
            ("delayed_surprise_s", 420.0),
            ("cooldown_s", 420),
        ]
    )
    ras = raster_core(
        24,
        48,
        42,
        48,
        routing(
            "relay.ir.tmt",
            "policy.go_accept",
            [
                ("relay.ir.tmt", "policy.go_accept", 0.66),
                ("relay.dp.coil", "policy.hitch_hold", 0.20),
            ],
            "dopamine",
            0.04,
            "legal_pass_stdp; DA tags the go_accept bind at the tube-metal win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.30),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("go_accept", 40, 0.50, 160.0, 2),
                    pop("hitch_hold", 40, 0.80, 10.0, 0),
                    pop("tmt_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r48-260",
        "Ethene-Veld furnace 3 / Coil C-12: TMT 1048 C beats coil DP 12 kPa by 180 us; "
        "ACCEPT already-legal 18.0 t/h pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal steam-cracker pass. total +1.14 = "
        "0.44 + 0.32 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "steam-cracker-coil",
        [
            "accept",
            "already-legal",
            "tmt-vs-coil-dp",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches that a tube-metal IR under cap can confirm an already-legal pass without "
        "a coil-DP hitch becoming a hold.",
        5,
    )
