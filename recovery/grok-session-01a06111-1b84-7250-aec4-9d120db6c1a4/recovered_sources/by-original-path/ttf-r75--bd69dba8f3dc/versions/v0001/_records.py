def record_391():
    excerpt, extra = lif_391_excerpt()
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
                "Acheson furnace F-7 on Carbor-Venn CV-3 is already pulling 18.4 kA against a "
                "14.0 kA resistor cap while coke-bed skin still reads a legal 2140 C under 2280. "
                "Current-first clamps the arc 18.4 -> 11.2 kA; temperature-first would keep cruise "
                "because the bed looks cool. A hood-brick spall already seated on the off-gas "
                "plenum does not appear on current or skin until the AE dump.",
            ),
            ("domain", "silicon-carbide-acheson"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep F-7 arc current <= 14.0 kA and finish the SiC soak without dumping grit "
                "through a torn hood brick.",
            ),
            ("t0_us", 1756850400000391),
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
                                "i.arc.ka 18.4 over 14.0 cap",
                                "tc.bed.C 2140 with skin under 2280",
                            ],
                        ),
                        (
                            "semantics",
                            "Current-first latches arc clamp 18.4 -> 11.2 kA; temperature-first "
                            "keeps 18.4 kA on a 'still under bed-skin cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one Hall-probe slot versus the bed-TC publisher on this "
                            "Acheson resistor bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (Hall 28 + TC 34): 2.90x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 18.4 kA; predicted next-sample 16.8 kA "
                            "> 14.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "arc Hall probe, 2 kHz, 28 us jitter",
                    "coke-bed skin TC, 1 kHz, 34 us jitter",
                    "hood AE puck (context)",
                    "transformer tap encoder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("arc_cap_kA", 14.0),
                        ("observed_arc_kA", 18.4),
                        ("bed_C", 2140.0),
                        ("bed_cap_C", 2280.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. F-7 indexed on Carbor-Venn CV-3; arc 18.4 kA; bed 2140 C.",
                    "2. Skin under 2280 C cap; soak armed.",
                    "3. Hall precursor at 1.180 ms.",
                    "4. Race window [5.280, 5.640] ms.",
                    "5. i.arc.ka 18.4 at 5.280 ms (winner).",
                    "6. tc.bed.C 2140 at 5.460 ms (loser by 180 us).",
                    "7. Gate at 5.980 ms: MODIFY clamp 18.4 -> 11.2 kA.",
                    "8. After clamp arc 11.2 kA <= 14.0; CO 380 ppm <= 600.",
                    "9. At 22.600 ms a hood-brick spall dumps 0.3 t grit.",
                    "10. 15 min hood isolate (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_arc_kA"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("arc_kA", 18.4),
                        ("bed_C", 2140.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("arc_kA", 18.4),
                        ("arc_cap_kA", 14.0),
                        ("predicted_unclamped_next_kA", 16.8),
                        ("bed_C", 2140.0),
                        ("bed_cap_C", 2280.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.4 kA because bed 2140 C is under 2280, treating the Hall "
                "over-cap as transformer inrush rather than a resistor-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Arc Hall 18.4 kA won by 180 us, so the soak is over the 14.0 kA resistor cap, "
                "not still a bed-skin story. Holding 18.4 kA predicts next-sample 16.8 kA > 14.0. "
                "MODIFY: arc 18.4 -> 11.2 kA. Observed after clamp 11.2 kA <= 14.0. A full REJECT "
                "is not indicated: a clean soak accepts 11.2 kA.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "arc_kA",
                            OrderedDict(
                                [
                                    ("cap", 14.0),
                                    ("observed", 18.4),
                                    ("predicted_unclamped_next", 16.8),
                                    ("clamped_arc_kA", 11.2),
                                    ("observed_after_clamp", 11.2),
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
            ("name", "clamped_arc_kA"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("arc_kA", 11.2),
                        ("bed_C", 2140.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: arc 18.4 -> 11.2 kA. Process-correct vs the 14.0 kA resistor cap. "
                "Hood brick still spalls at 22.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held arc at 11.2 kA. At 22.600 ms a hood-brick spall "
                "already seated on the off-gas plenum dumped 0.3 t of SiC grit. Clamp reduced "
                "dump energy; it did not prevent the spall. Partnered negative: process heads "
                "stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("arc", "clamp executed; peak 11.2 kA <= 14.0 cap"),
                        ("hood_brick", "spalled at 22.600 ms; 0.3 t grit"),
                        ("repair", "15 min hood isolate (abort_s=900)"),
                        ("mission", "CV-3 soak incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither Hall current nor bed TC predicted the seated hood-brick spall; ae.hood.brick is a new channel at 22.600 ms, 16.620 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min hood isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min hood isolate after the brick spall. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the arc clamp completed under the 14.0 kA "
                "cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "i.arc.ka (5.280 ms, 18.4 kA)"),
                        ("loser", "tc.bed.C (5.460 ms, 2140 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Temperature-first by < 180 us inside the 360 us window would have "
                            "kept 18.4 kA; predicted next-sample 16.8 kA would have missed the "
                            "14.0 cap even without the spall. The MODIFY is still the correct "
                            "process. The spall is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22600),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.600 ms hood-brick spall (tick t_us=22600), inside the "
                "42 ms raster. The correct MODIFY at 5.980 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=900 isolation tick.",
            ),
            ("delayed_surprise_s", 900),
        ]
    )
    spikes = [
        spike("tc.bed.C", 1.180, 0.41),
        spike("i.arc.ka", 2.112, 0.58),
        spike("tc.bed.C", 3.400, 0.50),
        spike("i.arc.ka", 5.280, 1.31),
        spike("tc.bed.C", 5.460, 1.12),
        spike("ctrl.gate", 5.980, 0.97),
        spike("i.arc.ka", 8.100, 0.82),
        spike("tc.bed.C", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.hood.brick", 22.600, 1.48),
        spike("ae.hood.brick", 24.100, 0.93),
        spike("tc.bed.C", 30.200, 0.40),
        spike("i.arc.ka", 36.400, 0.55),
    ]
    dw = 0.36
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.acheson-arc",
            "spikenaut.policy.arc-clamp",
            [
                ("relay.i.arc", "policy.arc_clamp", 0.68),
                ("relay.tc.bed", "policy.temp_hold", 0.29),
                ("relay.ae.hood", "policy.arc_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at Hall win (5.280 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.600 ms hood-brick spall",
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
                    pop_budget("arc_clamp", 50, 0.50, 220.0, dw),
                    pop_budget("temp_hold", 40, 0.80, 50.0, dw),
                    pop("spall_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r75-391"),
            (
                "title",
                "Carbor-Venn CV-3 / Furnace F-7: arc Hall 18.4 kA beats bed 2140 C by 180 us; "
                "correct MODIFY still eats an in-window hood-brick spall (partnered negative "
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
                    "hood isolate (abort_s=900) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "silicon-carbide-acheson",
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
                    "15 min hood isolate.",
                    1,
                ),
            ),
        ]
    )


def record_392():
    ticks = [
        tick(2160, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5400, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5580, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5920, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6260, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("ft.benzene.tph", 1.080, 0.42),
        spike("pt.live.bar", 2.160, 0.57),
        spike("ft.benzene.tph", 3.400, 0.49),
        spike("pt.live.bar", 5.400, 1.29),
        spike("pt.lag.kpa", 5.580, 1.10),
        spike("ctrl.gate", 5.920, 0.96),
        spike("pt.live.bar", 8.200, 0.80),
        spike("ft.benzene.tph", 10.200, 0.63),
        spike("ctrl.gate", 12.400, 0.84),
        spike("pt.live.bar", 16.400, 0.41),
        spike("pt.lag.kpa", 22.100, 0.54),
        spike("pt.live.bar", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(75392, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Alkylation reactor R-4 at Ethylbenz-Shiel ES-9 reads live shell 4.8 bar under a "
                "6.0 bar cap; a lagged bus faceplate still prints 48 with engineering_unit=kPa. "
                "Live-first should ACCEPT 18 t/h benzene; a weak supervisor treats 48 as bar and "
                "dumps the feed.",
            ),
            ("domain", "ethylbenzene-alkylation"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the ES-9 alkylation with live shell <= 6.0 bar, leave benzene at the "
                "planned 18 t/h, and bind the live bar tag rather than a lagged kPa faceplate.",
            ),
            ("t0_us", 1756850400000392),
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
                                "pt.live.bar 4.8 bar on R-4 LIVE",
                                "pt.lag.kpa 48 kPa on lagged bus faceplate",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-first should latch ACCEPT of 18 t/h benzene (4.8 < 6.0 bar); "
                            "lagged-first is a false '48 bar' over-cap clamp of a kPa-scaled tag.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live-PT slot versus the lagged-bus publisher on this "
                            "alkylation DCS bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (live 28 + lag 32). Order is "
                            "correctly live-first. The error is the unit bind, not the order: the "
                            "lagged faceplate still has engineering_unit=kPa.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live shell PT on R-4, 2 kHz, 28 us jitter, tag=RX_P.LIVE unit=bar",
                    "lagged bus PI, 1 kHz, 32 us jitter, tag=RX_P.LAG unit=kPa quality=GOOD",
                    "benzene FT (context)",
                    "ethylene FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("shell_cap_bar", 6.0),
                        ("live_bar", 4.8),
                        ("lagged_raw", 48.0),
                        ("lagged_unit", "kPa"),
                        ("lagged_as_bar_if_misread", 48.0),
                        ("benzene_tph", 18.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. R-4 LIVE already alkylating; shell 4.8 bar; benzene 18 t/h.",
                    "2. Lagged faceplate 48 kPa; engineering_unit=kPa; quality=GOOD.",
                    "3. Benzene precursor at 1.080 ms.",
                    "4. Race window [5.400, 5.740] ms.",
                    "5. pt.live.bar 4.8 at 5.400 ms (winner).",
                    "6. pt.lag.kpa 48 at 5.580 ms (loser by 180 us).",
                    "7. Gate at 5.920 ms: WRONG-MODIFY binds 48 kPa as 48 bar.",
                    "8. Benzene 18 -> 3.6 t/h; live shell stays 4.8 bar under cap.",
                    "9. Recycle dump on a legal reactor; lagged tag never needed a clamp.",
                    "10. Delayed (abort_s=720): 12 min recycle while R-4 is recharged.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_benzene"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("benzene_tph", 18.0),
                        ("bind_kpa_as_bar", False),
                        ("unit_bind", "bar"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_bar", 4.8),
                        ("shell_cap_bar", 6.0),
                        ("lagged_raw", 48.0),
                        ("lagged_unit", "kPa"),
                        ("lagged_quality", "GOOD"),
                        ("lagged_as_bar_if_misread", 48.0),
                        ("unit_bind", "bar"),
                        ("benzene_tph", 18.0),
                        ("t_gate_us", 5920),
                        ("correct_benzene_tph", 18.0),
                        ("correct_gate", "ACCEPT"),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 18 t/h benzene because live 4.8 bar is under the "
                "6.0 bar cap; the lagged 48 kPa faceplate is a unit-scaled echo, not a 48 bar "
                "over-cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Faceplate 48 exceeds the 6.0 bar cap (true only if the unit is bar). Apply the "
                "3.6 t/h benzene cut because RX_P.LAG is the highlighted tag. Leave live 4.8 bar "
                "unread as the validating PV.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "shell_bar",
                            OrderedDict(
                                [
                                    ("cap", 6.0),
                                    ("live", 4.8),
                                    ("lagged_raw", 48.0),
                                    ("lagged_unit", "kPa"),
                                    ("executed_unit_bind", "bar"),
                                    ("correct_gate", "ACCEPT"),
                                    ("correct_benzene_tph", 18.0),
                                ]
                            ),
                        ),
                        (
                            "unit_bind",
                            OrderedDict(
                                [
                                    ("t_gate_us", 5920),
                                    ("bind_kpa_as_bar", True),
                                    ("lagged_unit", "kPa"),
                                    ("wrong_unit", True),
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
            ("name", "benzene_cut_kpa_as_bar"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("benzene_tph", 3.6),
                        ("bind_kpa_as_bar", True),
                        ("unit_bind", "bar"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / wrong-unit lagged-bus): 3.6 t/h benzene cut applied because "
                "48 kPa was read as 48 bar. Live 4.8 bar stayed under 6.0. Routing "
                "relay.pt.lag -> policy.unit_clamp; no positive weight to policy.live_hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY clamped a legal alkylation on a unit error. Live 4.8 bar was under "
                "the 6.0 bar cap at t_gate; lagged 48 kPa was a faceplate scale, not 48 bar. "
                "12 min recycle dump (abort_s=720). Correct gate was ACCEPT of 18 t/h benzene "
                "at t_gate_us=5920.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live_shell", "4.8 bar left under 6.0 cap; never needed a cut"),
                        ("lagged_faceplate", "48 kPa bound as 48 bar"),
                        ("dump", "12 min benzene recycle"),
                        ("mission", "alkylation deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-first was the correct order and the live number was under cap; the MODIFY spent that win on a kPa-as-bar bind.",
                    "Delayed (abort_s=720): ES-9 holds 12 min while R-4 is dumped and recharged; next batch 14 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT 18 t/h benzene at t_gate_us=5920; bind_kpa_as_bar=false; unit_bind=bar on the live PT.",
                        ),
                        ("correct_actuator", "R-4_benzene_hold"),
                        ("wrong_unit", "kPa_as_bar"),
                        ("t_gate_us", 5920),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("benzene_tph", 3.6),
                                    ("bind_kpa_as_bar", True),
                                    ("unit_bind", "bar"),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min recycle dump (task/efficiency); live shell stayed legal while feed was spent on a unit-confused lagged tag (safety of a false clamp).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.live.bar (5.400 ms, 4.8 bar LIVE)"),
                        ("loser", "pt.lag.kpa (5.580 ms, 48 kPa lagged)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Lagged-first by < 180 us would still be 48 kPa = 0.48 bar under the "
                            "6.0 bar cap; a correct gate binds pt.live.bar to policy.live_hold at "
                            "t_gate either way. The wrong MODIFY spent the live win on a kPa-as-bar "
                            "clamp.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5920),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the kPa-as-bar bind (5.920 ms, tick 4). "
                "The 12 min recycle dump is delayed surprise, not the inflection.",
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
            "thalamic-relay.alkyl-lag",
            "spikenaut.policy.unit-clamp",
            [
                ("relay.pt.lag", "policy.unit_clamp", 0.74),
                ("relay.pt.live", "policy.unit_clamp", 0.21),
            ],
            "acetylcholine",
            0.08,
            "unit_cap_stdp; ACh tags the (wrong) unit_clamp bind at the live win",
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
                    pop_budget("unit_clamp", 48, 0.45, 300.0, dw),
                    pop("live_hold", 48, 0.90),
                    pop("unit_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r75-392"),
            (
                "title",
                "WRONG-MODIFY at Ethylbenz-Shiel ES-9 / Reactor R-4: live 4.8 bar read correctly; "
                "3.6 t/h benzene cut applied because 48 kPa was bound as 48 bar (wrong-unit / "
                "lagged-bus)",
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
                    "Wrong-modify / wrong-unit lagged-bus. Sidecar arithmetic 4.8 < 6.0 on live "
                    "is true; MODIFY bound to unit_clamp. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "ethylbenzene-alkylation",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-unit",
                        "lagged-bus",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live-first race can still be a wrong gate "
                    "when the MODIFY binds a lagged kPa faceplate as bar. Convictable from "
                    "live_bar < cap, lagged_unit=kPa, and routing without alkylation physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_393():
    ticks = [
        tick(2736, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6840, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7020, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7640, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(7960, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("pt.blast.bar", 1.360, 0.40),
        spike("ae.isp.pps", 2.736, 0.56),
        spike("pt.blast.bar", 4.100, 0.48),
        spike("ae.isp.pps", 6.840, 1.34),
        spike("pt.blast.bar", 7.020, 1.11),
        spike("ctrl.gate", 7.640, 0.98),
        spike("ae.isp.pps", 10.400, 0.81),
        spike("pt.blast.bar", 14.800, 0.62),
        spike("ctrl.gate", 18.200, 0.84),
        spike("ae.isp.pps", 28.400, 0.52),
        spike("pt.blast.bar", 36.100, 0.39),
        spike("ae.isp.pps", 42.200, 0.44),
    ]
    excerpt = independent_excerpt(75393, 120, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "HIL Imperial Smelting shaft S-1 at Isp-Corrie IC-HIL hears tuyere AE at 48 pps "
                "while the blast header remains 1.8 bar under a 2.4 bar cap. AE-first holds the "
                "22 t/h sinter charge; header-first would dispatch because the blast ram looks "
                "legal. The HIL shaft mockup is the authority, not the zinc-lead floor.",
            ),
            ("domain", "imperial-smelting-furnace"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep S-1 from dispatching a growling shaft while blast header pressure remains "
                "under its own cap.",
            ),
            ("t0_us", 1756850400000393),
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
                                "ae.isp.pps 48 over 14 cap",
                                "pt.blast.bar 1.8 under 2.4 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; header-first dispatches 22 t/h sinter on a "
                            "'blast still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one AE puck slot versus the blast-PT publisher on this "
                            "HIL ISP shaft bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + blast 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have dispatched 22 t/h into a growling shaft.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "tuyere AE puck, 50 kHz, 26 us jitter",
                    "blast header PT, 1 kHz, 32 us jitter",
                    "sinter weigh-feeder (context)",
                    "off-gas CO cell (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 14.0),
                        ("observed_ae_pps", 48.0),
                        ("blast_bar", 1.8),
                        ("blast_cap_bar", 2.4),
                        ("proposed_sinter_tph", 22.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. S-1 HIL indexed; 22 t/h sinter armed.",
                    "2. Blast 1.8 bar under 2.4; AE 48 pps over 14.",
                    "3. Blast precursor at 1.360 ms.",
                    "4. Race window [6.840, 7.160] ms.",
                    "5. ae.isp.pps 48 at 6.840 ms (winner).",
                    "6. pt.blast.bar 1.8 at 7.020 ms (loser by 180 us).",
                    "7. Gate at 7.640 ms: REJECT hold, do not dispatch.",
                    "8. Charge 0 t/h; blast left at 1.8 bar.",
                    "9. Shaft inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min shaft reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_sinter"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("sinter_tph", 22.0),
                        ("hold", False),
                        ("blast_bar", 1.8),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 48.0),
                        ("ae_cap_pps", 14.0),
                        ("blast_bar", 1.8),
                        ("blast_cap_bar", 2.4),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 22 t/h sinter because blast 1.8 bar is under 2.4, treating the "
                "48 pps AE as tuyere hash rather than a growling shaft.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Tuyere AE 48 pps won by 180 us, so the shaft is growling, not still a blast-header "
                "story. Blast 1.8 bar is under 2.4 and does not authorize dispatch. REJECT: hold "
                "charge 22 -> 0 t/h. A MODIFY that only trims blast would leave the growl.",
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
                                    ("observed", 48.0),
                                    ("executed_sinter_tph", 0.0),
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
            ("name", "hold_shaft"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("sinter_tph", 0.0),
                        ("hold", True),
                        ("blast_bar", 1.8),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: sinter 22 -> 0 t/h. Blast left at 1.8 bar under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held S-1. AE 48 pps beat blast 1.8 bar by 180 us. Header was "
                "legal; the shaft was not. 8 min shaft reset (abort_s=480) is delayed survey, "
                "not a process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("charge", "held at 0 t/h"),
                        ("blast", "left 1.8 bar < 2.4 cap"),
                        ("shaft", "8 min shaft reset (abort_s=480)"),
                        ("mission", "HIL sinter not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Blast PT never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min shaft reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.isp.pps (6.840 ms, 48 pps)"),
                        ("loser", "pt.blast.bar (7.020 ms, 1.8 bar)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Header-first by < 180 us inside the 320 us window would have dispatched "
                            "22 t/h into a growling shaft. The REJECT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7640),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.640 ms, tick 4). The 8 min shaft "
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
            "thalamic-relay.isp-ae",
            "spikenaut.policy.isp-hold",
            [
                ("relay.ae.isp", "policy.isp_hold", 0.70),
                ("relay.pt.blast", "policy.blast_go", 0.24),
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
                    pop_budget("isp_hold", 56, 0.45, 280.0, dw),
                    pop("blast_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r75-393"),
            (
                "title",
                "Isp-Corrie IC-HIL / Shaft S-1: tuyere AE 48 pps beats blast 1.8 bar by 180 us; "
                "correct REJECT holds sinter charge",
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
                    "Correct REJECT. AE 48 > 14 cap beats legal blast header. "
                    "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "imperial-smelting-furnace",
                    [
                        "reject",
                        "hil",
                        "ae-vs-blast",
                        "growling-shaft",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal blast header can lose to tuyere AE inside a 320 us "
                    "window; reversing 180 us would have dispatched a growling ISP shaft.",
                    3,
                ),
            ),
        ]
    )


def record_394():
    ticks = [
        tick(2880, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7200, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7380, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7840, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8200, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.bed.C", 1.200, 0.40),
        spike("o2.kiln.pct", 2.880, 0.55),
        spike("tc.bed.C", 4.400, 0.48),
        spike("o2.kiln.pct", 7.200, 1.26),
        spike("tc.bed.C", 7.380, 1.08),
        spike("ctrl.gate", 7.840, 0.95),
        spike("o2.kiln.pct", 11.200, 0.78),
        spike("tc.bed.C", 14.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("o2.kiln.pct", 22.600, 0.50),
        spike("tc.bed.C", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(75394, 48, 28000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("feed_tph", 9.0),
            ("o2_pct", 2.4),
            ("bed_C", 748.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Carbothermal kiln K-2 at Olivine-Knock OK-8 already holds free oxygen at 2.4 "
                "percent under a 4.0 percent trip, with bed 748 C under 780. Oxygen-first accepts "
                "the 9.0 t/h LFP precursor; bed-first would have rejected a legal roast on a "
                "'still climbing' model.",
            ),
            ("domain", "lfp-carbothermal-kiln"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the OK-8 roast with free O2 <= 4.0 percent and bed <= 780 C.",
            ),
            ("t0_us", 1756850400000394),
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
                                "o2.kiln.pct 2.4 under 4.0 trip",
                                "tc.bed.C 748 under 780 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Oxygen-first confirms the already-legal 9.0 t/h feed; bed-first "
                            "would have treated the zirconia cell as a climb echo and looked for "
                            "an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one zirconia-O2 slot versus the bed-TC publisher on this "
                            "simulated carbothermal bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (O2 26 + TC 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed feed illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "zirconia O2 cell on kiln off-gas, 26 us jitter",
                    "bed TC well, 32 us jitter",
                    "nitrogen FT (context)",
                    "delta-P bed (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("o2_cap_pct", 4.0),
                        ("observed_o2_pct", 2.4),
                        ("bed_cap_C", 780.0),
                        ("observed_bed_C", 748.0),
                        ("n2_nm3_h", 420.0),
                        ("n2_cap_nm3_h", 520.0),
                        ("proposed_feed_tph", 9.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. K-2 indexed on Olivine-Knock OK-8; 9.0 t/h feed armed.",
                    "2. Caps: O2 4.0 percent, bed 780 C, N2 520 Nm3/h.",
                    "3. Bed-TC precursor at 1.200 ms.",
                    "4. Race window [7.200, 7.560] ms.",
                    "5. o2.kiln.pct 2.4 at 7.200 ms (winner).",
                    "6. tc.bed.C 748 at 7.380 ms (loser by 180 us).",
                    "7. Gate at 7.840 ms: ACCEPT 9.0 t/h already legal.",
                    "8. Feed continues; no extra hold.",
                    "9. 6 min survey confirms O2 still under 4.0 percent.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "feed_9"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("o2_pct", 2.4),
                        ("o2_cap_pct", 4.0),
                        ("bed_C", 748.0),
                        ("bed_cap_C", 780.0),
                        ("n2_nm3_h", 420.0),
                        ("n2_cap_nm3_h", 520.0),
                        ("feed_tph", 9.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 9.0 t/h feed because O2 2.4 percent is under 4.0 and bed "
                "748 C is under 780 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Free oxygen 2.4 percent won by 180 us and is under 4.0. Bed 748 C is under "
                "780 C. Nitrogen 420 Nm3/h is under 520. ACCEPT the already-legal feed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "o2_pct",
                            OrderedDict(
                                [
                                    ("cap", 4.0),
                                    ("observed", 2.4),
                                    ("executed_feed_tph", 9.0),
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
            ("name", "feed_9"),
            ("parameters", OrderedDict(params.items())),
            (
                "gate_effect",
                "ACCEPT: 9.0 t/h feed and 2.4 percent O2 unchanged. Routing relay.o2.kiln -> "
                "policy.feed_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left K-2 on a 9.0 t/h / 2.4 percent O2 roast. Bed-TC hitch did "
                "not justify a hold. 6 min survey confirmed O2 still under 4.0 percent.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "still 9.0 t/h"),
                        ("oxygen", "2.4 under 4.0 trip"),
                        ("bed", "748 C under 780"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Bed TC 748 C hitch is residual, not a runaway trip.",
                    "Delayed (survey_s=360): 6 min survey restacks K-2 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "o2.kiln.pct (7.200 ms, 2.4 percent)"),
                        ("loser", "tc.bed.C (7.380 ms, 748 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Bed-first by < 180 us would only delay confirmation. The feed stays "
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
            "thalamic-relay.o2-cell",
            "spikenaut.policy.feed-go",
            [
                ("relay.o2.kiln", "policy.feed_go", 0.68),
                ("relay.tc.bed", "policy.bed_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_feed_stdp; 5-HT tags the feed_go bind at the zirconia win",
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
                    pop_budget("feed_go", 40, 0.45, 250.0, dw),
                    pop("bed_hold", 32, 0.90),
                    pop("o2_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r75-394"),
            (
                "title",
                "Olivine-Knock OK-8 / Kiln K-2: free O2 2.4 percent beats bed 748 C by 180 us; "
                "ACCEPT already-legal 9.0 t/h LFP precursor",
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
                    "Correct ACCEPT of an already-legal carbothermal roast. total +1.06 = "
                    "0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "lfp-carbothermal-kiln",
                    [
                        "accept",
                        "already-legal",
                        "simulated-carbothermal-loop",
                        "o2-vs-tc",
                        "sidecar-convictable",
                        "simulated",
                    ],
                    "Teaches that a zirconia cell under trip can confirm an already-legal roast "
                    "without a bed-TC hitch becoming a hold.",
                    4,
                ),
            ),
        ]
    )


def record_395():
    ticks = [
        tick(2016, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5040, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5920, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(240000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.loop.C", 0.980, 0.41),
        spike("gc.ketazine.wt", 2.016, 0.60),
        spike("tc.loop.C", 3.200, 0.51),
        spike("gc.ketazine.wt", 5.040, 1.30),
        spike("tc.loop.C", 5.200, 1.12),
        spike("ctrl.gate", 5.640, 0.97),
        spike("gc.ketazine.wt", 8.100, 0.78),
        spike("tc.loop.C", 12.400, 0.62),
        spike("ctrl.gate", 16.200, 0.85),
        spike("gc.ketazine.wt", 20.400, 0.54),
        spike("tc.loop.C", 22.800, 0.43),
    ]
    excerpt = independent_excerpt(75395, 80, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("feed_tph", 6.4),
            ("ketazine_wt_pct", 18.2),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Ketazine loop L-3 at Azine-Tarn AT-4 is already at 18.2 wt percent ketazine under "
                "a 22 cap, jacket 62 C under 70. Assay-first accepts the 6.4 t/h MEK/NH3 feed; "
                "jacket-first would have rejected a legal Raschig circuit on a 'still concentrating' "
                "model.",
            ),
            ("domain", "hydrazine-ketazine"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run L-3 at 6.4 t/h, keep ketazine <= 22 wt percent and jacket <= 70 C, and "
                "leave the circuit on schedule.",
            ),
            ("t0_us", 1756850400000395),
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
                                "gc.ketazine.wt 18.2 under 22 cap",
                                "tc.loop.C 62 under 70 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Assay-first confirms the already-legal 6.4 t/h feed; jacket-first "
                            "would have treated the GC as a hitch echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one online-GC slot versus the jacket-TC publisher on this "
                            "ketazine loop bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (GC 22 + jacket 30): 3.08x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal MEK/NH3 feed.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "online ketazine GC, 2 kHz, 22 us jitter",
                    "jacket TC, 1 kHz, 30 us jitter",
                    "MEK FT (context)",
                    "ammonia FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ketazine_cap_wt_pct", 22.0),
                        ("observed_ketazine_wt_pct", 18.2),
                        ("feed_tph", 6.4),
                        ("jacket_C", 62.0),
                        ("jacket_cap_C", 70.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Loop L-3 indexed on Azine-Tarn AT-4; feed 6.4 t/h armed.",
                    "2. Ketazine 18.2 wt percent under 22; jacket 62 C under 70.",
                    "3. Jacket precursor at 0.980 ms.",
                    "4. Race window [5.040, 5.320] ms.",
                    "5. gc.ketazine.wt 18.2 at 5.040 ms (winner).",
                    "6. tc.loop.C 62 at 5.200 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 6.4 t/h.",
                    "8. Ketazine stays 18.2; jacket stays 62 C.",
                    "9. Circuit stays on-spec.",
                    "10. Delayed (dwell_s=240): 4 min still reseq.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_ketazine_feed"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ketazine_wt_pct", 18.2),
                        ("ketazine_cap_wt_pct", 22.0),
                        ("feed_tph", 6.4),
                        ("jacket_C", 62.0),
                        ("jacket_cap_C", 70.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 6.4 t/h because ketazine 18.2 is under 22 and jacket 62 C is "
                "under 70.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Ketazine GC 18.2 wt percent won by 160 us, so the circuit is already legal, not "
                "still concentrating. Jacket 62 C is under 70. ACCEPT the 6.4 t/h feed. A REJECT "
                "would idle a legal Raschig loop.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ketazine_wt_pct",
                            OrderedDict(
                                [
                                    ("cap", 22.0),
                                    ("observed", 18.2),
                                    ("executed_feed_tph", 6.4),
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
            ("name", "hold_ketazine_feed"),
            ("parameters", OrderedDict(params.items())),
            ("gate_effect", "ACCEPT: leave 6.4 t/h; ketazine 18.2; jacket legal."),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 6.4 t/h ketazine feed. Assay 18.2 beat jacket "
                "62 C by 160 us. 4 min still reseq (dwell_s=240) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "6.4 t/h held"),
                        ("ketazine", "18.2 < 22 cap"),
                        ("loop", "L-3 on-spec"),
                        ("reseq", "4 min still reseq (dwell_s=240)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Jacket never approached 70 C; ketazine was already under cap.",
                    "Delayed (dwell_s=240): 4 min still reseq after the pulse.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "gc.ketazine.wt (5.040 ms, 18.2 wt percent)"),
                        ("loser", "tc.loop.C (5.200 ms, 62 C)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Jacket-first by < 160 us inside the 280 us window would have REJECTED "
                            "an already-legal MEK/NH3 feed. The ACCEPT is still the correct gate.",
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
    dw = 0.28
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.ketazine-gc",
            "spikenaut.policy.feed-go",
            [
                ("relay.gc.ketazine", "policy.feed_go", 0.67),
                ("relay.tc.loop", "policy.feed_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the ketazine-GC win as an already-legal feed",
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
            ("decision_window_ms", dw),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("feed_go", 40, 0.45, 250.0, dw),
                    pop("feed_hold", 32, 0.90),
                    pop("kz_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r75-395"),
            (
                "title",
                "Azine-Tarn AT-4 / Loop L-3: ketazine 18.2 wt percent beats jacket 62 C by "
                "160 us; correct ACCEPT of an already-legal 6.4 t/h MEK/NH3 feed",
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
                    "Correct ACCEPT. ketazine 18.2 < 22; jacket 62 < 70. "
                    "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "hydrazine-ketazine",
                    [
                        "accept",
                        "designed",
                        "gc-vs-jacket",
                        "already-legal-feed",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal jacket can lose to ketazine GC inside a 280 us "
                    "window; reversing 160 us would have REJECTED an already-legal Raschig feed.",
                    5,
                ),
            ),
        ]
    )
