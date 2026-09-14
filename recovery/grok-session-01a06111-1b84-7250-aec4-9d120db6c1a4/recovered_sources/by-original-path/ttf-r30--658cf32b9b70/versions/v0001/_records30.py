def record_166():
    ticks = [
        tick(1880, -0.02, 0.01, -0.03, -0.01, 0.01),
        tick(5180, -0.04, 0.01, -0.04, -0.02, 0.01),
        tick(5410, -0.03, 0.01, -0.04, -0.01, 0.01),
        tick(5680, -0.06, 0.02, -0.07, -0.03, 0.02),
        tick(6120, -0.02, 0.01, -0.02, -0.01, 0.01),
        tick(900000000, -0.01, 0.00, -0.02, 0.00, 0.00),
    ]
    spikes = [
        spike("enc.yaw.ctx", 1.120, 0.42),
        spike("enc.yaw.err", 2.240, 0.58),
        spike("hyd.brake.bar", 3.410, 0.50),
        spike("enc.yaw.err", 5.180, 1.32),
        spike("hyd.brake.bar", 5.410, 1.14),
        spike("ctrl.gate", 5.680, 0.98),
        spike("enc.yaw.err", 7.200, 0.82),
        spike("hyd.brake.bar", 9.550, 0.64),
        spike("ctrl.gate", 14.100, 0.86),
        spike("enc.yaw.ctx", 18.400, 0.41),
        spike("enc.yaw.err", 24.200, 0.55),
        spike("hyd.brake.bar", 31.800, 0.38),
    ]
    excerpt = independent_excerpt(30166, 84, 36000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Yaw-Y7 on Foehn-Nacelle FN-3 holds a 0.54 deg yaw-error against the published "
                "0.80 deg firmware-4.2 floor while the turbine still sends 2.4 MW. Brake "
                "hydraulics sit at 168 bar under a 210 bar cap. Encoder-first should ACCEPT the "
                "already-legal hold; a weak supervisor binds the retired 0.40 deg firmware-3.1 "
                "nameplate still riveted on the cabinet.",
            ),
            ("domain", "wind-nacelle-yaw"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep 2.4 MW generation with yaw-error <= 0.80 deg (firmware 4.2 plaque) and "
                "brake pressure <= 210 bar; do not feather a legal yaw.",
            ),
            ("t0_us", 1756852800000166),
            ("gate_latency_us", 500),
            ("race_window_us", 400),
            ("race_window_rel_ms", [5.10, 5.50]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "enc.yaw.err 0.54 deg vs 0.80 deg floor",
                                "hyd.brake.bar 168 bar under 210 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Yaw-first should ACCEPT 2.4 MW (0.54 < 0.80). Brake-first would only "
                            "confirm the same legal hold. The error is the floor the supervisor "
                            "binds, not the race.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one yaw-encoder demodulation slot versus the yaw-brake "
                            "pressure publisher on this 2.5 kHz nacelle bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 70 us (enc 32 + hyd 38): 3.3x over "
                            "a 2.0x trust floor. Order is correctly yaw-first. The error is the "
                            "superseded 0.40 deg nameplate, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "yaw-azimuth encoder, 2.5 kHz, 32 us jitter, axis yaw_err",
                    "yaw-brake hydraulic PT, 1 kHz, 38 us jitter",
                    "generator MW transducer (context)",
                    "blade-pitch encoder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("yaw_floor_deg", 0.80),
                        ("observed_yaw_err_deg", 0.54),
                        ("stale_floor_deg", 0.40),
                        ("stale_floor_class", "firmware-3.1 retired nameplate"),
                        ("proposed_gen_mw", 2.4),
                        ("brake_bar", 168.0),
                        ("brake_cap_bar", 210.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Yaw-Y7 indexed on FN-3; yaw-error 0.54 deg; 2.4 MW armed.",
                    "2. Published firmware-4.2 floor 0.80 deg; firmware-3.1 0.40 deg is a retired plaque.",
                    "3. Encoder precursor at 1.120 ms.",
                    "4. Race window [5.100, 5.500] ms.",
                    "5. enc.yaw.err 0.54 deg at 5.180 ms (winner).",
                    "6. hyd.brake.bar 168 bar at 5.410 ms (loser by 230 us).",
                    "7. Gate at 5.680 ms: wrong REJECT feathers and zeros MW on a stale 0.40 deg floor.",
                    "8. Nacelle idle; 0.54 deg never went over 0.80 deg.",
                    "9. 15 min generation window missed (missed_window_s=900).",
                    "10. QA: correct gate was ACCEPT; leave 2.4 MW; bind the published 0.80 deg floor.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_gen_2p4mw"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("gen_mw", 2.4),
                        ("yaw_hold", True),
                        ("feather", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("yaw_err_deg", 0.54),
                        ("yaw_floor_deg", 0.80),
                        ("stale_floor_deg", 0.40),
                        ("stale_floor_class", "firmware-3.1 retired nameplate"),
                        ("brake_bar", 168.0),
                        ("brake_cap_bar", 210.0),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 70),
                        ("t_gate_us", 5680),
                        ("missed_window_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.4 MW because yaw-error 0.54 deg is 0.26 deg under the "
                "published 0.80 deg firmware-4.2 floor and brake 168 bar is residual, not a trip.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Yaw-error 0.54 deg is over the 0.40 deg floor still printed on the firmware-3.1 "
                "nameplate (true vs that undocumented floor). REJECT: feather and hold 0 MW until "
                "yaw recovers below 0.40 deg so the nacelle does not walk the yaw bearing.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "yaw_err_deg",
                            OrderedDict(
                                [
                                    ("published_floor", 0.80),
                                    ("observed", 0.54),
                                    ("wrong_floor_applied", 0.40),
                                    ("executed_gen_mw", 0.0),
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
            ("name", "feather_wrong_floor"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("gen_mw", 0.0),
                        ("yaw_hold", True),
                        ("feather", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): gen 2.4 -> 0 MW, feather true. Routing relay_enc_yaw -> "
                "policy_feather_reject; no positive weight to policy_yaw_go. Published 0.80 deg "
                "floor was never violated.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT feathered Yaw-Y7 to 0 MW while yaw-error stayed 0.54 deg under the "
                "0.80 deg firmware-4.2 floor. 15 min generation window missed. Correct gate was "
                "ACCEPT of the already-legal 2.4 MW command.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("turbine", "feathered; 2.4 MW abandoned"),
                        ("yaw", "still 0.54 deg, under 0.80 deg published floor"),
                        ("window", "15 min generation missed"),
                        ("bearing", "no walk; stale-floor false positive"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 0.40 deg firmware-3.1 nameplate is a retired plaque; it is not a published firmware-4.2 constraint and never appears on the SCADA floor register.",
                    "Delayed (missed_window_s=900): sister nacelle Yaw-Y8 ran the same 2.4 MW window after QA rebound the 0.80 deg floor; Y7's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: yaw-error 0.54 deg < published 0.80 deg firmware-4.2 floor; leave 2.4 MW.",
                        ),
                        ("correct_floor_deg", 0.80),
                        ("wrong_floor_deg", 0.40),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("gen_mw", 0.0), ("feather", True)]),
                        ),
                        (
                            "cost",
                            "15 min missed generation (task/efficiency); yaw never over cap (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "enc.yaw.err (5.180 ms, 0.54 deg)"),
                        ("loser", "hyd.brake.bar (5.410 ms, 168 bar)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "Brake-first by < 230 us would still show 0.54 deg < 0.80 deg. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the encoder "
                            "win on a superseded firmware-3.1 plaque.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5680),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (5.680 ms, tick 4). The 15 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 900),
        ]
    )
    ras = raster_core(
        36,
        84,
        22,
        66,
        routing(
            "thalamic-relay.yaw-err",
            "spikenaut.policy.feather-reject",
            [
                ("relay_enc_yaw", "policy_feather_reject", 0.71),
                ("relay_hyd_brake", "policy_feather_reject", 0.22),
            ],
            "acetylcholine",
            0.08,
            "stale_floor_stdp; ACh tags the (wrong) feather_reject bind at the encoder win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("missed_window_s", 900),
                ("delayed_surprise_s", 900),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("feather_reject", 48, 0.50, 250.0, 5),
                    pop("yaw_go", 48, 0.80, 12.0, 0),
                    pop("brake_ctx", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r30-166"),
            (
                "title",
                "WRONG-REJECT at Foehn-Nacelle FN-3 / Yaw-Y7: yaw-error 0.54 deg is legal vs "
                "published 0.80 deg firmware-4.2 floor; supervisor bound a retired 0.40 deg "
                "firmware-3.1 nameplate",
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
                    "Wrong-reject. Sidecar arithmetic 0.54 < 0.80 is true; clamp bound to a "
                    "superseded 0.40 deg plaque. total -0.36 = -0.18 + 0.06 + -0.22 + -0.08 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "wind-nacelle-yaw",
                    [
                        "reject",
                        "wrong-gate",
                        "wrong-reject",
                        "stale-firmware-floor",
                        "superseded-plaque",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct yaw_err<floor read can still be a wrong gate "
                    "when routing.table[0].to is policy_feather_reject and executed gen_mw is zeroed.",
                    1,
                    supervisor_error_type="wrong-reject",
                ),
            ),
        ]
    )


def record_167():
    excerpt, extra = lif_167_excerpt()
    ticks = [
        tick(2410, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6120, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(6340, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6880, 0.10, -0.06, -0.04, 0.02, -0.01),
        tick(22400, 0.04, -0.46, -0.03, -0.01, -0.01),
        tick(780000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Pan-P11 at Treacle-Kettle TK-6 is boiling 78.4 Brix massecuite under a 76.0 "
                "Brix strike cap while steam still sits at 1.80 bar, under a 2.40 bar header "
                "overspeed. Refract-first drops steam to 1.10 bar; steam-first would keep 1.80 "
                "bar because the header is still legal. A crystal bridge already spanning the "
                "agitator does not appear on Brix or steam until the AE seize.",
            ),
            ("domain", "sugar-vacuum-pan"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep Pan-P11 Brix <= 76.0 and finish the strike without dumping massecuite "
                "onto the crystallizer floor.",
            ),
            ("t0_us", 1756852800000167),
            ("gate_latency_us", 760),
            ("race_window_us", 400),
            ("race_window_rel_ms", [6.00, 6.40]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "refract.brix 78.4 vs 76.0 cap",
                                "steam.pt.bar 1.80 under 2.40 header",
                            ],
                        ),
                        (
                            "semantics",
                            "Refract-first latches steam clamp 1.80 -> 1.10 bar; steam-first "
                            "keeps 1.80 bar on a 'still under header' model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one inline-refractometer slot versus the steam-header PT "
                            "publisher on this vacuum-pan skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 68 us (refract 30 + steam 38): 3.2x "
                            "over a 2.0x trust floor. Reversing order by < 220 us inside the 400 us "
                            "window would have kept 1.80 bar; predicted next-sample 77.1 Brix > 76.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "inline refractometer Brix, 2 kHz, 30 us jitter",
                    "steam-header pressure transmitter, 1 kHz, 38 us jitter",
                    "agitator AE puck on the pan wall, 40 kHz (context)",
                    "vacuum ring manometer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("brix_cap", 76.0),
                        ("observed_brix", 78.4),
                        ("steam_bar", 1.80),
                        ("steam_header_cap_bar", 2.40),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Pan-P11 indexed; steam 1.80 bar; Brix 78.4.",
                    "2. Header 1.80 bar under 2.40 cap; strike armed.",
                    "3. Agitator precursor at 1.180 ms.",
                    "4. Race window [6.000, 6.400] ms.",
                    "5. refract.brix 78.4 at 6.120 ms (winner).",
                    "6. steam.pt.bar 1.80 at 6.340 ms (loser by 220 us).",
                    "7. Gate at 6.880 ms: MODIFY clamp steam 1.80 -> 1.10 bar.",
                    "8. After clamp Brix 75.2 < 76.0; header still 1.80 bar available.",
                    "9. At 22.400 ms a crystal bridge seizes the agitator; 0.3 t dumps to the floor.",
                    "10. 13 min pan dump + agitator pull (abort_s=780); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_pan_steam"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_bar", 1.80),
                        ("brix", 78.4),
                        ("agitator_rpm", 12.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("brix", 78.4),
                        ("brix_cap", 76.0),
                        ("predicted_unclamped_next_brix", 77.1),
                        ("steam_bar", 1.80),
                        ("steam_header_cap_bar", 2.40),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 68),
                        ("abort_s", 780),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.80 bar steam because the header is under 2.40, treating "
                "the 78.4 Brix as a still-wet massecuite rather than a strike overshoot.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Brix 78.4 won by 220 us, so the pan is over-striking, not still a steam-header "
                "story. Holding 1.80 bar predicts next-sample 77.1 > 76.0 cap. MODIFY: steam "
                "1.80 -> 1.10 bar. Observed after clamp 75.2 < 76.0. A full REJECT is not "
                "indicated: a clean strike accepts 1.10 bar.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "brix",
                            OrderedDict(
                                [
                                    ("cap", 76.0),
                                    ("observed", 78.4),
                                    ("predicted_unclamped_next", 77.1),
                                    ("clamped_steam_bar", 1.10),
                                    ("observed_after_clamp", 75.2),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 68),
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
            ("name", "clamped_pan_steam"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_bar", 1.10),
                        ("brix", 75.2),
                        ("agitator_rpm", 12.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: steam 1.80 -> 1.10 bar. Process-correct vs the 76.0 Brix cap. Crystal "
                "bridge still seizes at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held Brix at 75.2. At 22.400 ms a crystal bridge already "
                "spanning the agitator seized and dumped 0.3 t onto the crystallizer floor. Clamp "
                "reduced dump energy; it did not prevent the seize. Partnered negative: process "
                "heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("brix", "clamp executed; peak 75.2 < 76.0 cap"),
                        ("crystal_bridge", "seized at 22.400 ms; 0.3 t floor dump"),
                        ("repair", "13 min pan dump + agitator pull (abort_s=780)"),
                        ("mission", "TK-6 strike incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither Brix nor steam PT predicted the seated crystal bridge; ae.crystal.bridge is a new channel at 22.400 ms, 15.520 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=780): 13 min pan dump + agitator pull. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "13 min pan dump + agitator pull after the crystal seize. Safety head -0.66 "
                "prices the dump; task_progress stays +0.32 because the steam clamp completed "
                "under the 76.0 Brix cap. World loss is named here, not subtracted from process "
                "heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "refract.brix (6.120 ms, 78.4)"),
                        ("loser", "steam.pt.bar (6.340 ms, 1.80 bar)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Steam-first by < 220 us inside the 400 us window would have kept "
                            "1.80 bar; predicted next-sample 77.1 would have exceeded the 76.0 "
                            "cap even without the crystal bridge. The MODIFY is still the correct "
                            "process. The seize is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms crystal-bridge seize (tick t_us=22400), inside "
                "the 42 ms raster. The correct MODIFY at 6.880 ms is in the same excerpt. Do not "
                "put inflection on the abort_s=780 dump tick.",
            ),
            ("delayed_surprise_s", 780),
        ]
    )
    spikes = [
        spike("enc.agit.ctx", 1.180, 0.40),
        spike("refract.brix", 2.410, 0.59),
        spike("steam.pt.bar", 3.880, 0.51),
        spike("refract.brix", 6.120, 1.30),
        spike("steam.pt.bar", 6.340, 1.12),
        spike("ctrl.gate", 6.880, 0.97),
        spike("refract.brix", 8.400, 0.80),
        spike("steam.pt.bar", 11.200, 0.63),
        spike("ctrl.gate", 14.600, 0.84),
        spike("ae.crystal.bridge", 22.400, 1.46),
        spike("ae.crystal.bridge", 24.200, 0.92),
        spike("enc.agit.ctx", 31.100, 0.40),
        spike("refract.brix", 38.400, 0.52),
    ]
    ras = raster_core(
        42,
        72,
        29,
        88,
        routing(
            "thalamic-relay.pan-brix",
            "spikenaut.policy.steam-clamp",
            [
                ("relay_refract_brix", "policy_steam_clamp", 0.69),
                ("relay_steam_pt", "policy_steam_hold", 0.27),
                ("relay_ae_crystal", "policy_steam_clamp", -0.40),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at refract win (6.120 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.400 ms crystal seize",
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
                    pop("steam_clamp", 50, 0.50, 200.0, 4),
                    pop("steam_hold", 40, 0.80, 50.0, 1),
                    pop("crystal_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r30-167"),
            (
                "title",
                "Treacle-Kettle TK-6 / Pan-P11: Brix beats steam-header by 220 us; correct "
                "MODIFY still eats an in-window crystal-bridge seize (partnered negative total -0.50)",
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
                    "42 ms raster. total -0.50 = 0.32 + -0.66 + -0.16 + 0.04 + -0.04. Named pan "
                    "dump (abort_s=780) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "sugar-vacuum-pan",
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
                    "13 min pan dump.",
                    2,
                ),
            ),
        ]
    )


def record_168():
    ticks = [
        tick(2810, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(7040, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7220, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7920, 0.04, 0.14, 0.04, 0.04, 0.02),
        tick(8280, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(540000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("tc.mold.ctx", 1.380, 0.42),
        spike("eddy.level.mm", 2.860, 0.60),
        spike("ir.strand.C", 4.510, 0.48),
        spike("eddy.level.mm", 7.040, 1.33),
        spike("ir.strand.C", 7.220, 1.10),
        spike("ctrl.gate", 7.920, 1.01),
        spike("eddy.level.mm", 10.400, 0.76),
        spike("tc.mold.ctx", 15.200, 0.44),
        spike("ir.strand.C", 19.800, 0.57),
        spike("ctrl.gate", 25.100, 0.80),
        spike("eddy.level.mm", 32.400, 0.52),
        spike("ir.strand.C", 39.200, 0.45),
        spike("tc.mold.ctx", 45.800, 0.36),
    ]
    excerpt = independent_excerpt(30168, 120, 48000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Mold-M4 on the Bloom-Weir BW-HIL pad shows eddy mold-level 48 mm against a 70 mm "
                "breakout floor while a strand IR camera, lit by the pad lamp, still reads 890 C "
                "under a 920 C freeze-look. Eddy-first latches REJECT hold; IR-first would raise "
                "caster speed 0.90 -> 1.20 m/min on an under-read strand.",
            ),
            ("domain", "steel-caster-mold"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not raise caster speed unless mold-level >= 70 mm; keep speed 0.00 m/min "
                "until the injected eddy level recovers.",
            ),
            ("t0_us", 1756852800000168),
            ("gate_latency_us", 880),
            ("race_window_us", 300),
            ("race_window_rel_ms", [6.95, 7.25]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "eddy.level.mm 48 mm vs 70 mm floor",
                                "ir.strand.C 890 C under 920",
                            ],
                        ),
                        (
                            "semantics",
                            "Eddy-first latches REJECT hold 0.00 m/min; IR-first would commit a "
                            "0.30 m/min raise on an apparent 890 C under-read.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one eddy-current mold-level sample versus IR integration on "
                            "this caster HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (eddy 26 + IR 32): 3.1x over a "
                            "2.0x trust floor. Pad injects the IR lamp 110-150 us before the eddy "
                            "demodulator (geometric lag, not a sensor fault); the 890 C packet is "
                            "still the loser in this 300 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "eddy-current mold-level, 5 kHz burst, 26 us jitter",
                    "strand IR pyrometer, 2 kHz, 32 us jitter",
                    "mold-copper thermocouple (context)",
                    "caster-speed encoder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("level_floor_mm", 70.0),
                        ("observed_level_mm", 48.0),
                        ("strand_cap_C", 920.0),
                        ("observed_strand_C", 890.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Mold-M4 on BW-HIL; eddy level 48 mm; speed armed 0.90 m/min.",
                    "2. Breakout floor 70 mm; IR 890 C under 920 C freeze-look.",
                    "3. Mold-TC precursor at 1.380 ms.",
                    "4. Race window [6.950, 7.250] ms.",
                    "5. eddy.level.mm 48 mm at 7.040 ms (winner).",
                    "6. ir.strand.C 890 C at 7.220 ms (loser by 180 us).",
                    "7. Gate at 7.920 ms: REJECT hold speed 0.00 m/min.",
                    "8. Level stays 48 mm; no strand raise.",
                    "9. HIL pad confirms eddy-authoritative under lamp-present mode.",
                    "10. Delayed (abort_s=540): 9 min re-prime of the tundish before the next heat.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "raise_caster_1p20"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_min", 1.20),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("level_mm", 48.0),
                        ("level_floor_mm", 70.0),
                        ("strand_C", 890.0),
                        ("strand_cap_C", 920.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.20 m/min because strand IR 890 C is under the 920 C "
                "freeze-look, treating the 48 mm eddy as a still-filling meniscus.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Eddy level 48 mm won by 180 us, so the meniscus is under the 70 mm breakout "
                "floor. IR 890 C is a pad-lamp under-read, not a freeze permit. REJECT: hold "
                "speed 0.00 m/min. Raising to 1.20 m/min on a 48 mm level is a breakout.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "level_mm",
                            OrderedDict(
                                [
                                    ("floor", 70.0),
                                    ("observed", 48.0),
                                    ("executed_speed_m_min", 0.0),
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
            ("name", "hold_caster_breakout"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_min", 0.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: speed 1.20 -> 0.00 m/min. Eddy-authoritative vs the 70 mm floor. IR "
                "under-read does not clear a low meniscus.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Mold-M4 at 0.00 m/min while eddy level stayed 48 mm under "
                "the 70 mm floor. Strand did not freeze; breakout avoided. 9 min tundish re-prime "
                "is delayed surprise bound to abort_s=540.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("caster", "held 0.00 m/min; 1.20 m/min abandoned"),
                        ("level", "48 mm, under 70 mm floor"),
                        ("strand", "no freeze; IR was pad-lamp"),
                        ("heat", "9 min re-prime before next heat"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 890 C IR face was not a calibration fault: a HIL pad lamp can lower apparent strand temperature while eddy level stays under floor.",
                    "Delayed (abort_s=540): 9 min tundish re-prime. Sister strand Mold-M5 confirmed eddy-authoritative under lamp-present mode.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "eddy.level.mm (7.040 ms, 48 mm)"),
                        ("loser", "ir.strand.C (7.220 ms, 890 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 180 us inside the 300 us window would have committed "
                            "a 0.30 m/min raise with level 48 < 70 floor. Order, not amplitude, "
                            "selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7920),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (7.920 ms, tick 4) as the hold "
                "lands. The 9 min re-prime is delayed surprise bound to abort_s=540.",
            ),
            ("delayed_surprise_s", 540),
        ]
    )
    ras = raster_core(
        48,
        120,
        18,
        104,
        routing(
            "thalamic-relay.mold-level",
            "spikenaut.policy.caster-hold",
            [
                ("relay_eddy_level", "policy_caster_hold", 0.70),
                ("relay_ir_strand", "policy_ir_raise", 0.24),
            ],
            "dopamine",
            0.15,
            "breakout_hold_stdp; DA tags the caster_hold bind at the eddy-level win",
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
            ("decision_window_ms", 0.30),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("caster_hold", 60, 0.48, 280.0, 5),
                    pop("speed_raise", 40, 0.85, 40.0, 0),
                    pop("breakout_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r30-168"),
            (
                "title",
                "Bloom-Weir BW-HIL / Mold-M4: eddy 48 mm beats IR 890 C by 180 us; correct "
                "REJECT holds the caster speed",
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
                    "Correct REJECT. Eddy level under floor beats IR under-read. "
                    "total 0.78 = 0.10 + 0.40 + 0.12 + 0.10 + 0.06. Tick 6 binds abort_s=540.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "steel-caster-mold",
                    [
                        "reject",
                        "hil",
                        "breakout-floor",
                        "ir-underread",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a HIL lamp under-read losing a 180 us race does not clear a "
                    "mold-level under-floor. Hold is distillable from eddy vs cap.",
                    3,
                ),
            ),
        ]
    )


def record_169():
    ticks = [
        tick(3200, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(8120, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(8310, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(8580, 0.14, 0.10, 0.05, 0.04, 0.02),
        tick(8980, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(480000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.hp.ctx", 1.080, 0.43),
        spike("cond.permeate.uS", 3.180, 0.58),
        spike("pt.feed.bar", 5.020, 0.50),
        spike("cond.permeate.uS", 8.120, 1.26),
        spike("pt.feed.bar", 8.310, 1.08),
        spike("ctrl.gate", 8.580, 0.97),
        spike("cond.permeate.uS", 11.400, 0.76),
        spike("pt.feed.bar", 14.880, 0.60),
        spike("ctrl.gate", 18.200, 0.83),
        spike("cond.permeate.uS", 22.050, 0.55),
        spike("enc.hp.ctx", 25.400, 0.40),
        spike("pt.feed.bar", 29.200, 0.46),
    ]
    excerpt = independent_excerpt(30169, 56, 30000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("feed_bar", 12.4),
            ("permeate_uS", 180.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Train-T2 on Spindrift-Rack SR-5 holds 180 uS/cm permeate under a 400 uS/cm "
                "salt-passage cap with a 12.4 bar feed already filed under the 16.0 bar element "
                "cap. Feed-PT is 12.4 bar, still legal. Conductivity-first ACCEPTS the filed "
                "feed; PT-first would have extra-clamped a legal two-stage RO.",
            ),
            ("domain", "desal-RO-train"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold the 12.4 bar feed while permeate conductivity stays <= 400 uS/cm and feed "
                "stays <= 16.0 bar; do not extra-clamp a legal two-stage RO.",
            ),
            ("t0_us", 1756852800000169),
            ("gate_latency_us", 460),
            ("race_window_us", 400),
            ("race_window_rel_ms", [8.00, 8.40]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "cond.permeate.uS 180 vs 400 cap",
                                "pt.feed.bar 12.4 under 16.0 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Conductivity-first latches ACCEPT of the 12.4 bar feed; PT-first "
                            "would extra-clamp a legal element.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one conductivity-cell integrator versus feed-PT on this "
                            "two-stage RO skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 190 us vs combined jitter 62 us (cond 28 + PT 34): 3.1x over a "
                            "2.0x trust floor. Reversing order by < 190 us would have extra-clamped "
                            "a legal 12.4 bar feed.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "permeate conductivity cell, 2 kHz, 28 us jitter",
                    "feed-header pressure transmitter, 1 kHz, 34 us jitter",
                    "high-pressure pump encoder (context)",
                    "concentrate flow orifice (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("permeate_cap_uS", 400.0),
                        ("observed_permeate_uS", 180.0),
                        ("feed_cap_bar", 16.0),
                        ("observed_feed_bar", 12.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Train-T2 latched on SR-5; two-stage RO in production.",
                    "2. Permeate 180 uS/cm; feed 12.4 bar under 16.0 cap.",
                    "3. HP-pump precursor at 1.080 ms.",
                    "4. Race window [8.000, 8.400] ms.",
                    "5. cond.permeate.uS 180 at 8.120 ms (winner).",
                    "6. pt.feed.bar 12.4 at 8.310 ms (loser by 190 us).",
                    "7. Gate at 8.580 ms: ACCEPT 12.4 bar feed.",
                    "8. Permeate 180 uS/cm; feed 12.4 bar under 16.0 cap.",
                    "9. Production continues; train remains latched.",
                    "10. Delayed (survey_s=480): sister train T3 conductivity-authoritative under PT-present mode.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_feed_12p4"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("permeate_uS", 180.0),
                        ("permeate_cap_uS", 400.0),
                        ("feed_bar", 12.4),
                        ("feed_cap_bar", 16.0),
                        ("race_margin_us", 190),
                        ("combined_jitter_us", 62),
                        ("survey_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Conductivity 180 uS/cm is under the 400 uS/cm cap and feed 12.4 bar is under "
                "the 16.0 bar cap; 12.4 bar hold is already legal.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Permeate 180 uS/cm won by 190 us; commanded 12.4 bar is 3.6 bar under the 16.0 "
                "bar cap; conductivity keeps the 400 uS/cm floor. ACCEPT the hold. A PT-led "
                "extra-clamp would abort a legal train.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "permeate_uS",
                            OrderedDict(
                                [
                                    ("cap", 400.0),
                                    ("observed", 180.0),
                                ]
                            ),
                        ),
                        (
                            "feed_bar",
                            OrderedDict(
                                [
                                    ("cap", 16.0),
                                    ("commanded", 12.4),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 190),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 3.06),
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
            ("name", "hold_feed_12p4"),
            ("parameters", OrderedDict(params.items())),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed_action; 12.4 bar feed held for the "
                "two-stage RO.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Train-T2 completed the hold with permeate 180 uS/cm and feed 12.4 bar; elements "
                "unharmed. Conductivity-authoritative under PT-present mode confirmed.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("permeate", "180 uS/cm held; under 400 cap"),
                        ("feed", "12.4 bar; under 16.0 cap"),
                        ("train", "latched; production continues"),
                        ("near_miss_log", "none"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 12.4 bar feed-PT was not a calibration fault: a concentrate-side pulse can raise apparent header while conductivity stays legal.",
                    "Delayed (survey_s=480): sister train T3 logged the same conductivity-vs-PT disagreement; rack policy flipped conductivity-authoritative before the next CIP.",
                ],
            ),
            ("survey_s", 480),
            ("delayed_surprise_s", 480),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "cond.permeate.uS (8.120 ms, 180 uS/cm)"),
                        ("loser", "pt.feed.bar (8.310 ms, 12.4 bar)"),
                        ("margin_us", 190),
                        (
                            "counterfactual_if_reversed",
                            "PT-first by < 190 us inside the 400 us window would have extra-clamped "
                            "a legal 12.4 bar feed on a 180 uS/cm permeate that is still under the "
                            "400 uS/cm cap.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 8580),
            (
                "reward_inflection_note",
                "Safety and efficiency both step up at the ACCEPT gate (8.580 ms, tick 4) as "
                "the hold locks in over a false extra-clamp.",
            ),
        ]
    )
    ras = raster_core(
        30,
        56,
        34,
        57,
        routing(
            "thalamic-relay.ro-cond",
            "spikenaut.policy.ro-accept",
            [
                ("relay_cond_perm", "policy_ro_accept", 0.66),
                ("relay_pt_feed", "policy_extra_clamp", 0.23),
            ],
            "serotonin",
            0.12,
            "salt_passage_stdp; 5-HT tags the ro_accept bind at the conductivity win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 480),
                ("delayed_surprise_s", 480),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("ro_accept", 40, 0.50, 250.0, 4),
                    pop("extra_clamp", 32, 0.85, 80.0, 1),
                    pop("salt_veto", 22, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r30-169"),
            (
                "title",
                "Spindrift-Rack SR-5 / Train-T2: permeate 180 uS/cm beats feed-PT 12.4 bar by "
                "190 us; ACCEPT already-legal 12.4 bar two-stage RO",
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
                    "Clean ACCEPT of an already-legal RO feed. total 1.10 = 0.42 + 0.30 + 0.18 + "
                    "0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "desal-RO-train",
                    [
                        "accept",
                        "simulated",
                        "cond-vs-pt",
                        "already-legal-feed",
                        "two-stage-ro",
                    ],
                    "Teaches a fusion head that a feed-PT pulse can lose to a legal permeate "
                    "conductivity without a further pressure clamp.",
                    4,
                ),
            ),
        ]
    )


def record_170():
    ticks = [
        tick(1800, 0.05, 0.04, 0.03, 0.01, 0.01),
        tick(4560, 0.09, 0.06, 0.04, 0.03, 0.02),
        tick(4740, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5180, 0.14, 0.10, 0.06, 0.04, 0.02),
        tick(5520, 0.07, 0.05, 0.03, 0.01, 0.01),
        tick(360000000, 0.03, 0.03, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.meal.ctx", 0.920, 0.41),
        spike("o2.calciner.pct", 2.080, 0.56),
        spike("ir.meal.C", 3.140, 0.47),
        spike("o2.calciner.pct", 4.560, 1.25),
        spike("ir.meal.C", 4.740, 1.07),
        spike("ctrl.gate", 5.180, 0.98),
        spike("o2.calciner.pct", 7.400, 0.75),
        spike("ir.meal.C", 9.880, 0.54),
        spike("ctrl.gate", 13.200, 0.81),
        spike("enc.meal.ctx", 16.600, 0.42),
        spike("o2.calciner.pct", 20.400, 0.50),
        spike("ir.meal.C", 24.800, 0.36),
    ]
    excerpt = independent_excerpt(30170, 40, 26000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("meal_t_h", 82.0),
            ("o2_pct", 3.8),
            ("fuel_gj_h", 210.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Calciner-C3 at Clinker-Spire CS-8 is feeding 82 t/h of raw meal under a 95 t/h "
                "riser cap while gas O2 sits at 3.8 percent, still over a 2.5 percent reducing "
                "floor. O2-first ACCEPTS the filed 82 t/h; IR-first would treat 3.8 percent as a "
                "rich cloud and cut meal.",
            ),
            ("domain", "cement-precalciner"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 82 t/h meal while O2 stays >= 2.5 percent and meal stays <= 95 t/h; do not "
                "cut a legal calciner on a false-rich IR cloud.",
            ),
            ("t0_us", 1756852800000170),
            ("gate_latency_us", 620),
            ("race_window_us", 400),
            ("race_window_rel_ms", [4.40, 4.80]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "o2.calciner.pct 3.8 vs 2.5 floor",
                                "ir.meal.C 812 C under 880 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "O2-first latches ACCEPT of the 82 t/h meal; IR-first would cut meal "
                            "on an 812 C cloud still under 880 C.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one zirconia O2 slot versus meal IR on this precalciner "
                            "riser bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (O2 28 + IR 32): 3.0x over a "
                            "2.0x trust floor. Reversing order by < 180 us would have cut a legal "
                            "82 t/h meal.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "zirconia O2 probe, 2 kHz, 28 us jitter",
                    "meal IR pyrometer, 1 kHz, 32 us jitter",
                    "meal-rate encoder (context)",
                    "tertiary-air PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("meal_cap_t_h", 95.0),
                        ("observed_meal_t_h", 82.0),
                        ("o2_floor_pct", 2.5),
                        ("observed_o2_pct", 3.8),
                        ("ir_cap_C", 880.0),
                        ("observed_ir_C", 812.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Calciner-C3 indexed on CS-8; meal 82 t/h; O2 3.8 percent.",
                    "2. Riser cap 95 t/h; IR 812 C under 880 C.",
                    "3. Meal-encoder precursor at 0.920 ms.",
                    "4. Race window [4.400, 4.800] ms.",
                    "5. o2.calciner.pct 3.8 at 4.560 ms (winner).",
                    "6. ir.meal.C 812 C at 4.740 ms (loser by 180 us).",
                    "7. Gate at 5.180 ms: ACCEPT 82 t/h meal hold.",
                    "8. O2 3.8 percent; meal 82 t/h under 95 cap.",
                    "9. Calciner continues; kiln remains latched.",
                    "10. Delayed (reseq_s=360): sister calciner C4 O2-authoritative under IR-present mode.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_meal_82"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("meal_t_h", 82.0),
                        ("meal_cap_t_h", 95.0),
                        ("o2_pct", 3.8),
                        ("o2_floor_pct", 2.5),
                        ("ir_C", 812.0),
                        ("ir_cap_C", 880.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("reseq_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "O2 3.8 percent is over the 2.5 percent reducing floor and meal 82 t/h is under "
                "the 95 t/h riser cap; 82 t/h hold is already legal.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "O2 3.8 percent won by 180 us; commanded 82 t/h is 13 t/h under the 95 t/h cap; "
                "IR 812 C keeps the 880 C floor. ACCEPT the hold. An IR-led meal cut would abort "
                "a legal calciner.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "meal_t_h",
                            OrderedDict(
                                [
                                    ("cap", 95.0),
                                    ("commanded", 82.0),
                                ]
                            ),
                        ),
                        (
                            "o2_pct",
                            OrderedDict(
                                [
                                    ("floor", 2.5),
                                    ("observed", 3.8),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 3.00),
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
            ("name", "hold_meal_82"),
            ("parameters", OrderedDict(params.items())),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed_action; 82 t/h meal and 3.8 percent O2 "
                "held for the calciner.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Calciner-C3 completed the hold with meal 82 t/h and O2 3.8 percent; riser "
                "unharmed. O2-authoritative under IR-present mode confirmed.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("meal", "82 t/h held; under 95 cap"),
                        ("o2", "3.8 percent; over 2.5 floor"),
                        ("calciner", "latched; kiln continues"),
                        ("near_miss_log", "none"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 812 C IR cloud was not a calibration fault: a dust curtain can raise apparent meal temperature while zirconia O2 stays legal.",
                    "Delayed (reseq_s=360): sister calciner C4 logged the same O2-vs-IR disagreement; kiln policy flipped O2-authoritative before the next meal rotation.",
                ],
            ),
            ("reseq_s", 360),
            ("delayed_surprise_s", 360),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "o2.calciner.pct (4.560 ms, 3.8 percent)"),
                        ("loser", "ir.meal.C (4.740 ms, 812 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 180 us inside the 400 us window would have cut a legal "
                            "82 t/h meal on an 812 C cloud that is still under the 880 C cap.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5180),
            (
                "reward_inflection_note",
                "Safety and efficiency both step up at the ACCEPT gate (5.180 ms, tick 4) as "
                "the hold locks in over a false meal cut.",
            ),
        ]
    )
    ras = raster_core(
        26,
        40,
        46,
        48,
        routing(
            "thalamic-relay.calciner-o2",
            "spikenaut.policy.meal-go",
            [
                ("relay_o2_calciner", "policy_meal_go", 0.64),
                ("relay_ir_meal", "policy_meal_cut", 0.26),
            ],
            "histamine",
            0.18,
            "reducing_floor_stdp; histamine tags the meal_go bind at the O2 win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("reseq_s", 360),
                ("delayed_surprise_s", 360),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("meal_go", 32, 0.50, 280.0, 4),
                    pop("o2_cut", 32, 0.80, 80.0, 1),
                    pop("riser_ctx", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r30-170"),
            (
                "title",
                "Clinker-Spire CS-8 / Calciner-C3: O2 3.8 percent beats IR 812 C by 180 us; "
                "ACCEPT already-legal 82 t/h meal hold",
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
                    "Clean ACCEPT. O2 3.8 percent > 2.5 floor; meal 82 t/h < 95 cap. total "
                    "1.16 = 0.44 + 0.32 + 0.20 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "cement-precalciner",
                    [
                        "accept",
                        "cement",
                        "o2-vs-ir",
                        "already-legal-meal",
                        "designed",
                    ],
                    "Teaches that an IR dust cloud can lose to a zirconia O2 probe when both "
                    "reads are under cap; reversing 180 us would have cut a legal meal.",
                    5,
                ),
            ),
        ]
    )
