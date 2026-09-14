def record_411():
    excerpt, extra = lif_411_excerpt()
    extra = OrderedDict(extra)
    extra["abort_s"] = 840
    extra["delayed_surprise_s"] = 840
    ticks = [
        tick(2440, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6120, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(6308, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6840, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22600, 0.04, -0.45, -0.03, -0.01, -0.01),
        tick(840000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Zone bar Z-4 at Bardeen-Clart BC-2 is driving 44 kW of RF coil while the "
                "germanium solid-liquid interface sits at 972 C against a 940 C coil-power cap. "
                "Temperature-first cuts coil to 33 kW; coil-first would keep 44 kW because the "
                "oscillator 8.4 kHz is still under the 9.0 kHz detune ceiling. A hairline already "
                "seated in the quartz ampoule does not appear on interface T or coil kW until the AE dump.",
            ),
            ("domain", "germanium-zone-refiner"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep Zone bar Z-4 interface <= 940 C and finish the pass without dumping "
                "molten germanium onto the boat floor.",
            ),
            ("t0_us", 1756850400000411),
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
                                "tc.iface.C 972 over 940 coil-power cap",
                                "ft.coil.kW 44 with oscillator 8.4 kHz under 9.0",
                            ],
                        ),
                        (
                            "semantics",
                            "Temperature-first latches coil clamp 44 -> 33 kW; "
                            "coil-first keeps 44 kW on a 'still under oscillator-detune ceiling' model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one interface-TC slot versus the RF-coil kW publisher on this "
                            "zone-refiner skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 188 us vs combined jitter 62 us (TC 28 + kW 34): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 188 us inside the 400 us "
                            "window would have kept 44 kW; predicted next-sample 981 C > 940 "
                            "coil-power cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "interface thermocouple lance, 2 kHz, 28 us jitter",
                    "RF coil kW + oscillator tach, 1 kHz, 34 us jitter",
                    "ampoule AE puck (context)",
                    "boat IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("iface_cap_C", 940.0),
                        ("observed_iface_C", 972.0),
                        ("coil_kW", 44.0),
                        ("oscillator_kHz", 8.4),
                        ("oscillator_cap_kHz", 9.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Zone bar Z-4 in pass; coil 44 kW; interface 972 C.",
                    "2. Oscillator 8.4 kHz under 9.0 detune; pass armed.",
                    "3. Coil-kW precursor at 1.180 ms.",
                    "4. Race window [6.000, 6.400] ms.",
                    "5. tc.iface.C 972 C at 6.120 ms (winner).",
                    "6. ft.coil.kW 44 at 6.308 ms (loser by 188 us).",
                    "7. Gate at 6.840 ms: MODIFY clamp 44 -> 33 kW.",
                    "8. After clamp interface 928 C <= 940; oscillator still 8.4 kHz.",
                    "9. At 22.600 ms a seated quartz hairline dumps 0.4 kg of Ge onto the boat.",
                    "10. 14 min boat isolate (abort_s=840); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_rf_coil"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("coil_kW", 44.0),
                        ("iface_C", 972.0),
                        ("oscillator_kHz", 8.4),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("iface_C", 972.0),
                        ("iface_cap_C", 940.0),
                        ("predicted_unclamped_next_C", 981.0),
                        ("coil_kW", 44.0),
                        ("oscillator_kHz", 8.4),
                        ("oscillator_cap_kHz", 9.0),
                        ("race_margin_us", 188),
                        ("combined_jitter_us", 62),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 44 kW because oscillator 8.4 kHz is under 9.0, treating the "
                "972 C interface as a still-sooty lance rather than a coil-power miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Interface 972 C won by 188 us, so the bar is over the 940 C coil-power "
                "cap, not still an oscillator-detune story. Holding 44 kW predicts next-sample "
                "981 C > 940. MODIFY: coil 44 -> 33 kW. Observed after clamp 928 C <= "
                "940. A full REJECT is not indicated: a clean zone pass accepts 33 kW.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "iface_C",
                            OrderedDict(
                                [
                                    ("cap", 940.0),
                                    ("observed", 972.0),
                                    ("predicted_unclamped_next", 981.0),
                                    ("clamped_coil_kW", 33.0),
                                    ("observed_after_clamp", 928.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 188),
                                    ("combined_jitter_us", 62),
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
            ("name", "clamped_rf_coil"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("coil_kW", 33.0),
                        ("iface_C", 928.0),
                        ("oscillator_kHz", 8.4),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: coil 44 -> 33 kW. Process-correct vs the 940 C coil-power cap. "
                "Seated ampoule hairline still dumps at 22.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held interface at 928 C. At 22.600 ms a seated quartz "
                "hairline already in the ampoule dumped 0.4 kg of Ge onto the boat. Clamp "
                "reduced dump energy; it did not prevent the dump. Partnered negative: process "
                "heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("iface", "clamp executed; peak 928 C <= 940 cap"),
                        ("ampoule", "hairline dump at 22.600 ms; 0.4 kg Ge"),
                        ("repair", "14 min boat isolate (abort_s=840)"),
                        ("mission", "BC-2 zone pass incomplete this cycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither interface T nor coil kW predicted the seated ampoule hairline; ae.ampoule.crack is a new channel at 22.600 ms, 15.760 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=840): 14 min boat isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "14 min boat isolate after the ampoule hairline. Safety head -0.64 "
                "prices the dump; task_progress stays +0.30 because the clamp completed.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.iface.C (6.120 ms, 972 C)"),
                        ("loser", "ft.coil.kW (6.308 ms, 44 kW)"),
                        ("margin_us", 188),
                        (
                            "counterfactual_if_reversed",
                            "Coil-first by < 188 us inside the 400 us window would have kept "
                            "44 kW; predicted next-sample 981 C would have missed the 940 "
                            "coil-power cap even without the hairline. The MODIFY is still the "
                            "correct process. The dump is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22600),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.600 ms ampoule hairline (tick t_us=22600), inside "
                "the 42 ms raster. The correct MODIFY at 6.840 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=840 boat-isolate tick.",
            ),
        ]
    )
    spikes = [
        spike("ft.coil.ctx", 1.180, 0.41),
        spike("tc.iface.C", 2.440, 0.58),
        spike("ft.coil.kW", 3.880, 0.50),
        spike("tc.iface.C", 6.120, 1.31),
        spike("ft.coil.kW", 6.308, 1.12),
        spike("ctrl.gate", 6.840, 0.97),
        spike("tc.iface.C", 8.200, 0.82),
        spike("ft.coil.kW", 10.550, 0.64),
        spike("ctrl.gate", 14.100, 0.86),
        spike("ae.ampoule.crack", 22.600, 1.48),
        spike("ae.ampoule.crack", 24.400, 0.93),
        spike("ft.coil.ctx", 29.800, 0.40),
        spike("tc.iface.C", 36.200, 0.55),
    ]
    ras = raster_core(
        42,
        80,
        22,
        74,
        routing(
            "thalamic-relay.bc-iface",
            "spikenaut.policy.coil-clamp",
            [
                ("relay_iface_C", "policy_coil_clamp", 0.68),
                ("relay_coil_kw", "policy_coil_hold", 0.29),
                ("relay_ae_ampoule", "policy_coil_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at interface win (6.120 ms) opens a 42 ms "
            "eligibility trace that still covers the 22.600 ms ampoule hairline",
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
                    pop("coil_clamp", 50, 0.50, 200.0, 4),
                    pop("coil_hold", 40, 0.80, 50.0, 1),
                    pop("ampoule_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r79-411"),
            (
                "title",
                "Bardeen-Clart BC-2 / Zone bar Z-4: interface 972 C beats coil 44 kW by 188 us; "
                "correct MODIFY still eats an in-window ampoule hairline (partnered negative total -0.48)",
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
                    "boat isolate (abort_s=840) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "germanium-zone-refiner",
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
                    "14 min boat isolate.",
                    1,
                ),
            ),
        ]
    )


def record_412():
    ticks = [
        tick(2210, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5480, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5762, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6180, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6400, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(540000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.cell.ctx", 1.050, 0.42),
        spike("i.hs.kA", 2.210, 0.57),
        spike("i.ls.kA", 3.080, 0.88),
        spike("i.hs.kA", 5.580, 1.29),
        spike("i.ls.kA", 5.762, 1.10),
        spike("ctrl.gate", 6.180, 0.96),
        spike("i.hs.kA", 7.800, 0.80),
        spike("i.ls.kA", 10.200, 0.63),
        spike("ctrl.gate", 13.500, 0.84),
        spike("enc.cell.ctx", 18.400, 0.41),
        spike("i.hs.kA", 22.100, 0.54),
        spike("i.ls.kA", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(79412, 96, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Electrowinning cell Te-7 at Telluride-Twistle TT-5 still prints live high-select "
                "cathode current 11.60 kA against a 9.50 kA cell cap, with both shunt legs LIVE on "
                "the same bipolar cell. High-select shunt A is the winning transmitter at 11.60 kA; "
                "low-select shunt B is the currently-losing transmitter at 3.80 kA. HS-first should "
                "MODIFY-cut the WINNING leg 11.60 -> 8.20 kA; a weak supervisor binds the losing "
                "leg and MODIFY-cuts B 3.80 -> 0.90 kA while A stays 11.60.",
            ),
            ("domain", "tellurium-electrowinning"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Cut cathode current on the WINNING high-select shunt until live HS stays <= 9.50 "
                "kA; do not spend the cut on the currently-losing low-select transmitter.",
            ),
            ("t0_us", 1756850400000412),
            ("gate_latency_us", 540),
            ("race_window_us", 380),
            ("race_window_rel_ms", [5.50, 5.88]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "i.hs.kA 11.60 kA on the winning high-select shunt",
                                "i.ls.kA 3.80 kA currently-losing low-select shunt",
                            ],
                        ),
                        (
                            "semantics",
                            "HS-first should latch a winning-leg cut 11.60 -> 8.20 kA; "
                            "LS-first is a false 'losing transmitter still the select' bind that "
                            "cuts only the cold shunt.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one live-HS sample versus the LS-shunt publisher "
                            "on this tankhouse PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 182 us vs combined jitter 60 us (HS 28 + LS 32). Order is "
                            "correctly HS-first. The error is which selector leg the "
                            "MODIFY binds, not the race order.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "cathode high-select shunt, 4 Hz packet, 28 us jitter on this sample",
                    "cathode low-select shunt encoder, 32 us jitter",
                    "cell voltage PT (context)",
                    "electrolyte TC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_kA", 9.50),
                        ("hs_live_kA", 11.60),
                        ("ls_live_kA", 3.80),
                        ("selector", "high_select"),
                        ("both_legs_live", True),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Te-7 in pass; HS/LS shunts 11.60 / 3.80 kA armed, both LIVE.",
                    "2. Live HS 11.60 > 9.50 cap; losing LS 3.80 under cap.",
                    "3. LS shunt sampled at 3.080 ms.",
                    "4. Race window [5.500, 5.880] ms.",
                    "5. i.hs.kA 11.60 at 5.580 ms (winner).",
                    "6. i.ls.kA 3.80 at 5.762 ms (loser by 182 us).",
                    "7. Gate at 6.180 ms: WRONG MODIFY losing leg 3.80 -> 0.90 kA; winning stays 11.60.",
                    "8. selector_bound=losing; winning_kA unchanged 11.60; HS stays 11.48 > 9.50.",
                    "9. Cell remains over-current for the rest of the pass.",
                    "10. Delayed (abort_s=540): 9 min off-spec Te dump window.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_hs_ls_current"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("winning_kA", 11.60),
                        ("losing_kA", 3.80),
                        ("selector_bound", "none"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("hs_live_kA", 11.60),
                        ("cap_kA", 9.50),
                        ("ls_live_kA", 3.80),
                        ("both_legs_live", True),
                        ("selector", "high_select"),
                        ("live_over_cap", True),
                        ("race_margin_us", 182),
                        ("combined_jitter_us", 60),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping 11.60 / 3.80 kA because 11.60 kA is treated as a "
                "header smear rather than a cell-current miss. Live HS 11.60 is over the 9.50 "
                "cap; the correct gate cuts the WINNING high-select leg.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Live HS 11.60 kA is over the 9.50 cap, so a cut is required. A weak "
                "supervisor binds the currently-losing low-select transmitter that lost the "
                "race and MODIFY-cuts shunt B 3.80 -> 0.90 kA, leaving shunt A at 11.60 kA. "
                "Both legs are LIVE; the losing transmitter cannot dump the current. The "
                "MODIFY is plausible to a supervisor that treats HS/LS as a single shunt.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "current_kA",
                            OrderedDict(
                                [
                                    ("cap", 9.50),
                                    ("live_hs", 11.60),
                                    ("executed_losing_kA", 0.90),
                                    ("executed_winning_kA", 11.60),
                                ]
                            ),
                        ),
                        (
                            "selector",
                            OrderedDict(
                                [
                                    ("bound", "losing"),
                                    ("both_legs_live", True),
                                    ("winning_unchanged", True),
                                    ("t_gate_us", 6180),
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
            ("name", "losing_leg_cut"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("winning_kA", 11.60),
                        ("losing_kA", 0.90),
                        ("selector_bound", "losing"),
                        ("both_legs_live", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "WRONG MODIFY: losing leg 3.80 -> 0.90 kA; winning leg left at 11.60. Live HS "
                "11.60 remains over 9.50. selector_bound=losing.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-modify / selector-wrong-leg. Live high-select 11.60 stayed over the "
                "9.50 cap. The supervisor cut only the currently-losing transmitter to 0.90 kA "
                "and left the winning leg at 11.60 kA. Nine minutes of off-spec Te dump "
                "(abort_s=540).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("losing_leg", "cut; 0.90 kA vs filed 3.80"),
                        ("winning_leg", "unchanged; 11.60 kA still over cap"),
                        ("live_hs", "11.48 kA still over 9.50"),
                        ("mission", "TT-5 tankhouse pass over-current"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live HS winning a 182 us race did not prevent a losing-leg MODIFY; reversing order would still have been a wrong bind if the supervisor keyed on the LS shunt.",
                    "Delayed (abort_s=540): 9 min off-spec Te dump window. Named un-netted loss.",
                ],
            ),
            (
                "recovery",
                "MODIFY; cut WINNING high-select shunt A 11.60 -> 8.20 kA; leave losing shunt B "
                "at 3.80 kA; bind live HS; do not spend a cell-current cut on the currently-losing "
                "transmitter while both_legs_live is true.",
            ),
            (
                "cost",
                OrderedDict(
                    [
                        ("actual_hs_kA", 11.60),
                        ("actual_cap_kA", 9.50),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("winning_kA", 11.60),
                                    ("losing_kA", 0.90),
                                    ("selector_bound", "losing"),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "9 min off-spec Te dump (task/efficiency); legal winning-leg cut "
                            "was skipped so live 11.60 stayed over 9.50 (safety of a false trim).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "i.hs.kA (5.580 ms, 11.60 kA)"),
                        ("loser", "i.ls.kA (5.762 ms, 3.80 kA)"),
                        ("margin_us", 182),
                        (
                            "counterfactual_if_reversed",
                            "LS-first by < 182 us would still leave live 11.60 over cap; a "
                            "correct gate binds i.hs.kA to policy_winning_cut either way. The "
                            "wrong MODIFY spent the live win on a losing-leg clamp.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6180),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong MODIFY (6.180 ms, tick 4). "
                "The 9 min Te miss is delayed surprise, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        28,
        96,
        32,
        86,
        routing(
            "thalamic-relay.te-hs",
            "spikenaut.policy.losing-cut",
            [
                ("relay_hs_live", "policy_losing_cut", 0.73),
                ("relay_ls_stem", "policy_losing_cut", 0.22),
            ],
            "acetylcholine",
            0.08,
            "te_selector_stdp; ACh tags the (wrong) losing_cut bind at the live-HS win",
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
            ("decision_window_ms", 0.38),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("losing_cut", 42, 0.45, 250.0, 4),
                    pop("winning_cut", 42, 0.90),
                    pop("hs_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r79-412"),
            (
                "title",
                "WRONG-MODIFY at Telluride-Twistle TT-5 / Cell Te-7: live HS 11.60 over cap; "
                "current cut spent on currently-losing selector leg (selector-wrong-leg)",
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
                    "Wrong-modify / selector-wrong-leg. Sidecar arithmetic live HS 11.60 > 9.50 "
                    "is true and winning_kA stays 11.60; MODIFY bound the losing transmitter. "
                    "total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "tellurium-electrowinning",
                    [
                        "modify",
                        "wrong-gate",
                        "selector-wrong-leg",
                        "winning-leg-unchanged",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct HS-first race can still be a wrong gate "
                    "when routing.table[0].to is policy_losing_cut and winning_kA is unchanged. "
                    "Convictable from hs_live_kA vs cap_kA without Te electrochemistry.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_413():
    ticks = [
        tick(2810, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(7180, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7368, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7980, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(8200, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(360000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("tc.if.ctx", 1.420, 0.43),
        spike("ae.if.pps", 2.880, 0.61),
        spike("enc.org.m3", 4.550, 0.49),
        spike("ae.if.pps", 7.180, 1.34),
        spike("enc.org.m3", 7.368, 1.11),
        spike("ctrl.gate", 7.980, 1.02),
        spike("ae.if.pps", 10.200, 0.78),
        spike("tc.if.ctx", 14.800, 0.44),
        spike("enc.org.m3", 19.400, 0.58),
        spike("ctrl.gate", 24.600, 0.81),
        spike("ae.if.pps", 31.200, 0.53),
        spike("enc.org.m3", 38.800, 0.46),
        spike("tc.if.ctx", 44.100, 0.37),
    ]
    excerpt = independent_excerpt(79413, 112, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Column HF-3 on the Hafnia-Dumble HD-HIL pad is armed for a 0.22 m3/h organic "
                "raise while an interface AE packet reads 55 pps against a 15 pps move cap. An "
                "organic-flow encoder, lit by the pad lamp, still reads 4.8 m3 under a 7.0 m3 "
                "travel look. AE-first latches REJECT hold; encoder-first would commit a 0.22 "
                "m3/h raise into a live emulsion band.",
            ),
            ("domain", "hafnium-separation-column"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not raise Column HF-3 organic unless interface AE <= 15 pps; keep feed "
                "0.0 m3/h until the injected emulsion band recovers.",
            ),
            ("t0_us", 1756850400000413),
            ("gate_latency_us", 860),
            ("race_window_us", 310),
            ("race_window_rel_ms", [7.10, 7.41]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.if.pps 55 pps",
                                "enc.org.m3 4.8 m3 under 7.0",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches REJECT hold 0.0 m3/h organic; encoder-first would "
                            "commit a 0.22 m3/h raise on an apparent 4.8 m3 under-read.",
                        ),
                        (
                            "window_derivation",
                            "310 us = one interface-AE sample versus encoder integration on this "
                            "hafnium HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 188 us vs combined jitter 58 us (AE 26 + ENC 32): 3.2x over a "
                            "2.0x trust floor. Pad injects the encoder lamp 110-150 us before the "
                            "AE (geometric lag, not a sensor fault); the 4.8 m3 packet is still "
                            "the loser in this 310 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "interface AE puck, 5 kHz burst, 26 us jitter",
                    "organic flow encoder, 200 Hz, 32 us jitter",
                    "band thermocouple (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("if_cap_pps", 15.0),
                        ("observed_if_pps", 55.0),
                        ("org_m3", 4.8),
                        ("org_look_m3", 7.0),
                        ("proposed_raise_m3_h", 0.22),
                        ("lamp_inject_lead_us", [110, 150]),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        (
                            "pad",
                            "Hafnia-Dumble HD-HIL MIBK/thiocyanate column mockup with physical organic pump",
                        ),
                        ("injected", "interface AE burst + encoder lamp spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop hafnium SX column. Invented plant; not a live Hf shop.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Column HF-3 on the HD-HIL pad; 0.22 m3/h organic armed.",
                    "2. Encoder lamp injected 110-150 us before AE sees 55 pps.",
                    "3. Band-TC precursor at 1.420 ms.",
                    "4. Race window [7.100, 7.410] ms.",
                    "5. ae.if.pps 55 pps at 7.180 ms (winner).",
                    "6. enc.org.m3 4.8 m3 at 7.368 ms (loser by 188 us).",
                    "7. Gate at 7.980 ms: REJECT hold 0.0 m3/h; do not raise 0.22.",
                    "8. Interface remains over 15 pps this cycle; feed cap held.",
                    "9. Pump re-seat queued on the pad.",
                    "10. Delayed (abort_s=360): 6 min band re-settle and lamp-spectrum retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "raise_hf_organic"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("raise_m3_h", 0.22),
                        ("hold", False),
                        ("encoder_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("if_pps", 55.0),
                        ("if_cap_pps", 15.0),
                        ("org_m3", 4.8),
                        ("org_look_m3", 7.0),
                        ("race_margin_us", 188),
                        ("combined_jitter_us", 58),
                        ("abort_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 0.22 m3/h organic raise because encoder 4.8 m3 looks under "
                "the 7.0 m3 travel look, treating AE 55 pps as a noisy bus echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Interface AE 55 pps is over the 15 pps organic-move cap. Encoder 4.8 m3 is a HIL "
                "lamp under-read, not a clearance. REJECT: hold 0.0 m3/h; do not commit a "
                "0.22 m3/h raise.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "if_pps",
                            OrderedDict(
                                [
                                    ("cap", 15.0),
                                    ("observed", 55.0),
                                    ("org_m3", 4.8),
                                ]
                            ),
                        ),
                        (
                            "raise_m3_h",
                            OrderedDict([("proposed", 0.22), ("executed", 0.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 188),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 3.24),
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
            ("name", "hold_for_band_drop"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("raise_m3_h", 0.0),
                        ("hold", True),
                        ("encoder_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0.0 m3/h; 0.22 m3/h raise cancelled. AE 55 > 15 pps cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Column HF-3 at 0.0 m3/h organic. Emulsion band over cap "
                "this cycle; feed cap held. Encoder apparent was not treated as an AE clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("organic", "held; 0.0 m3/h"),
                        ("band", "still over 15 pps this cycle"),
                        ("encoder", "4.8 m3 unused as clearance"),
                        ("mission", "raise deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: encoder lamp was injected 110-150 us before the AE puck, yet interface AE still won the 310 us race.",
                    "Delayed (abort_s=360): pad policy update forbids treating organic encoder m3 as an interface-AE substitute after a 6 min re-settle.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.if.pps (7.180 ms, 55 pps)"),
                        ("loser", "enc.org.m3 (7.368 ms, 4.8 m3)"),
                        ("margin_us", 188),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 188 us inside the 310 us window would have committed "
                            "a 0.22 m3/h raise with AE 55 > 15 pps cap. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7980),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (7.980 ms, tick 4) as the hold "
                "lands. The 6 min re-settle is delayed surprise bound to abort_s=360.",
            ),
        ]
    )
    ras = raster_core(
        46,
        112,
        20,
        103,
        routing(
            "thalamic-relay.hf-ae",
            "spikenaut.policy.feed-hold",
            [
                ("relay_if_pps", "policy_feed_hold", 0.70),
                ("relay_enc_org", "policy_enc_raise", 0.24),
            ],
            "dopamine",
            0.15,
            "band_hold_stdp; DA tags the feed_hold bind at the interface-AE win",
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
            ("decision_window_ms", 0.31),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("feed_hold", 70, 0.48, 230.0, 5),
                    pop("enc_raise", 50, 0.85),
                    pop("if_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r79-413"),
            (
                "title",
                "Hafnia-Dumble HD-HIL / Column HF-3: interface AE 55 pps beats organic encoder "
                "4.8 m3 by 188 us; correct REJECT holds the organic raise",
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
                    "Correct REJECT. Interface AE over cap beats encoder under-read. "
                    "total 0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06. Tick 6 binds abort_s=360.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "hafnium-separation-column",
                    [
                        "reject",
                        "hil",
                        "interface-ae",
                        "encoder-underread",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a HIL organic-encoder under-read losing a 188 us race does not "
                    "clear an interface-AE over-rate. Hold is distillable from pps vs cap.",
                    3,
                ),
            ),
        ]
    )


def record_414():
    ticks = [
        tick(3220, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(7920, 0.08, 0.05, 0.04, 0.03, 0.02),
        tick(8110, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(8360, 0.12, 0.09, 0.05, 0.04, 0.02),
        tick(8980, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(120000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.ag.ctx", 1.105, 0.43),
        spike("do.broth.pct", 3.220, 0.59),
        spike("ir.jacket.C", 5.010, 0.50),
        spike("do.broth.pct", 7.920, 1.27),
        spike("ir.jacket.C", 8.110, 1.09),
        spike("ctrl.gate", 8.360, 0.97),
        spike("do.broth.pct", 11.200, 0.78),
        spike("ir.jacket.C", 14.880, 0.61),
        spike("ctrl.gate", 18.400, 0.84),
        spike("do.broth.pct", 22.050, 0.56),
        spike("enc.ag.ctx", 23.400, 0.40),
    ]
    excerpt = independent_excerpt(79414, 52, 24000, 13, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("feed_t_h", 9.6),
            ("do_pct", 34.0),
            ("jacket_C", 28.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Fermenter F-11 at Lysyl-Ing LI-8 is already holding broth dissolved oxygen at "
                "34 percent over an 18 percent DO floor with a 9.6 t/h glucose feed already "
                "filed under the 12.0 t/h inlet ceiling. Jacket-IR-first would extra-clamp a "
                "legal broth; DO-first ACCEPTS the filed 9.6 t/h lysine pass.",
            ),
            ("domain", "lysine-fermenter"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold the 9.6 t/h glucose feed while DO stays >= 18 percent and feed stays <= "
                "12.0 t/h; do not extra-clamp a legal aerated lysine fermenter.",
            ),
            ("t0_us", 1756850400000414),
            ("gate_latency_us", 400),
            ("race_window_us", 440),
            ("race_window_rel_ms", [7.80, 8.24]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "do.broth.pct 34 percent over 18 floor",
                                "ir.jacket.C 28 C smear under 50 look",
                            ],
                        ),
                        (
                            "semantics",
                            "DO-first ACCEPTS the already-legal 9.6 t/h feed. Jacket-first "
                            "would extra-clamp because 28 C looks under a 50 C broth look.",
                        ),
                        (
                            "window_derivation",
                            "440 us = one DO-probe slot versus jacket-IR group delay on this "
                            "fermenter skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 190 us vs combined jitter 66 us (DO 32 + IR 34): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 190 us inside the 440 us "
                            "window would have extra-clamped a legal 34 percent / 9.6 t/h pass.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "broth optical DO probe, 1 kHz, 32 us jitter",
                    "jacket IR pyrometer, 2 kHz, 34 us jitter",
                    "agitator encoder (context)",
                    "OUR offgas (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("do_floor_pct", 18.0),
                        ("observed_do_pct", 34.0),
                        ("jacket_C", 28.0),
                        ("feed_cap_t_h", 12.0),
                        ("proposed_feed_t_h", 9.6),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "unstructured Monod + kLa correlation, seed 79414; "
                            "12-zone aerated tank; NOT lumped-CSTR, NOT U-RANS, NOT a wet-stand",
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
                    "1. Fermenter F-11 in pass; 9.6 t/h glucose armed.",
                    "2. DO 34 percent over 18 floor; feed 9.6 under 12.0 t/h inlet.",
                    "3. Agitator encoder precursor at 1.105 ms.",
                    "4. Race window [7.800, 8.240] ms.",
                    "5. do.broth.pct 34 percent at 7.920 ms (winner).",
                    "6. ir.jacket.C 28 C at 8.110 ms (loser by 190 us).",
                    "7. Gate at 8.360 ms: ACCEPT 9.6 t/h; executed identical to proposed.",
                    "8. DO stays 33.8 percent > 18; feed 9.62 t/h < 12.0.",
                    "9. Jacket remaining a shell glint did not require an extra clamp.",
                    "10. Delayed (survey_s=120): 120 s titer coupon on the harvest lock.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_lysine_feed"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("do_pct", 34.0),
                        ("do_floor_pct", 18.0),
                        ("jacket_C", 28.0),
                        ("feed_cap_t_h", 12.0),
                        ("race_margin_us", 190),
                        ("combined_jitter_us", 66),
                        ("survey_s", 120),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 9.6 t/h feed: DO 34 percent is over the "
                "18 percent floor and 9.6 t/h is under 12.0 t/h inlet.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "DO 34 percent won by 190 us and is over the 18 percent floor. Jacket "
                "28 C is a shell glint, not a broth miss. ACCEPT the filed 9.6 t/h "
                "feed. Executed identical to proposed. An extra clamp is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "do_pct",
                            OrderedDict(
                                [
                                    ("floor", 18.0),
                                    ("observed", 34.0),
                                    ("executed_feed_t_h", 9.6),
                                ]
                            ),
                        ),
                        (
                            "jacket_C",
                            OrderedDict([("look", 50.0), ("observed", 28.0)]),
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
            ("name", "hold_lysine_feed"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 9.6 t/h feed. DO 34 percent > 18 floor.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 9.6 t/h glucose feed. DO stayed 33.8 percent over "
                "18. Jacket remaining a shell glint was the losing channel and did not "
                "justify an extra clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held; 9.6 t/h"),
                        ("do", "33.8 percent > 18 floor"),
                        ("jacket", "28 C glint unused as broth miss"),
                        ("broth", "pass continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Jacket IR 28 C losing a 190 us race did not predict a DO miss; reversing 190 us would have extra-clamped a legal 34 percent pass.",
                    "Delayed (survey_s=120): 120 s titer coupon on the harvest lock; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "do.broth.pct (7.920 ms, 34 percent)"),
                        ("loser", "ir.jacket.C (8.110 ms, 28 C)"),
                        ("margin_us", 190),
                        (
                            "counterfactual_if_reversed",
                            "Jacket-first by < 190 us inside the 440 us window would have extra-clamped "
                            "a legal pass. DO-first confirms the filed feed.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 8360),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (8.360 ms, tick 4). The 120 s titer coupon "
                "is delayed surprise bound to survey_s=120, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        24,
        52,
        40,
        50,
        routing(
            "thalamic-relay.do-probe",
            "spikenaut.policy.feed-accept",
            [
                ("relay_do_pct", "policy_feed_accept", 0.66),
                ("relay_jacket_IR", "policy_extra_clamp", 0.23),
            ],
            "serotonin",
            0.12,
            "do_confirm_stdp; 5-HT tags the feed_accept bind at the DO-probe win",
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
            ("decision_window_ms", 0.44),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("feed_accept", 50, 0.50, 180.0, 4),
                    pop("extra_clamp", 40, 0.85, 40.0, 1),
                    pop("ir_veto", 22, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r79-414"),
            (
                "title",
                "Lysyl-Ing LI-8 / Fermenter F-11: DO 34 percent beats jacket IR 28 C by 190 us; "
                "ACCEPT already-legal 9.6 t/h lysine glucose feed",
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
                    "Clean ACCEPT of an already-legal lysine glucose feed. "
                    "total 1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08. Tick 6 binds survey_s=120.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "lysine-fermenter",
                    [
                        "accept",
                        "simulated",
                        "do-vs-jacket",
                        "feed-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging jacket IR losing a 190 us race does not require an "
                    "extra clamp when broth DO is already over the aeration floor.",
                    4,
                ),
            ),
        ]
    )


def record_415():
    ticks = [
        tick(1980, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(4980, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(5160, 0.08, 0.05, 0.03, 0.02, 0.01),
        tick(5360, 0.12, 0.09, 0.06, 0.04, 0.02),
        tick(6020, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(240000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.grate.ctx", 0.880, 0.44),
        spike("tc.bed.C", 1.980, 0.61),
        spike("ir.offgas.C", 3.410, 0.52),
        spike("tc.bed.C", 4.980, 1.30),
        spike("ir.offgas.C", 5.160, 1.12),
        spike("ctrl.gate", 5.360, 0.99),
        spike("tc.bed.C", 8.050, 0.77),
        spike("ir.offgas.C", 11.400, 0.58),
        spike("ctrl.gate", 14.900, 0.83),
        spike("tc.bed.C", 18.200, 0.54),
        spike("enc.grate.ctx", 21.100, 0.39),
    ]
    excerpt = independent_excerpt(79415, 84, 22000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("feed_t_h", 3.6),
            ("bed_C", 604.0),
            ("offgas_C", 418.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Roaster R-6 at Selenous-Stank SS-4 reads bed 604 C against a 655 C thermal trip "
                "with a 3.6 t/h selenium-cake feed already filed under the 5.0 t/h grate ceiling. "
                "Offgas-IR-first would extra-clamp a legal hearth; bed-TC-first ACCEPTS the "
                "filed 3.6 t/h pass.",
            ),
            ("domain", "selenium-roaster"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold the 3.6 t/h cake feed while bed stays <= 655 C and feed stays <= 5.0 t/h; "
                "do not extra-clamp a legal selenium roaster.",
            ),
            ("t0_us", 1756850400000415),
            ("gate_latency_us", 360),
            ("race_window_us", 300),
            ("race_window_rel_ms", [4.90, 5.20]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.bed.C 604 C under 655",
                                "ir.offgas.C 418 C smear under 500 look",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-TC-first ACCEPTS the already-legal 3.6 t/h feed. Offgas-first would "
                            "extra-clamp because 418 C looks under a 500 C hearth look.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one bed-TC slot versus offgas-IR group delay on this "
                            "roaster skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (TC 26 + IR 32): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 300 us "
                            "window would have extra-clamped a legal 604 C / 3.6 t/h pass.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "hearth-bed thermocouple, 4 kHz, 26 us jitter",
                    "offgas IR pyrometer, 1 kHz, 32 us jitter",
                    "grate encoder (context)",
                    "header DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_trip_C", 655.0),
                        ("observed_bed_C", 604.0),
                        ("offgas_C", 418.0),
                        ("feed_cap_t_h", 5.0),
                        ("proposed_feed_t_h", 3.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Roaster R-6 in pass; 3.6 t/h cake armed.",
                    "2. Bed 604 C under 655 trip; feed 3.6 under 5.0 t/h grate.",
                    "3. Grate encoder precursor at 0.880 ms.",
                    "4. Race window [4.900, 5.200] ms.",
                    "5. tc.bed.C 604 C at 4.980 ms (winner).",
                    "6. ir.offgas.C 418 C at 5.160 ms (loser by 180 us).",
                    "7. Gate at 5.360 ms: ACCEPT 3.6 t/h; executed identical to proposed.",
                    "8. Bed stays 605 C < 655; feed 3.61 t/h < 5.0.",
                    "9. Offgas remaining a duct glint did not require an extra clamp.",
                    "10. Delayed (survey_s=240): 4 min Se titer on the calcine header.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_se_feed"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 604.0),
                        ("bed_trip_C", 655.0),
                        ("offgas_C", 418.0),
                        ("feed_cap_t_h", 5.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 3.6 t/h feed: bed 604 C is under the "
                "655 C trip and 3.6 t/h is under 5.0 t/h grate.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 604 C won by 180 us and is under the 655 C trip. Offgas IR 418 C is a "
                "duct glint, not a thermal miss. ACCEPT the filed 3.6 t/h feed. Executed "
                "identical to proposed. An extra clamp is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("trip", 655.0),
                                    ("observed", 604.0),
                                    ("executed_feed_t_h", 3.6),
                                ]
                            ),
                        ),
                        (
                            "offgas_C",
                            OrderedDict([("look", 500.0), ("observed", 418.0)]),
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
            ("name", "hold_se_feed"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 3.6 t/h feed. Bed 604 C < 655 trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 3.6 t/h cake feed. Bed stayed 605 C under 655. "
                "Offgas remaining a duct glint was the losing channel and did not justify an "
                "extra clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held; 3.6 t/h"),
                        ("bed", "605 C < 655"),
                        ("offgas", "418 C glint unused as thermal miss"),
                        ("calcine", "pass continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Offgas IR 418 C losing a 180 us race did not predict a thermal miss; reversing 180 us would have extra-clamped a legal 604 C hearth.",
                    "Delayed (survey_s=240): 4 min Se titer on the calcine header; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bed.C (4.980 ms, 604 C)"),
                        ("loser", "ir.offgas.C (5.160 ms, 418 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Offgas-first by < 180 us inside the 300 us window would have extra-clamped "
                            "a legal hearth. Bed-TC-first confirms the filed feed.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5360),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (5.360 ms, tick 4). The 4 min Se titer "
                "is delayed surprise bound to survey_s=240, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        22,
        84,
        28,
        52,
        routing(
            "thalamic-relay.se-tc",
            "spikenaut.policy.feed-accept",
            [
                ("relay_bed_C", "policy_feed_accept", 0.69),
                ("relay_offgas_IR", "policy_extra_clamp", 0.21),
            ],
            "octopamine",
            0.05,
            "bed_confirm_stdp; octopamine tags the feed_accept bind at the bed-TC win",
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
            ("decision_window_ms", 0.30),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("feed_accept", 45, 0.50, 220.0, 3),
                    pop("extra_clamp", 40, 0.85, 80.0, 1),
                    pop("ir_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r79-415"),
            (
                "title",
                "Selenous-Stank SS-4 / Roaster R-6: bed 604 C beats offgas IR 418 C by 180 us; "
                "ACCEPT already-legal 3.6 t/h selenium-cake feed",
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
                    "Clean ACCEPT of an already-legal selenium-cake feed. "
                    "total 1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08. Tick 6 binds survey_s=240.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "selenium-roaster",
                    [
                        "accept",
                        "designed",
                        "bed-vs-offgas",
                        "feed-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging offgas IR losing a 180 us race does not require a "
                    "wait when bed temperature is already under the thermal trip.",
                    5,
                ),
            ),
        ]
    )

