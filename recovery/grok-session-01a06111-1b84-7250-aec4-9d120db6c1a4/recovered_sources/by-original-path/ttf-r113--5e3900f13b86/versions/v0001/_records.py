def record_581():
    excerpt, extra = lif_581_excerpt()
    ticks = [
        tick(2080, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5200, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5380, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5900, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22400, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    spikes = [
        spike("pt.p4.bar", 1.040, 0.41),
        spike("p4s10.vapor.gNm3", 2.080, 0.58),
        spike("pt.p4.bar", 3.400, 0.50),
        spike("p4s10.vapor.gNm3", 5.200, 1.31),
        spike("pt.p4.bar", 5.380, 1.12),
        spike("ctrl.gate", 5.900, 0.97),
        spike("p4s10.vapor.gNm3", 8.100, 0.82),
        spike("pt.p4.bar", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.seal.dump", 22.400, 1.48),
        spike("ae.seal.dump", 24.100, 0.93),
        spike("pt.p4.bar", 30.200, 0.40),
        spike("p4s10.vapor.gNm3", 36.400, 0.55),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Pentasulf-Reen PR-3 kettle K-2 UV cell reads 9.4 g/Nm3 P4S10 over the 6.5 g/Nm3 stop. "
                "Yellow-phosphorus header PT sits at 3.2 bar, 2.0 shy of the 5.2 bar liquor-pump lock. "
                "Vapor-first clamps P4 liquor 14.0 t/h down to 8.4; header-first would keep 14.0 t/h "
                "cruising. Agitator-seal AE stays mute until a later seal dump.",
            ),
            ("domain", "phosphorus-pentasulfide-kettle"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep K-2 P4S10 vapor <= 6.5 g/Nm3 and finish the pentasulfide cook without "
                "dumping P4S10-wet liquor through a failed agitator seal.",
            ),
            ("t0_us", 1756850400000581),
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
                                "p4s10.vapor.gNm3 9.4 over 6.5 cap",
                                "pt.p4.bar 3.2 with header under 5.2",
                            ],
                        ),
                        (
                            "semantics",
                            "Vapor-first latches P4 liquor clamp 14.0 -> 8.4 t/h; header-first keeps 14.0 "
                            "on a 'still under liquor-pump-cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one UV-absorption vapor slot versus the P4-header PT publisher "
                            "on this phosphorus-pentasulfide kettle bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (vapor 28 + header 34): 2.90x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 14.0 t/h; predicted next-sample 7.8 g/Nm3 "
                            "> 6.5 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "off-gas UV P4S10 pentasulfide UV cell, 2 kHz, 28 us jitter",
                    "P4-liquor header PT, 1 kHz, 34 us jitter",
                    "agitator-seal AE puck (context)",
                    "P4 Coriolis (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("p4s10_cap_gNm3", 6.5),
                        ("observed_p4s10_gNm3", 9.4),
                        ("p4_liquor_tph", 14.0),
                        ("p4_bar", 3.2),
                        ("p4_cap_bar", 5.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. K-2 indexed on Pentasulf-Reen PR-3; P4 liquor 14.0 t/h; P4S10 vapor 9.4 g/Nm3.",
                    "2. Header 3.2 bar under 5.2 cap; pentasulfide cook armed.",
                    "3. Header PT precursor at 1.040 ms.",
                    "4. Race window [5.200, 5.560] ms.",
                    "5. p4s10.vapor.gNm3 9.4 at 5.200 ms (winner).",
                    "6. pt.p4.bar 3.2 at 5.380 ms (loser by 180 us).",
                    "7. Gate at 5.900 ms: MODIFY clamp P4 liquor 14.0 -> 8.4 t/h.",
                    "8. After clamp vapor 5.8 g/Nm3 <= 6.5; header still 3.2 bar.",
                    "9. At 22.400 ms an agitator-seal dump dumps 0.3 t P4S10-wet liquor.",
                    "10. 15 min seal isolate (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_p4_liquor"),
            (
                "parameters",
                OrderedDict(
                    [("p4_liquor_tph", 14.0), ("p4s10_gNm3", 9.4), ("p4_bar", 3.2)]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("p4s10_gNm3", 9.4),
                        ("p4s10_cap_gNm3", 6.5),
                        ("predicted_unclamped_next_gNm3", 7.8),
                        ("p4_liquor_tph", 14.0),
                        ("p4_bar", 3.2),
                        ("p4_cap_bar", 5.2),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 14.0 t/h P4 liquor because header 3.2 bar is under 5.2, treating "
                "the 9.4 g/Nm3 vapor as a fogged UV cell rather than a condenser-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "P4S10 vapor 9.4 g/Nm3 won by 180 us, so the kettle is off-spec, not still "
                "a P4-header story. Holding 14.0 t/h liquor predicts next-sample 7.8 g/Nm3 > 6.5 "
                "cap. MODIFY: P4 liquor 14.0 -> 8.4 t/h. Observed after clamp 5.8 g/Nm3 <= 6.5. "
                "A full REJECT is not indicated: a clean pentasulfide cook accepts 8.4 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "p4s10_gNm3",
                            OrderedDict(
                                [
                                    ("cap", 6.5),
                                    ("observed", 9.4),
                                    ("predicted_unclamped_next", 7.8),
                                    ("clamped_p4_liquor_tph", 8.4),
                                    ("observed_after_clamp", 5.8),
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
            ("name", "clamped_p4_liquor"),
            (
                "parameters",
                OrderedDict(
                    [("p4_liquor_tph", 8.4), ("p4s10_gNm3", 5.8), ("p4_bar", 3.2)]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: P4 liquor 14.0 -> 8.4 t/h. Process-correct vs the 6.5 g/Nm3 vapor cap. "
                "Seal still dumps at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held P4S10 vapor at 5.8 g/Nm3. At 22.400 ms an agitator "
                "seal already seated dumped 0.3 t of P4S10-wet liquor. Clamp reduced dump energy; "
                "it did not prevent the seal failure. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("offgas", "clamp executed; peak 5.8 g/Nm3 <= 6.5 cap"),
                        ("seal", "dumped at 22.400 ms; 0.3 t P4S10-wet liquor"),
                        ("repair", "15 min seal isolate (abort_s=900)"),
                        ("mission", "PR-3 pentasulfide cook incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither P4S10 vapor nor P4 header PT predicted the seated agitator-seal dump; ae.seal.dump is a new channel at 22.400 ms, 16.500 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min seal isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min seal isolate after the agitator-seal dump. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the liquor clamp completed under the 6.5 g/Nm3 "
                "cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "p4s10.vapor.gNm3 (5.200 ms, 9.4 g/Nm3)"),
                        ("loser", "pt.p4.bar (5.380 ms, 3.2 bar)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Header-first by < 180 us inside the 360 us window would have kept "
                            "14.0 t/h; predicted next-sample 7.8 g/Nm3 would have missed "
                            "the 6.5 cap even without the dump. The MODIFY is still the correct "
                            "process. The seal dump is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms agitator-seal dump (tick t_us=22400), inside the "
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
            "thalamic-relay.p4s10-vapor",
            "spikenaut.policy.p4-clamp",
            [
                ("relay.p4s10.vapor", "policy.p4_clamp", 0.68),
                ("relay.pt.p4", "policy.header_hold", 0.29),
                ("relay.ae.seal", "policy.p4_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at vapor win (5.200 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.400 ms agitator-seal dump",
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
                    pop_budget("p4_clamp", 50, 0.5, 220.0, 0.36),
                    pop_budget("header_hold", 40, 0.8, 50.0, 0.36),
                    pop("seal_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r113-581",
        "Pentasulf-Reen PR-3 / Kettle K-2: P4S10 vapor beats P4 header by 180 us; correct "
        "MODIFY still eats an in-window agitator-seal dump (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the 42 ms "
        "raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named seal isolate "
        "(abort_s=900) is not netted into task_progress.",
        ras,
        gate,
        "phosphorus-pentasulfide-kettle",
        [
            "modify",
            "partnered-negative-total",
            "independent-lif-raster",
            "sidecar-sim-only",
            "in-window-world-charge",
            "designed",
        ],
        "A critic can see the world-charge as a LIF burst inside the raster while process "
        "heads stay honest. Credit assignment is spikes, not prose across a 15 min seal isolate.",
        1,
    )


def record_582():
    ticks = [
        tick(2240, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5600, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5780, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6120, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6460, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("ft.ether.tph", 1.120, 0.42),
        spike("enc.po.pct", 2.240, 0.57),
        spike("ft.ether.tph", 3.500, 0.49),
        spike("enc.po.pct", 5.600, 1.29),
        spike("tag.pc.pct", 5.780, 1.10),
        spike("ctrl.gate", 6.120, 0.96),
        spike("enc.po.pct", 8.400, 0.80),
        spike("ft.ether.tph", 10.400, 0.63),
        spike("ctrl.gate", 12.600, 0.84),
        spike("enc.po.pct", 16.600, 0.41),
        spike("tag.pc.pct", 22.200, 0.54),
        spike("enc.po.pct", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(113582, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Borether-Ghyll BG-6 etherate kettle R-4 is already over the published kettle-TC cap: "
                "live well 94.0 C versus 82.0. The live BF3-etherate stem is 78.0 percent-open. A leftover "
                "DCS tag still publishes percent-closed 22.0 (100 minus 78). Live-PO-first must cut 78.0 "
                "to 34.0; the weak supervisor binds percent-closed as if it were percent-open and opens "
                "78.0 to 92.0.",
            ),
            ("domain", "boron-trifluoride-etherate-kettle"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the BG-6 etherate pass with kettle TC <= 82.0 C, leave diethyl ether at 4.2 t/h, "
                "and keep the leftover percent-closed tag out of the live stem slot.",
            ),
            ("t0_us", 1756850400000582),
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
                                "enc.po.pct 78.0 percent-open on LIVE R-4 stem",
                                "tag.pc.pct 22.0 leftover percent-closed",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-percent-open-first should MODIFY-cut the BF3-etherate stem on R-4; "
                            "percent-closed-as-PV is a scale invert that opens the valve because 22.0 looks starved.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live percent-open encoder slot versus the leftover percent-closed "
                            "publisher on this BF3-etherate PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (live 28 + closed-tag 32). Order is "
                            "correctly live-PO-first. The error is percent-closed bind: the leftover tag "
                            "is not the PV, so chasing 22.0 opens R-4 instead of cutting under 82.0 C.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live stem percent-open encoder on R-4, 2 kHz, 28 us jitter, tag=R4_BF3.PO status=LIVE",
                    "leftover percent-closed tag, 1 kHz, 32 us jitter, tag=R4_BF3.PC status=LEFTOVER",
                    "kettle TC well (context)",
                    "diethyl-ether Coriolis (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_tc_C", 82.0),
                        ("live_tc_C", 94.0),
                        ("live_po_pct", 78.0),
                        ("shadow_pc_pct", 22.0),
                        ("live_status", "LIVE"),
                        ("pc_tag_status", "LEFTOVER"),
                        ("pc_is_pv", False),
                        ("bind_percent_closed", False),
                        ("ether_tph", 4.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. R-4 LIVE etherating; kettle 94.0 C; stem 78.0 percent-open; ether 4.2 t/h.",
                    "2. Leftover DCS tag still paints percent-closed 22.0 from last campaign.",
                    "3. Ether precursor at 1.120 ms.",
                    "4. Race window [5.600, 5.940] ms.",
                    "5. enc.po.pct 78.0 at 5.600 ms (winner).",
                    "6. tag.pc.pct 22.0 at 5.780 ms (loser by 180 us).",
                    "7. Gate at 6.120 ms: WRONG-MODIFY binds leftover percent-closed as live stem.",
                    "8. Stem 78.0 -> 92.0 percent-open; live TC stays 94.0 over 82.0.",
                    "9. Live 94.0 stays > 82.0; R-4 dumps etherate liquor.",
                    "10. Delayed (abort_s=720): 12 min etherate dump while R-4 stays over cap.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_etherate_live"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("valve_po_pct", 78.0),
                        ("ether_tph", 4.2),
                        ("bind_percent_closed", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_tc_C", 94.0),
                        ("cap_tc_C", 82.0),
                        ("live_po_pct", 78.0),
                        ("shadow_pc_pct", 22.0),
                        ("pc_is_pv", False),
                        ("live_status", "LIVE"),
                        ("pc_tag_status", "LEFTOVER"),
                        ("ether_tph", 4.2),
                        ("correct_valve_po_pct", 34.0),
                        ("correct_ether_tph", 4.2),
                        ("correct_gate", "MODIFY"),
                        ("t_gate_us", 6120),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 720),
                        ("leftover_tag", "R4_BF3.PC"),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping 78.0 percent-open on R-4 because leftover percent-closed "
                "22.0 looks like a starved stem, treating the 82.0 C cap as a stale well.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Kettle 94.0 C exceeds the 82.0 cap, so a stem cut is required, but the highlighted "
                "stem is leftover R4_BF3.PC at 22.0 percent-closed. Apply a 92.0 percent-open 'chase' "
                "on the inverted scale (which opens). Leave LIVE R-4 unused, then overshoot to 92.0.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "etherate",
                            OrderedDict(
                                [
                                    ("cap_tc_C", 82.0),
                                    ("live_tc_C", 94.0),
                                    ("live_po_pct", 78.0),
                                    ("shadow_pc_pct", 22.0),
                                    ("executed_valve_po_pct", 92.0),
                                    ("correct_valve_po_pct", 34.0),
                                    ("correct_gate", "MODIFY"),
                                ]
                            ),
                        ),
                        (
                            "percent_closed",
                            OrderedDict(
                                [
                                    ("t_gate_us", 6120),
                                    ("bind_percent_closed", True),
                                    ("pc_is_pv", False),
                                    ("pc_tag_status", "LEFTOVER"),
                                    ("wrong_pair", True),
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
            ("name", "percent_closed_as_open"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("valve_po_pct", 92.0),
                        ("ether_tph", 4.2),
                        ("bind_percent_closed", True),
                        ("live_tc_C", 94.0),
                        ("pc_is_pv", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / percent-open vs percent-closed): 92.0 percent-open BF3-etherate "
                "OPEN applied because leftover percent-closed 22.0 was treated as the live stem. "
                "Routing relay.pc.shadow -> policy.pc_open; no positive weight to policy.po_cut.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY opened the BF3-etherate stem on a kettle that needed a live cut. Live "
                "94.0 C was over the 82.0 cap at t_gate; leftover percent-closed 22.0 is not the PV "
                "so the 92.0 percent-open 'chase' opened the valve. 12 min etherate dump (abort_s=720). "
                "Correct gate was MODIFY; cut R-4 stem 78.0 -> 34.0 percent-open at t_gate_us=6120 and "
                "leave the leftover percent-closed tag unbound.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live_pv", "R-4 left illegal at 94.0 C; stem opened 78.0 -> 92.0 percent-open"),
                        ("leftover_pc", "R4_BF3.PC treated as live stem while still LEFTOVER percent-closed"),
                        ("dump", "12 min etherate-liquor dump, R-4 over cap"),
                        ("mission", "BF3-etherate cook deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-percent-open-first was the correct order and live kettle TC was over cap; the MODIFY spent that win as a leftover percent-closed chase.",
                    "Delayed (abort_s=720): BG-6 holds 12 min while R-4 is dumped and recharged; next batch 14 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY; cut live R-4 stem 78.0 -> 34.0 percent-open at t_gate_us=6120; bind_percent_closed=false; pc_is_pv=false; leave diethyl ether at 4.2 t/h; leave R4_BF3.PC unbound.",
                        ),
                        ("correct_actuator", "R-4_bf3_stem_direct"),
                        ("wrong_pair", "R4_BF3.PC_as_percent_open"),
                        ("t_gate_us", 6120),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("valve_po_pct", 92.0),
                                    ("bind_percent_closed", True),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min etherate dump (task/efficiency); live kettle TC never returned under 82.0 C while the cut was spent as a leftover percent-closed chase on R4_BF3.PC.",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "enc.po.pct (5.600 ms, 78.0 percent-open)"),
                        ("loser", "tag.pc.pct (5.780 ms, 22.0 leftover percent-closed)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Percent-closed-first by < 180 us would still be 22.0 on a leftover inverted "
                            "scale; a correct gate binds enc.po.pct to policy.po_cut at t_gate either "
                            "way. The wrong MODIFY spent the live win on a percent-closed chase.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6120),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the leftover percent-closed bind (6.120 ms, tick 4). "
                "The 12 min etherate dump is delayed surprise, not the inflection.",
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
            "thalamic-relay.bf3-percent-closed",
            "spikenaut.policy.pc-open",
            [
                ("relay.pc.shadow", "policy.pc_open", 0.74),
                ("relay.enc.po", "policy.pc_open", 0.21),
            ],
            "acetylcholine",
            0.08,
            "percent_closed_stdp; ACh tags the (wrong) leftover percent-closed chase at the live PO win",
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
                    pop_budget("pc_open", 48, 0.45, 300.0, 0.34),
                    pop("po_cut", 48, 0.90),
                    pop("pair_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r113-582",
        "WRONG-MODIFY at Borether-Ghyll BG-6 / Kettle R-4: live 94.0 C over 82.0 cap; "
        "92.0 percent-open BF3 OPEN on leftover percent-closed 22.0 (percent-open vs percent-closed)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-modify / percent-open vs percent-closed. Sidecar arithmetic 94.0 > 82.0 on live "
        "kettle TC is true; MODIFY bound to pc_open. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
        ras,
        gate,
        "boron-trifluoride-etherate-kettle",
        [
            "modify",
            "wrong-gate",
            "percent-open",
            "percent-closed",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live-percent-open-first race can still be a wrong gate when the "
        "MODIFY treats leftover percent-closed as the live stem and opens BF3-etherate. Convictable "
        "from live_tc_C vs cap, pc_is_pv, bind_percent_closed, and routing without etherate physics.",
        2,
        supervisor_error_type="wrong-modify",
    )


def record_583():
    ticks = [
        tick(2736, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6840, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7020, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7640, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(7960, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("p.bub.kW", 1.360, 0.40),
        spike("ae.b2.pps", 2.736, 0.56),
        spike("p.bub.kW", 4.100, 0.48),
        spike("ae.b2.pps", 6.840, 1.34),
        spike("p.bub.kW", 7.020, 1.11),
        spike("ctrl.gate", 7.640, 0.98),
        spike("ae.b2.pps", 10.400, 0.81),
        spike("p.bub.kW", 14.800, 0.62),
        spike("ctrl.gate", 18.200, 0.84),
        spike("ae.b2.pps", 28.400, 0.52),
        spike("p.bub.kW", 36.100, 0.39),
        spike("ae.b2.pps", 42.200, 0.44),
    ]
    excerpt = independent_excerpt(113583, 120, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Gallichl-Tarn GT-HIL quartz AE puck on bubbler B-2 is 58 pps, fourfold the 14 pps "
                "quiet band. Bubbler RF remains 1.9 kW, 2.3 shy of the 4.2 kW trip. Legal action "
                "parks the 2.6 kW tap at zero; a power-first dispatch would energize a noisy "
                "ampoule. RF kW meters do not outrank the puck.",
            ),
            ("domain", "gallium-trichloride-bubbler"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep B-2 from dispatching a growling quartz ampoule while bubbler RF remains under "
                "its own cap.",
            ),
            ("t0_us", 1756850400000583),
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
                                "ae.b2.pps 58 over 14 cap",
                                "p.bub.kW 1.9 under 4.2 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; power-first dispatches 2.6 kW on a 'kW still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one AE puck slot versus the bubbler-RF publisher on this HIL gallium-trichloride bubbler bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + RF 32): 3.10x over a "
                            "2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have dispatched 2.6 kW into a growling ampoule.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "quartz AE puck, 50 kHz, 26 us jitter",
                    "bubbler RF CT, 1 kHz, 32 us jitter",
                    "GaCl3-carrier MFC (context)",
                    "ampoule wall TC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 14.0),
                        ("observed_ae_pps", 58.0),
                        ("bubbler_kW", 1.9),
                        ("bubbler_cap_kW", 4.2),
                        ("proposed_kW", 2.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. B-2 HIL indexed; 2.6 kW tap armed.",
                    "2. RF 1.9 kW under 4.2; AE 58 pps over 14.",
                    "3. RF precursor at 1.360 ms.",
                    "4. Race window [6.840, 7.160] ms.",
                    "5. ae.b2.pps 58 at 6.840 ms (winner).",
                    "6. p.bub.kW 1.9 at 7.020 ms (loser by 180 us).",
                    "7. Gate at 7.640 ms: REJECT hold, do not dispatch.",
                    "8. Power 0 kW; RF left at 1.9 kW.",
                    "9. Ampoule inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min bubbler reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_bubbler"),
            (
                "parameters",
                OrderedDict([("kW", 2.6), ("hold", False), ("bubbler_kW", 1.9)]),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 58.0),
                        ("ae_cap_pps", 14.0),
                        ("bubbler_kW", 1.9),
                        ("bubbler_cap_kW", 4.2),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.6 kW because bubbler RF 1.9 kW is under 4.2, treating the 58 pps AE "
                "as rectifier hash rather than a growling ampoule.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Quartz AE 58 pps won by 180 us, so the GaCl3 bubbler is growling, not still "
                "a current story. 1.9 kW is under 4.2 and does not authorize dispatch. REJECT: "
                "hold power 2.6 -> 0 kW. A MODIFY that only trims kW would leave the growl.",
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
                                    ("observed", 58.0),
                                    ("executed_kW", 0.0),
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
            ("name", "hold_bubbler"),
            (
                "parameters",
                OrderedDict([("kW", 0.0), ("hold", True), ("bubbler_kW", 1.9)]),
            ),
            (
                "gate_effect",
                "REJECT: power 2.6 -> 0 kW. Bubbler left at 1.9 kW under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held B-2. AE 58 pps beat RF 1.9 kW by 180 us. Power was legal; "
                "the ampoule was not. 8 min bubbler reset (abort_s=480) is delayed survey, not a "
                "process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("power", "held at 0 kW"),
                        ("current", "left 1.9 kW < 4.2 cap"),
                        ("ampoule", "8 min bubbler reset (abort_s=480)"),
                        ("mission", "HIL bubbler not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Bubbler RF never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min bubbler reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.b2.pps (6.840 ms, 58 pps)"),
                        ("loser", "p.bub.kW (7.020 ms, 1.9 kW)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Power-first by < 180 us inside the 320 us window would have "
                            "dispatched 2.6 kW into a growling ampoule. The REJECT is still "
                            "the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7640),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.640 ms, tick 4). The 8 min cell "
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
            "thalamic-relay.b2-ae",
            "spikenaut.policy.b2-hold",
            [
                ("relay.ae.b2", "policy.b2_hold", 0.70),
                ("relay.p.bub", "policy.kw_go", 0.24),
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
                    pop_budget("b2_hold", 56, 0.45, 280.0, 0.32),
                    pop("kw_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r113-583",
        "Gallichl-Tarn GT-HIL / Bubbler B-2: quartz AE 58 pps beats RF 1.9 kW by 180 us; "
        "correct REJECT holds the tap",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 58 > 14 cap beats legal bubbler RF. total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "gallium-trichloride-bubbler",
        ["reject", "hil", "ae-vs-kw", "growling-ampoule", "tick6-sidecar-bound"],
        "Teaches that a legal bubbler-RF header can lose to quartz AE inside a 320 us "
        "window; reversing 180 us would have dispatched a growling GaCl3 ampoule.",
        3,
    )


def record_584():
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
        spike("tc.bath.C", 2.880, 0.55),
        spike("tc.jacket.C", 4.400, 0.48),
        spike("tc.bath.C", 7.200, 1.26),
        spike("tc.jacket.C", 7.380, 1.08),
        spike("ctrl.gate", 7.840, 0.95),
        spike("tc.bath.C", 11.200, 0.78),
        spike("tc.jacket.C", 14.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("tc.bath.C", 22.600, 0.50),
        spike("tc.jacket.C", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(113584, 48, 28000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("dez_kgh", 1.4),
            ("bath_C", 18.6),
            ("jacket_C", 41.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Zincethyl-Beck ZB-4 simulated bubbler U-7 bath TC already sits at 18.6 C versus a "
                "32.0 C DEZ trip. Jacket skin is 41 C, 29 K shy of 70 C. The 1.4 kg/h diethylzinc "
                "recipe sits inside both caps; a jacket-first hold would idle a quiet MOCVD train.",
            ),
            ("domain", "diethylzinc-bubbler"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the ZB-4 bubbler pass with bath <= 32.0 C and jacket <= 70 C.",
            ),
            ("t0_us", 1756850400000584),
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
                                "tc.bath.C 18.6 under 32.0 trip",
                                "tc.jacket.C 41 under 70 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Bath-first confirms the already-legal 1.4 kg/h DEZ feed; jacket-first "
                            "would have treated the bath TC as a flood echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one bath-TC slot versus the jacket-TC publisher on this simulated diethylzinc-bubbler bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (bath 26 + jacket 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed DEZ feed illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bath TC well on DEZ bubbler, 26 us jitter",
                    "jacket TC well, 32 us jitter",
                    "DEZ mass-flow (context)",
                    "carrier N2 MFC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bath_cap_C", 32.0),
                        ("observed_bath_C", 18.6),
                        ("jacket_cap_C", 70.0),
                        ("observed_jacket_C", 41.0),
                        ("carrier_slm", 2.2),
                        ("carrier_cap_slm", 4.0),
                        ("proposed_dez_kgh", 1.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. U-7 indexed on Zincethyl-Beck ZB-4; 1.4 kg/h DEZ armed.",
                    "2. Caps: bath 32.0 C, jacket 70 C, carrier 4.0 slm.",
                    "3. Jacket TC precursor at 1.200 ms.",
                    "4. Race window [7.200, 7.560] ms.",
                    "5. tc.bath.C 18.6 at 7.200 ms (winner).",
                    "6. tc.jacket.C 41 at 7.380 ms (loser by 180 us).",
                    "7. Gate at 7.840 ms: ACCEPT 1.4 kg/h already legal.",
                    "8. DEZ continues; no extra hold.",
                    "9. 6 min survey confirms bath still under 32.0 C.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "feed_dez_14"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bath_C", 18.6),
                        ("bath_cap_C", 32.0),
                        ("jacket_C", 41.0),
                        ("jacket_cap_C", 70.0),
                        ("carrier_slm", 2.2),
                        ("carrier_cap_slm", 4.0),
                        ("dez_kgh", 1.4),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 1.4 kg/h DEZ feed because bath 18.6 C is under 32.0 and jacket "
                "41 C is under 70 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bath 18.6 C won by 180 us and is under 32.0. Jacket 41 C is under 70 C. "
                "Carrier 2.2 slm is under 4.0. ACCEPT the already-legal DEZ feed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bath_C",
                            OrderedDict(
                                [
                                    ("cap", 32.0),
                                    ("observed", 18.6),
                                    ("executed_dez_kgh", 1.4),
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
            ("name", "feed_dez_14"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 1.4 kg/h DEZ and 18.6 C bath unchanged. Routing relay.tc.bath -> policy.dez_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left U-7 on a 1.4 kg/h / 18.6 C DEZ feed. Jacket TC hitch did "
                "not justify a hold. 6 min survey confirmed bath still under 32.0 C.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "still 1.4 kg/h DEZ"),
                        ("bath", "18.6 C under 32.0 trip"),
                        ("jacket", "41 C under 70"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Jacket TC 41 C hitch is residual, not a runaway trip.",
                    "Delayed (survey_s=360): 6 min survey restacks U-7 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bath.C (7.200 ms, 18.6 C)"),
                        ("loser", "tc.jacket.C (7.380 ms, 41 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Jacket-first by < 180 us would only delay confirmation. The DEZ feed "
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
            "thalamic-relay.dez-bath",
            "spikenaut.policy.dez-go",
            [
                ("relay.tc.bath", "policy.dez_go", 0.68),
                ("relay.tc.jacket", "policy.jacket_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_dez_stdp; 5-HT tags the dez_go bind at the bath-TC win",
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
                    pop_budget("dez_go", 40, 0.45, 250.0, 0.36),
                    pop("jacket_hold", 32, 0.90),
                    pop("bath_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r113-584",
        "Zincethyl-Beck ZB-4 / Bubbler U-7: bath 18.6 C beats jacket 41 C by 180 us; ACCEPT "
        "already-legal 1.4 kg/h DEZ",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal DEZ bubbler feed. total +1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "diethylzinc-bubbler",
        [
            "accept",
            "already-legal",
            "simulated-dez-bubbler",
            "bath-vs-jacket",
            "sidecar-convictable",
            "simulated",
        ],
        "Teaches that a bath TC under trip can confirm an already-legal DEZ feed "
        "without a jacket-TC hitch becoming a hold.",
        4,
    )


def record_585():
    ticks = [
        tick(2016, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5040, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5920, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(240000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("o2.offgas.vol", 0.980, 0.41),
        spike("tc.bed.C", 2.016, 0.60),
        spike("o2.offgas.vol", 3.200, 0.51),
        spike("tc.bed.C", 5.040, 1.30),
        spike("o2.offgas.vol", 5.200, 1.12),
        spike("ctrl.gate", 5.640, 0.97),
        spike("tc.bed.C", 8.100, 0.78),
        spike("o2.offgas.vol", 12.400, 0.62),
        spike("ctrl.gate", 16.200, 0.85),
        spike("tc.bed.C", 20.400, 0.54),
        spike("o2.offgas.vol", 22.800, 0.43),
    ]
    excerpt = independent_excerpt(113585, 80, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("ho2o3_tph", 2.6),
            ("bed_C", 842.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Holmox-Wath HW-5 calciner C-8 bed well is 842 C, 138 K shy of the "
                "980 C stack limit, and off-gas oxygen is 8.4 vol percent versus a 14.0 vol percent trip. "
                "Keeping 2.6 t/h is lawful; an oxygen-first veto would idle a quiet holmia stack.",
            ),
            ("domain", "holmium-oxide-calciner"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run C-8 at 2.6 t/h, keep bed <= 980 C and off-gas O2 <= 14.0 vol percent, and leave "
                "the holmia calcine on schedule.",
            ),
            ("t0_us", 1756850400000585),
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
                                "tc.bed.C 842 under 980 cap",
                                "o2.offgas.vol 8.4 under 14.0 trip",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first confirms the already-legal 2.6 t/h run; oxygen-first would "
                            "have treated the bed TC as a hitch echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one bed-TC slot versus the zirconia-O2 publisher on this holmia calciner bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (TC 22 + O2 30): 3.08x over a "
                            "2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal 2.6 t/h run.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed TC well, 2 kHz, 22 us jitter",
                    "off-gas zirconia O2, 1 kHz, 30 us jitter",
                    "hood IR (context)",
                    "oxalate-feed Coriolis (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 980.0),
                        ("observed_bed_C", 842.0),
                        ("ho2o3_tph", 2.6),
                        ("o2_vol", 8.4),
                        ("o2_cap_vol", 14.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Calciner C-8 indexed on Holmox-Wath HW-5; 2.6 t/h armed.",
                    "2. Bed 842 C under 980; off-gas O2 8.4 vol percent under 14.0.",
                    "3. Zirconia precursor at 0.980 ms.",
                    "4. Race window [5.040, 5.320] ms.",
                    "5. tc.bed.C 842 at 5.040 ms (winner).",
                    "6. o2.offgas.vol 8.4 at 5.200 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 2.6 t/h.",
                    "8. Bed stays 842 C; O2 stays 8.4 vol percent.",
                    "9. Holmia calciner on-spec.",
                    "10. Delayed (dwell_s=240): 4 min hood reseq.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_ho2o3_tph"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 842.0),
                        ("bed_cap_C", 980.0),
                        ("ho2o3_tph", 2.6),
                        ("o2_vol", 8.4),
                        ("o2_cap_vol", 14.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.6 t/h because bed 842 C is under 980 and off-gas O2 "
                "8.4 vol percent is under 14.0.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed TC 842 C won by 160 us, so the calciner is already legal, not still climbing. "
                "Off-gas O2 8.4 vol percent is under 14.0. ACCEPT the 2.6 t/h run. A REJECT would idle a legal holmia stack.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 980.0),
                                    ("observed", 842.0),
                                    ("executed_ho2o3_tph", 2.6),
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
            ("name", "hold_ho2o3_tph"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: leave 2.6 t/h; bed 842 C; oxygen legal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 2.6 t/h holmia run. Bed 842 C beat oxygen "
                "8.4 vol percent by 160 us. 4 min hood reseq (dwell_s=240) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("growth", "2.6 t/h held"),
                        ("bed", "842 C < 980 cap"),
                        ("chamber", "C-8 on-spec"),
                        ("reseq", "4 min hood reseq (dwell_s=240)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "off-gas O2 never approached 14.0 vol percent; bed was already under cap.",
                    "Delayed (dwell_s=240): 4 min hood reseq after monolayer.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bed.C (5.040 ms, 842 C)"),
                        ("loser", "o2.offgas.vol (5.200 ms, 8.4 vol percent)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Oxygen-first by < 160 us inside the 280 us window would have "
                            "REJECTED an already-legal 2.6 t/h run. The ACCEPT is still the "
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
            "thalamic-relay.holmia-bed",
            "spikenaut.policy.holmia-go",
            [
                ("relay.tc.bed", "policy.holmia_go", 0.67),
                ("relay.o2.offgas", "policy.holmia_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the bed-TC win as an already-legal holmia run",
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
                    pop_budget("holmia_go", 40, 0.45, 250.0, 0.28),
                    pop("holmia_hold", 32, 0.90),
                    pop("bed_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r113-585",
        "Holmox-Wath HW-5 / Calciner C-8: bed 842 C beats off-gas O2 8.4 vol percent by 160 us; "
        "correct ACCEPT of an already-legal 2.6 t/h run",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Bed 842 < 980; O2 8.4 < 14.0. total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
        ras,
        gate,
        "holmium-oxide-calciner",
        ["accept", "designed", "bed-vs-oxygen", "already-legal-holmia", "tick6-sidecar-bound"],
        "Teaches that a legal oxygen header can lose to bed TC inside a 280 us window; "
        "reversing 160 us would have REJECTED an already-legal holmia run.",
        5,
    )
