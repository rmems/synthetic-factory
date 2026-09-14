def record_361():
    excerpt, extra = lif_361_excerpt()
    extra = OrderedDict(extra)
    extra["abort_s"] = 840
    extra["delayed_surprise_s"] = 840
    ticks = [
        tick(2440, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6120, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(6308, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6840, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22400, 0.04, -0.45, -0.03, -0.01, -0.01),
        tick(840000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Converter C-2 at Fayalite-Hope FH-3 is blasting 38 kNm3/h of tuyere air while "
                "matte bath sits at 1248 C against a 1220 C tuyere-air cap. Temperature-first "
                "cuts blast to 29 kNm3/h; blast-first would keep 38 kNm3/h because the blower "
                "3420 rpm is still under the 3600 rpm stall ceiling. A punched-out tuyere already "
                "seated over the aisle does not appear on bath T or blast FT until the AE dump.",
            ),
            ("domain", "peirce-smith-converter"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep Converter C-2 bath <= 1220 C and finish the copper blow without dumping "
                "matte onto the converter aisle.",
            ),
            ("t0_us", 1756850400000361),
            ("gate_latency_us", 720),
            ("race_window_us", 400),
            ("race_window_rel_ms", [6.0, 6.40]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.bath.C 1248 over 1220 tuyere-air cap",
                                "ft.blast.kNm 38 with blower 3420 under 3600",
                            ],
                        ),
                        (
                            "semantics",
                            "Temperature-first latches blast clamp 38 -> 29 kNm3/h; "
                            "blast-first keeps 38 kNm3/h on a 'still under blower-stall ceiling' model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one bath-TC slot versus the blast-air FT publisher on this "
                            "converter skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 188 us vs combined jitter 64 us (TC 30 + FT 34): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 188 us inside the 400 us "
                            "window would have kept 38 kNm3/h; predicted next-sample 1256 C > 1220 "
                            "tuyere-air cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bath thermocouple lance, 2 kHz, 30 us jitter",
                    "tuyere blast FT + blower tach, 1 kHz, 34 us jitter",
                    "tuyere AE puck (context)",
                    "aisle IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bath_cap_C", 1220.0),
                        ("observed_bath_C", 1248.0),
                        ("blast_kNm3_h", 38.0),
                        ("blower_rpm", 3420.0),
                        ("blower_cap_rpm", 3600.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Converter C-2 in copper blow; blast 38 kNm3/h; bath 1248 C.",
                    "2. Blower 3420 rpm under 3600 stall; blow armed.",
                    "3. Blast-FT precursor at 1.180 ms.",
                    "4. Race window [6.000, 6.400] ms.",
                    "5. tc.bath.C 1248 C at 6.120 ms (winner).",
                    "6. ft.blast.kNm 38 at 6.308 ms (loser by 188 us).",
                    "7. Gate at 6.840 ms: MODIFY clamp 38 -> 29 kNm3/h.",
                    "8. After clamp bath 1212 C <= 1220; blower still 3420 rpm.",
                    "9. At 22.400 ms a punched-out tuyere dumps 0.6 t of matte onto the aisle.",
                    "10. 14 min aisle fire watch (abort_s=840); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_tuyere_blast"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("blast_kNm3_h", 38.0),
                        ("bath_C", 1248.0),
                        ("blower_rpm", 3420.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bath_C", 1248.0),
                        ("bath_cap_C", 1220.0),
                        ("predicted_unclamped_next_C", 1256.0),
                        ("blast_kNm3_h", 38.0),
                        ("blower_rpm", 3420.0),
                        ("blower_cap_rpm", 3600.0),
                        ("race_margin_us", 188),
                        ("combined_jitter_us", 64),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 38 kNm3/h because blower 3420 rpm is under 3600, treating the "
                "1248 C bath as a still-sooty lance rather than a tuyere-air miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bath 1248 C won by 188 us, so the converter is over the 1220 C tuyere-air "
                "cap, not still a blower-stall story. Holding 38 kNm3/h predicts next-sample "
                "1256 C > 1220. MODIFY: blast 38 -> 29 kNm3/h. Observed after clamp 1212 C <= "
                "1220. A full REJECT is not indicated: a clean copper blow accepts 29 kNm3/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bath_C",
                            OrderedDict(
                                [
                                    ("cap", 1220.0),
                                    ("observed", 1248.0),
                                    ("predicted_unclamped_next", 1256.0),
                                    ("clamped_blast_kNm3_h", 29.0),
                                    ("observed_after_clamp", 1212.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 188),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 2.94),
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
            ("name", "clamped_tuyere_blast"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("blast_kNm3_h", 29.0),
                        ("bath_C", 1212.0),
                        ("blower_rpm", 3420.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: blast 38 -> 29 kNm3/h. Process-correct vs the 1220 C tuyere-air cap. "
                "Punched tuyere still dumps at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held bath at 1212 C. At 22.400 ms a punched-out tuyere "
                "already seated over the aisle dumped 0.6 t of matte onto the floor. Clamp "
                "reduced dump energy; it did not prevent the dump. Partnered negative: process "
                "heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bath", "clamp executed; peak 1212 C <= 1220 cap"),
                        ("tuyere", "punch-out dump at 22.400 ms; 0.6 t matte"),
                        ("repair", "14 min aisle fire watch (abort_s=840)"),
                        ("mission", "FH-3 copper blow incomplete this cycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither bath T nor blast FT predicted the seated tuyere punch-out; ae.tuyere.dump is a new channel at 22.400 ms, 15.560 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=840): 14 min aisle fire watch. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "14 min aisle fire watch after the tuyere punch-out. Safety head -0.64 "
                "prices the dump; task_progress stays +0.30 because the clamp completed.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bath.C (6.120 ms, 1248 C)"),
                        ("loser", "ft.blast.kNm (6.308 ms, 38 kNm3/h)"),
                        ("margin_us", 188),
                        (
                            "counterfactual_if_reversed",
                            "Blast-first by < 188 us inside the 400 us window would have kept "
                            "38 kNm3/h; predicted next-sample 1256 C would have missed the 1220 "
                            "tuyere-air cap even without the punch-out. The MODIFY is still the "
                            "correct process. The dump is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms tuyere punch-out (tick t_us=22400), inside "
                "the 42 ms raster. The correct MODIFY at 6.840 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=840 fire-watch tick.",
            ),
        ]
    )
    spikes = [
        spike("ft.blast.ctx", 1.180, 0.41),
        spike("tc.bath.C", 2.440, 0.58),
        spike("ft.blast.kNm", 3.880, 0.50),
        spike("tc.bath.C", 6.120, 1.31),
        spike("ft.blast.kNm", 6.308, 1.12),
        spike("ctrl.gate", 6.840, 0.97),
        spike("tc.bath.C", 8.200, 0.82),
        spike("ft.blast.kNm", 10.550, 0.64),
        spike("ctrl.gate", 14.100, 0.86),
        spike("ae.tuyere.dump", 22.400, 1.48),
        spike("ae.tuyere.dump", 24.200, 0.93),
        spike("ft.blast.ctx", 29.800, 0.40),
        spike("tc.bath.C", 36.200, 0.55),
    ]
    ras = raster_core(
        42,
        76,
        24,
        77,
        routing(
            "thalamic-relay.fh-bath",
            "spikenaut.policy.blast-clamp",
            [
                ("relay_bath_C", "policy_blast_clamp", 0.68),
                ("relay_blast_ft", "policy_blast_hold", 0.29),
                ("relay_ae_tuyere", "policy_blast_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at bath win (6.120 ms) opens a 42 ms "
            "eligibility trace that still covers the 22.400 ms tuyere punch-out",
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
                    pop("blast_clamp", 50, 0.50, 200.0, 4),
                    pop("blast_hold", 40, 0.80, 50.0, 1),
                    pop("tuyere_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r69-361"),
            (
                "title",
                "Fayalite-Hope FH-3 / Converter C-2: bath 1248 C beats blast 38 kNm3/h by 188 us; "
                "correct MODIFY still eats an in-window tuyere punch-out (partnered negative total -0.48)",
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
                    "42 ms raster. total -0.48 = 0.30 + -0.64 + -0.14 + 0.04 + -0.04. Named "
                    "aisle fire watch (abort_s=840) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "peirce-smith-converter",
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
                    "14 min aisle fire watch.",
                    1,
                ),
            ),
        ]
    )


def record_362():
    ticks = [
        tick(2210, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5480, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5662, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6020, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6400, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(540000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.cycle.ctx", 1.050, 0.42),
        spike("o2.live.pct", 2.210, 0.57),
        spike("fv.small.stem", 3.080, 0.88),
        spike("o2.live.pct", 5.480, 1.29),
        spike("fv.small.stem", 5.662, 1.10),
        spike("ctrl.gate", 6.020, 0.96),
        spike("fv.large.stem", 6.400, 1.18),
        spike("o2.live.pct", 7.800, 0.80),
        spike("fv.small.stem", 10.200, 0.63),
        spike("ctrl.gate", 13.500, 0.84),
        spike("enc.cycle.ctx", 18.400, 0.41),
        spike("o2.live.pct", 22.100, 0.54),
        spike("fv.large.stem", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(69362, 100, 30000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Working oxidizer OX-4 at Anthraq-Force AF-6 still prints live off-gas O2 8.40 "
                "percent against a 6.00 percent working-O2 cap, with split-range air already "
                "filed at FV-11A small 28 percent plus FV-11B large 62 percent. Both halves are "
                "LIVE on the same vessel. Live-O2-first should MODIFY the LARGE half 62 -> 18 "
                "percent; a weak supervisor binds the small-trim stem and MODIFY-closes FV-11A "
                "28 -> 4 percent while FV-11B stays 62.",
            ),
            ("domain", "hydrogen-peroxide-ao"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Cut working-air on the LARGE split-range half until live O2 stays <= 6.00 "
                "percent; do not spend the cut on the small-trim half.",
            ),
            ("t0_us", 1756850400000362),
            ("gate_latency_us", 540),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.4, 5.76]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "o2.live.pct 8.40 percent on the working oxidizer",
                                "fv.small.stem 28 percent small-trim encoder",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-O2-first should latch a large-half cut 62 -> 18 percent; "
                            "small-stem-first is a false 'trim still high' bind that closes only "
                            "the 0-30 percent half.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one live-O2 sample versus the small-valve stem publisher "
                            "on this oxidizer PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 182 us vs combined jitter 60 us (O2 28 + stem 32). Order is "
                            "correctly live-O2-first. The error is which split-range half the "
                            "MODIFY binds, not the race order.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "working-oxidizer zirconia O2, 4 Hz packet, 28 us jitter on this sample",
                    "FV-11A small-trim stem encoder, 32 us jitter",
                    "FV-11B large-half stem (context)",
                    "working-liquor PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_O2_pct", 6.00),
                        ("live_O2_pct", 8.40),
                        ("small_half_pct", 28.0),
                        ("large_half_pct", 62.0),
                        ("small_span_pct", 30.0),
                        ("both_halves_live", True),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. OX-4 in working oxidation; split-range air 28 / 62 percent armed.",
                    "2. Live O2 8.40 > 6.00 cap; both halves LIVE on the same vessel.",
                    "3. Small-stem sampled at 3.080 ms.",
                    "4. Race window [5.400, 5.760] ms.",
                    "5. o2.live.pct 8.40 at 5.480 ms (winner).",
                    "6. fv.small.stem 28 percent at 5.662 ms (loser by 182 us).",
                    "7. Gate at 6.020 ms: WRONG MODIFY small half 28 -> 4 percent; large stays 62.",
                    "8. split_range_half=small; large_half_pct unchanged 62; O2 stays 8.12 > 6.00.",
                    "9. Working liquor remains over-oxidized for the rest of the pass.",
                    "10. Delayed (abort_s=540): 9 min off-spec AO working window.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_split_range_air"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("small_half_pct", 28.0),
                        ("large_half_pct", 62.0),
                        ("split_range_half", "none"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_O2_pct", 8.40),
                        ("cap_O2_pct", 6.00),
                        ("small_half_pct", 28.0),
                        ("large_half_pct", 62.0),
                        ("both_halves_live", True),
                        ("live_over_cap", True),
                        ("race_margin_us", 182),
                        ("combined_jitter_us", 60),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping 28 / 62 percent split-range air because 8.40 percent "
                "O2 is treated as a wet-cell smear rather than a working-O2 miss. Live 8.40 is "
                "over the 6.00 cap; the correct gate cuts the LARGE half.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Live O2 8.40 percent is over the 6.00 cap, so a cut is required. A weak "
                "supervisor binds the small-trim stem that lost the race and MODIFY-closes "
                "FV-11A 28 -> 4 percent, leaving FV-11B at 62 percent. Both halves are LIVE; "
                "the small half cannot dump the air. The MODIFY is plausible to a supervisor "
                "that treats split-range as a single valve.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "O2_pct",
                            OrderedDict(
                                [
                                    ("cap", 6.00),
                                    ("live", 8.40),
                                    ("executed_small_half_pct", 4.0),
                                    ("executed_large_half_pct", 62.0),
                                ]
                            ),
                        ),
                        (
                            "split_range",
                            OrderedDict(
                                [
                                    ("half_bound", "small"),
                                    ("both_halves_live", True),
                                    ("large_unchanged", True),
                                    ("t_gate_us", 6020),
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
            ("name", "small_half_trim"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("small_half_pct", 4.0),
                        ("large_half_pct", 62.0),
                        ("split_range_half", "small"),
                        ("both_halves_live", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "WRONG MODIFY: small half 28 -> 4 percent; large half left at 62. Live O2 "
                "8.40 remains over 6.00. split_range_half=small.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-modify / split-range-wrong-half. Live working O2 8.40 stayed over the "
                "6.00 cap. The supervisor closed only the small trim to 4 percent and left the "
                "large half at 62 percent. Nine minutes of off-spec AO working (abort_s=540).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("small_half", "trimmed; 4 percent vs filed 28"),
                        ("large_half", "unchanged; 62 percent still dumping air"),
                        ("live_O2", "8.12 percent still over 6.00"),
                        ("mission", "AF-6 working pass over-oxidized"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live O2 winning a 182 us race did not prevent a small-half MODIFY; reversing order would still have been a wrong bind if the supervisor keyed on the trim stem.",
                    "Delayed (abort_s=540): 9 min off-spec AO working window. Named un-netted loss.",
                ],
            ),
            (
                "recovery",
                "MODIFY; cut LARGE half FV-11B 62 -> 18 percent; leave small half at 28 percent; "
                "bind live O2; do not spend a working-O2 cut on the 0-30 percent trim while "
                "both_halves_live is true.",
            ),
            (
                "cost",
                OrderedDict(
                    [
                        ("actual_live_O2_pct", 8.40),
                        ("actual_cap_O2_pct", 6.00),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("small_half_pct", 4.0),
                                    ("large_half_pct", 62.0),
                                    ("split_range_half", "small"),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "9 min off-spec AO working (task/efficiency); legal large-half cut "
                            "was skipped so live 8.40 stayed over 6.00 (safety of a false trim).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "o2.live.pct (5.480 ms, 8.40 percent)"),
                        ("loser", "fv.small.stem (5.662 ms, 28 percent)"),
                        ("margin_us", 182),
                        (
                            "counterfactual_if_reversed",
                            "Small-stem-first by < 182 us would still leave live 8.40 over cap; a "
                            "correct gate binds o2.live.pct to policy_large_cut either way. The "
                            "wrong MODIFY spent the live win on a small-trim clamp.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6020),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong MODIFY (6.020 ms, tick 4). "
                "The 9 min AO miss is delayed surprise, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        30,
        100,
        30,
        90,
        routing(
            "thalamic-relay.ao-o2",
            "spikenaut.policy.small-trim",
            [
                ("relay_o2_live", "policy_small_trim", 0.73),
                ("relay_fv_small", "policy_small_trim", 0.22),
            ],
            "acetylcholine",
            0.08,
            "split_range_stdp; ACh tags the (wrong) small_trim bind at the live-O2 win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 540),
                ("delayed_surprise_s", 540),
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
                    pop("small_trim", 42, 0.45, 280.0, 4),
                    pop("large_cut", 42, 0.90),
                    pop("o2_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r69-362"),
            (
                "title",
                "WRONG-MODIFY at Anthraq-Force AF-6 / Oxidizer OX-4: live O2 8.40 over cap; "
                "air cut spent on small split-range half (split-range-wrong-half)",
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
                    "Wrong-modify / split-range-wrong-half. Sidecar arithmetic live 8.40 > 6.00 "
                    "is true and large_half_pct stays 62; MODIFY bound the small trim. "
                    "total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "hydrogen-peroxide-ao",
                    [
                        "modify",
                        "wrong-gate",
                        "split-range-wrong-half",
                        "large-half-unchanged",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live-O2-first race can still be a wrong gate "
                    "when routing.table[0].to is policy_small_trim and large_half_pct is unchanged. "
                    "Convictable from live_O2_pct vs cap_O2_pct without AO chemistry.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_363():
    ticks = [
        tick(2810, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(7040, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7218, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7900, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(8200, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(360000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("tc.crust.ctx", 1.420, 0.43),
        spike("ae.crust.pps", 2.880, 0.61),
        spike("enc.elec.m", 4.550, 0.49),
        spike("ae.crust.pps", 7.040, 1.34),
        spike("enc.elec.m", 7.218, 1.11),
        spike("ctrl.gate", 7.900, 1.02),
        spike("ae.crust.pps", 10.200, 0.78),
        spike("tc.crust.ctx", 14.800, 0.44),
        spike("enc.elec.m", 19.400, 0.58),
        spike("ctrl.gate", 24.600, 0.81),
        spike("ae.crust.pps", 31.200, 0.53),
        spike("enc.elec.m", 38.800, 0.46),
        spike("tc.crust.ctx", 44.100, 0.37),
    ]
    excerpt = independent_excerpt(69363, 120, 48000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Furnace F-1 on the Acetylene-Dell AD-HIL pad is armed for a 0.18 m/min electrode "
                "lower while a crust-break AE packet reads 48 pps against a 12 pps move cap. An "
                "electrode encoder, lit by the pad lamp, still reads 6.2 m under an 8.0 m travel "
                "look. AE-first latches REJECT hold; encoder-first would commit a 0.18 m/min "
                "lower into a live crust.",
            ),
            ("domain", "calcium-carbide-furnace"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not lower Furnace F-1 electrodes unless crust AE <= 12 pps; keep slip "
                "0.0 m/min until the injected crust recovers.",
            ),
            ("t0_us", 1756850400000363),
            ("gate_latency_us", 860),
            ("race_window_us", 290),
            ("race_window_rel_ms", [6.95, 7.24]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.crust.pps 48 pps",
                                "enc.elec.m 6.2 m under 8.0",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches REJECT hold 0.0 m/min slip; encoder-first would "
                            "commit a 0.18 m/min lower on an apparent 6.2 m under-read.",
                        ),
                        (
                            "window_derivation",
                            "290 us = one crust-AE sample versus encoder integration on this "
                            "carbide HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 178 us vs combined jitter 56 us (AE 24 + ENC 32): 3.2x over a "
                            "2.0x trust floor. Pad injects the encoder lamp 120-160 us before the "
                            "AE (geometric lag, not a sensor fault); the 6.2 m packet is still "
                            "the loser in this 290 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "crust-break AE puck, 5 kHz burst, 24 us jitter",
                    "electrode slip encoder, 200 Hz, 32 us jitter",
                    "crust thermocouple (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 12.0),
                        ("observed_ae_pps", 48.0),
                        ("elec_m", 6.2),
                        ("elec_look_m", 8.0),
                        ("proposed_slip_m_min", 0.18),
                        ("lamp_inject_lead_us", [120, 160]),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("pad", "Acetylene-Dell AD-HIL carbide furnace mockup with physical electrode slip"),
                        ("injected", "crust-break AE burst + encoder lamp spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop calcium-carbide furnace. Invented plant; not a live acetylene shop.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Furnace F-1 on the AD-HIL pad; 0.18 m/min slip armed.",
                    "2. Encoder lamp injected 120-160 us before AE sees 48 pps.",
                    "3. Crust-TC precursor at 1.420 ms.",
                    "4. Race window [6.950, 7.240] ms.",
                    "5. ae.crust.pps 48 pps at 7.040 ms (winner).",
                    "6. enc.elec.m 6.2 m at 7.218 ms (loser by 178 us).",
                    "7. Gate at 7.900 ms: REJECT hold 0.0 m/min; do not lower 0.18.",
                    "8. Crust remains over 12 pps this cycle; slip cap held.",
                    "9. Electrode re-seat queued on the pad.",
                    "10. Delayed (abort_s=360): 6 min crust re-break and lamp-spectrum retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "lower_carbide_electrode"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("slip_m_min", 0.18),
                        ("hold", False),
                        ("encoder_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 48.0),
                        ("ae_cap_pps", 12.0),
                        ("elec_m", 6.2),
                        ("elec_look_m", 8.0),
                        ("race_margin_us", 178),
                        ("combined_jitter_us", 56),
                        ("abort_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 0.18 m/min electrode lower because encoder 6.2 m looks under "
                "the 8.0 m travel look, treating AE 48 pps as a noisy bus echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Crust AE 48 pps is over the 12 pps electrode-move cap. Encoder 6.2 m is a HIL "
                "lamp under-read, not a clearance. REJECT: hold 0.0 m/min; do not commit a "
                "0.18 m/min lower.",
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
                                    ("elec_m", 6.2),
                                ]
                            ),
                        ),
                        (
                            "slip_m_min",
                            OrderedDict([("proposed", 0.18), ("executed", 0.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 178),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 3.18),
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
            ("name", "hold_for_crust_drop"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("slip_m_min", 0.0),
                        ("hold", True),
                        ("encoder_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0.0 m/min; 0.18 m/min lower cancelled. AE 48 > 12 pps cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Furnace F-1 at 0.0 m/min slip. Crust over cap this cycle; "
                "slip cap held. Encoder apparent was not treated as an AE clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("slip", "held; 0.0 m/min"),
                        ("crust", "still over 12 pps this cycle"),
                        ("encoder", "6.2 m unused as clearance"),
                        ("mission", "lower deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: encoder lamp was injected 120-160 us before the AE puck, yet crust AE still won the 290 us race.",
                    "Delayed (abort_s=360): pad policy update forbids treating electrode encoder m as a crust-AE substitute after a 6 min re-break.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.crust.pps (7.040 ms, 48 pps)"),
                        ("loser", "enc.elec.m (7.218 ms, 6.2 m)"),
                        ("margin_us", 178),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 178 us inside the 290 us window would have committed "
                            "a 0.18 m/min lower with AE 48 > 12 pps cap. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7900),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (7.900 ms, tick 4) as the hold "
                "lands. The 6 min re-break is delayed surprise bound to abort_s=360.",
            ),
        ]
    )
    ras = raster_core(
        48,
        120,
        18,
        104,
        routing(
            "thalamic-relay.carbide-ae",
            "spikenaut.policy.slip-hold",
            [
                ("relay_ae_pps", "policy_slip_hold", 0.70),
                ("relay_enc_elec", "policy_enc_lower", 0.24),
            ],
            "dopamine",
            0.15,
            "ae_hold_stdp; DA tags the slip_hold bind at the crust-AE win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 360),
                ("delayed_surprise_s", 360),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.29),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("slip_hold", 70, 0.48, 250.0, 5),
                    pop("enc_lower", 50, 0.85),
                    pop("ae_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r69-363"),
            (
                "title",
                "Acetylene-Dell AD-HIL / Furnace F-1: crust AE 48 pps beats electrode encoder 6.2 m "
                "by 178 us; correct REJECT holds the electrode slip",
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
                    "Correct REJECT. Crust AE over cap beats encoder under-read. "
                    "total 0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06. Tick 6 binds abort_s=360.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "calcium-carbide-furnace",
                    [
                        "reject",
                        "hil",
                        "crust-ae",
                        "encoder-underread",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a HIL electrode-encoder under-read losing a 178 us race does not "
                    "clear a crust-AE over-rate. Hold is distillable from pps vs cap.",
                    3,
                ),
            ),
        ]
    )


def record_364():
    ticks = [
        tick(3220, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(8120, 0.08, 0.05, 0.04, 0.03, 0.02),
        tick(8310, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(8520, 0.12, 0.09, 0.05, 0.04, 0.02),
        tick(8980, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(120000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.lift.ctx", 1.105, 0.43),
        spike("tc.bed.C", 3.220, 0.59),
        spike("ir.cyclone.C", 5.010, 0.50),
        spike("tc.bed.C", 8.120, 1.27),
        spike("ir.cyclone.C", 8.310, 1.09),
        spike("ctrl.gate", 8.520, 0.97),
        spike("tc.bed.C", 11.200, 0.78),
        spike("ir.cyclone.C", 14.880, 0.61),
        spike("ctrl.gate", 18.400, 0.84),
        spike("tc.bed.C", 22.050, 0.56),
        spike("enc.lift.ctx", 24.100, 0.40),
    ]
    excerpt = independent_excerpt(69364, 56, 26000, 13, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("feed_t_h", 18.0),
            ("bed_C", 84.2),
            ("cyclone_C", 62.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Reactor R-8 at Propene-Ayre PA-11 is already holding the fluidized PP bed at "
                "84.2 C under an 88.0 C agglomeration cap with an 18.0 t/h propylene feed already "
                "filed under the 22.0 t/h inlet ceiling. Cyclone-IR-first would extra-clamp a "
                "legal bed; bed-first ACCEPTS the filed 18.0 t/h gas-phase pass.",
            ),
            ("domain", "polypropylene-gas-phase"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold the 18.0 t/h propylene feed while bed stays <= 88.0 C and feed stays <= "
                "22.0 t/h; do not extra-clamp a legal Unipol-style reactor.",
            ),
            ("t0_us", 1756850400000364),
            ("gate_latency_us", 400),
            ("race_window_us", 460),
            ("race_window_rel_ms", [8.0, 8.46]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.bed.C 84.2 C under 88.0",
                                "ir.cyclone.C 62 C smear under 70 look",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first ACCEPTS the already-legal 18.0 t/h feed. Cyclone-first "
                            "would extra-clamp because 62 C looks under a 70 C agglomeration look.",
                        ),
                        (
                            "window_derivation",
                            "460 us = one bed-TC slot versus cyclone-IR group delay on this "
                            "gas-phase skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 190 us vs combined jitter 66 us (TC 32 + IR 34): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 190 us inside the 460 us "
                            "window would have extra-clamped a legal 84.2 C / 18.0 t/h pass.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "dense-phase bed thermocouple tree, 1 kHz, 32 us jitter",
                    "cyclone-inlet IR pyrometer, 2 kHz, 34 us jitter",
                    "recycle compressor lift encoder (context)",
                    "bed DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 88.0),
                        ("observed_bed_C", 84.2),
                        ("cyclone_C", 62.0),
                        ("feed_cap_t_h", 22.0),
                        ("proposed_feed_t_h", 18.0),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "two-fluid Euler-Euler + quadrature-method-of-moments PSD, seed 69364; "
                            "8-zone Unipol-style bed; NOT lumped-CSTR, NOT U-RANS, NOT a wet-stand",
                        ),
                        (
                            "fidelity_limits",
                            "Rigid reactor shell; no distributor-plate motion. Raster is kernelized "
                            "events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Reactor R-8 in pass; 18.0 t/h propylene armed.",
                    "2. Bed 84.2 C under 88.0 agglomeration; feed 18.0 under 22.0 t/h inlet.",
                    "3. Lift encoder precursor at 1.105 ms.",
                    "4. Race window [8.000, 8.460] ms.",
                    "5. tc.bed.C 84.2 C at 8.120 ms (winner).",
                    "6. ir.cyclone.C 62 C at 8.310 ms (loser by 190 us).",
                    "7. Gate at 8.520 ms: ACCEPT 18.0 t/h; executed identical to proposed.",
                    "8. Bed stays 84.4 C < 88.0; feed 18.05 t/h < 22.0.",
                    "9. Cyclone remaining a shell glint did not require an extra clamp.",
                    "10. Delayed (survey_s=120): 120 s melt-flow coupon on the powder lock.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_pp_feed"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 84.2),
                        ("bed_cap_C", 88.0),
                        ("cyclone_C", 62.0),
                        ("feed_cap_t_h", 22.0),
                        ("race_margin_us", 190),
                        ("combined_jitter_us", 66),
                        ("survey_s", 120),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 18.0 t/h feed: bed 84.2 C is under the "
                "88.0 C agglomeration cap and 18.0 t/h is under 22.0 t/h inlet.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 84.2 C won by 190 us and is under the 88.0 C agglomeration cap. Cyclone "
                "62 C is a shell glint, not an agglomeration miss. ACCEPT the filed 18.0 t/h "
                "feed. Executed identical to proposed. An extra clamp is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 88.0),
                                    ("observed", 84.2),
                                    ("executed_feed_t_h", 18.0),
                                ]
                            ),
                        ),
                        (
                            "cyclone_C",
                            OrderedDict([("look", 70.0), ("observed", 62.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 190),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 2.88),
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
            ("name", "hold_pp_feed"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 18.0 t/h feed. Bed 84.2 C < 88.0 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 18.0 t/h propylene feed. Bed stayed 84.4 C under "
                "88.0 C. Cyclone remaining a shell glint was the losing channel and did not "
                "justify an extra clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held; 18.0 t/h"),
                        ("bed", "84.4 C < 88.0 C"),
                        ("cyclone", "62 C glint unused as agglomeration miss"),
                        ("powder", "pass continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Cyclone IR 62 C losing a 190 us race did not predict agglomeration; reversing 190 us would have extra-clamped a legal 84.2 C pass.",
                    "Delayed (survey_s=120): 120 s melt-flow coupon on the powder lock; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bed.C (8.120 ms, 84.2 C)"),
                        ("loser", "ir.cyclone.C (8.310 ms, 62 C)"),
                        ("margin_us", 190),
                        (
                            "counterfactual_if_reversed",
                            "Cyclone-first by < 190 us inside the 460 us window would have extra-clamped "
                            "a legal pass. Bed-first confirms the filed feed.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 8520),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (8.520 ms, tick 4). The 120 s melt-flow coupon "
                "is delayed surprise bound to survey_s=120, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        26,
        56,
        42,
        61,
        routing(
            "thalamic-relay.bed-tc",
            "spikenaut.policy.feed-accept",
            [
                ("relay_bed_C", "policy_feed_accept", 0.66),
                ("relay_cyclone_IR", "policy_extra_clamp", 0.23),
            ],
            "serotonin",
            0.12,
            "bed_confirm_stdp; 5-HT tags the feed_accept bind at the bed-TC win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 120),
                ("delayed_surprise_s", 120),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.46),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("feed_accept", 50, 0.50, 175.0, 4),
                    pop("extra_clamp", 40, 0.85, 40.0, 1),
                    pop("cyclone_veto", 22, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r69-364"),
            (
                "title",
                "Propene-Ayre PA-11 / Reactor R-8: bed 84.2 C beats cyclone IR 62 C by 190 us; "
                "ACCEPT already-legal 18.0 t/h gas-phase PP feed",
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
                    "Clean ACCEPT of an already-legal gas-phase PP feed. "
                    "total 1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08. Tick 6 binds survey_s=120.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "polypropylene-gas-phase",
                    [
                        "accept",
                        "simulated",
                        "bed-vs-cyclone",
                        "feed-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging cyclone IR losing a 190 us race does not require an "
                    "extra clamp when the fluidized bed is already under the agglomeration cap.",
                    4,
                ),
            ),
        ]
    )


def record_365():
    ticks = [
        tick(1980, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5120, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(5300, 0.08, 0.05, 0.03, 0.02, 0.01),
        tick(5480, 0.12, 0.09, 0.06, 0.04, 0.02),
        tick(6020, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(240000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.bus.ctx", 0.880, 0.44),
        spike("tc.cell.C", 1.980, 0.61),
        spike("ph.anolyte", 3.410, 0.52),
        spike("tc.cell.C", 5.120, 1.30),
        spike("ph.anolyte", 5.300, 1.12),
        spike("ctrl.gate", 5.480, 0.99),
        spike("tc.cell.C", 8.050, 0.77),
        spike("ph.anolyte", 11.400, 0.58),
        spike("ctrl.gate", 14.900, 0.83),
        spike("tc.cell.C", 18.200, 0.54),
        spike("enc.bus.ctx", 21.100, 0.39),
    ]
    excerpt = independent_excerpt(69365, 88, 22000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("current_kA", 12.5),
            ("cell_C", 88.0),
            ("anolyte_pH", 6.8),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Cell bank B-12 at Chlorate-Heugh CH-9 reads electrolyte 88.0 C against a 95.0 C "
                "thermal trip with a 12.5 kA load already filed under the 14.0 kA rectifier "
                "ceiling. pH-first would extra-clamp a legal bank; cell-TC-first ACCEPTS the "
                "filed 12.5 kA pass.",
            ),
            ("domain", "sodium-chlorate-cell"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold the 12.5 kA load while cell stays <= 95.0 C and current stays <= 14.0 kA; "
                "do not extra-clamp a legal chlorate bank.",
            ),
            ("t0_us", 1756850400000365),
            ("gate_latency_us", 360),
            ("race_window_us", 320),
            ("race_window_rel_ms", [5.05, 5.37]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.cell.C 88.0 C under 95.0",
                                "ph.anolyte 6.8 smear under 6.2 look",
                            ],
                        ),
                        (
                            "semantics",
                            "Cell-TC-first ACCEPTS the already-legal 12.5 kA load. pH-first would "
                            "extra-clamp because 6.8 looks over a 6.2 anolyte look.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one cell-TC slot versus anolyte-pH group delay on this "
                            "cell-room skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (TC 26 + pH 32): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have extra-clamped a legal 88.0 C / 12.5 kA pass.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "cell-electrolyte thermocouple, 4 kHz, 26 us jitter",
                    "anolyte pH probe, 1 kHz, 32 us jitter",
                    "rectifier bus encoder (context)",
                    "header DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cell_trip_C", 95.0),
                        ("observed_cell_C", 88.0),
                        ("anolyte_pH", 6.8),
                        ("current_cap_kA", 14.0),
                        ("proposed_current_kA", 12.5),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Cell bank B-12 in pass; 12.5 kA load armed.",
                    "2. Cell 88.0 C under 95.0 trip; current 12.5 under 14.0 kA rectifier.",
                    "3. Bus encoder precursor at 0.880 ms.",
                    "4. Race window [5.050, 5.370] ms.",
                    "5. tc.cell.C 88.0 C at 5.120 ms (winner).",
                    "6. ph.anolyte 6.8 at 5.300 ms (loser by 180 us).",
                    "7. Gate at 5.480 ms: ACCEPT 12.5 kA; executed identical to proposed.",
                    "8. Cell stays 88.2 C < 95.0; current 12.52 kA < 14.0.",
                    "9. pH remaining a junction glint did not require an extra clamp.",
                    "10. Delayed (survey_s=240): 4 min chlorate titer on the liquor header.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_chlorate_current"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("cell_C", 88.0),
                        ("cell_trip_C", 95.0),
                        ("anolyte_pH", 6.8),
                        ("current_cap_kA", 14.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 12.5 kA load: cell 88.0 C is under the "
                "95.0 C trip and 12.5 kA is under 14.0 kA rectifier.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Cell 88.0 C won by 180 us and is under the 95.0 C trip. Anolyte pH 6.8 is a "
                "junction glint, not a thermal miss. ACCEPT the filed 12.5 kA load. Executed "
                "identical to proposed. An extra clamp is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "cell_C",
                            OrderedDict(
                                [
                                    ("trip", 95.0),
                                    ("observed", 88.0),
                                    ("executed_current_kA", 12.5),
                                ]
                            ),
                        ),
                        (
                            "anolyte_pH",
                            OrderedDict([("look", 6.2), ("observed", 6.8)]),
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
            ("name", "hold_chlorate_current"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 12.5 kA load. Cell 88.0 C < 95.0 trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 12.5 kA load. Cell stayed 88.2 C under 95.0. "
                "pH remaining a junction glint was the losing channel and did not justify an "
                "extra clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("current", "held; 12.5 kA"),
                        ("cell", "88.2 C < 95.0"),
                        ("pH", "6.8 glint unused as thermal miss"),
                        ("liquor", "pass continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Anolyte pH 6.8 losing a 180 us race did not predict a thermal miss; reversing 180 us would have extra-clamped a legal 88.0 C bank.",
                    "Delayed (survey_s=240): 4 min chlorate titer on the liquor header; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.cell.C (5.120 ms, 88.0 C)"),
                        ("loser", "ph.anolyte (5.300 ms, 6.8)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "pH-first by < 180 us inside the 320 us window would have extra-clamped "
                            "a legal bank. Cell-TC-first confirms the filed load.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5480),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (5.480 ms, tick 4). The 4 min chlorate titer "
                "is delayed surprise bound to survey_s=240, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        22,
        88,
        26,
        50,
        routing(
            "thalamic-relay.cell-tc",
            "spikenaut.policy.current-accept",
            [
                ("relay_cell_C", "policy_current_accept", 0.69),
                ("relay_ph_anolyte", "policy_extra_clamp", 0.21),
            ],
            "octopamine",
            0.05,
            "cell_confirm_stdp; octopamine tags the current_accept bind at the cell-TC win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 240),
                ("delayed_surprise_s", 240),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("current_accept", 45, 0.50, 210.0, 3),
                    pop("extra_clamp", 40, 0.85, 40.0, 1),
                    pop("ph_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r69-365"),
            (
                "title",
                "Chlorate-Heugh CH-9 / Bank B-12: cell 88.0 C beats anolyte pH 6.8 by 180 us; "
                "ACCEPT already-legal 12.5 kA chlorate load",
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
                    "Clean ACCEPT of an already-legal sodium-chlorate load. "
                    "total 1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08. Tick 6 binds survey_s=240.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "sodium-chlorate-cell",
                    [
                        "accept",
                        "designed",
                        "cell-vs-ph",
                        "current-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging anolyte pH losing a 180 us race does not require a "
                    "wait when cell temperature is already under the thermal trip.",
                    5,
                ),
            ),
        ]
    )
