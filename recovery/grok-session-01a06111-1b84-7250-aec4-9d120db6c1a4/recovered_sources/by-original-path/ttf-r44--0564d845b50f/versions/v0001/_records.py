def record_236():
    excerpt, extra = lif_236_excerpt()
    ticks = [
        tick(2520, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(6280, 0.07, -0.04, -0.03, 0.01, -0.01),
        tick(6496, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(7160, 0.08, -0.06, -0.03, 0.02, -0.02),
        tick(22800, 0.06, -0.38, -0.04, -0.02, -0.02),
        tick(900000000, 0.02, -0.05, -0.02, 0.00, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Remelt-Bay RB-7 is already driving Thoria-Kettle TK-3 at 14.2 kA melt current "
                "while the slag-cap thermocouple sits at 1680 C against a 1620 C slag-skin "
                "cap. A cap-first latch clamps the melt; a current-first story would keep "
                "the 14.2 kA cruise. Stored hoop in the slag crust is not yet an observable "
                "of either race channel.",
            ),
            ("domain", "esr-ingot-melt"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the TK-3 electroslag pass, keep slag-skin <= 1620 C, and leave the "
                "mold crust unmarked.",
            ),
            ("t0_us", 1756794621000236),
            ("gate_latency_us", 880),
            ("race_window_us", 500),
            ("race_window_rel_ms", [6.20, 6.70]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.slag.cap 1680 C pulse",
                                "enc.melt.kA 14.2 kA cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Cap-first latches melt 14.2 -> 9.6 kA; current-first keeps "
                            "cruise on a still-cooling slag-skin model.",
                        ),
                        (
                            "window_derivation",
                            "500 us = one 1 kHz slag-cap sample minus melt-encoder group "
                            "delay on this ESR bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 216 us vs combined jitter ~66 us (cap 30 + melt 36): 3.3x over "
                            "a 2.0x trust floor. Reversing order by < 216 us inside the 500 us window "
                            "would have kept 14.2 kA cruise; predicted next-sample 1648 C > 1620 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "slag-cap thermocouple, 1 kHz, 30 us timestamp jitter",
                    "melt-current encoder, 500 Hz, 36 us jitter",
                    "mold-wall AE puck (context until the crust tear)",
                    "flux-hopper PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("slag_skin_cap_C", 1620.0),
                        ("observed_cap_C", 1680.0),
                        ("proposed_melt_kA", 14.2),
                        ("flux_feed_kg_min", 2.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Remelt-Bay RB-7 indexed onto TK-3; melt armed at 14.2 kA.",
                    "2. Cruise 14.2 kA; slag-cap 1680 C against 1620 C slag-skin cap.",
                    "3. Melt precursor at 1.220 ms; cap warm-start 1680 C.",
                    "4. Race window [6.200, 6.700] ms opens on the ESR bus.",
                    "5. tc.slag.cap 1680 C at 6.280 ms (winner).",
                    "6. enc.melt.kA 14.2 kA at 6.496 ms (loser by 216 us).",
                    "7. Gate at 7.160 ms (winner + 880 us): MODIFY clamp 14.2 -> 9.6 kA.",
                    "8. Clamp executes; next-sample cap 1594 C < 1620 cap.",
                    "9. At 22.800 ms stored hoop still tears a 26 mm slag crust; AE burst.",
                    "10. Mold isolate 15 min (abort_s=900); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_melt_current"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("melt_kA", 14.2),
                        ("flux_feed_kg_min", 2.4),
                        ("ingot_t", 18.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("cap_C", 1680.0),
                        ("slag_skin_cap_C", 1620.0),
                        ("predicted_unclamped_next_C", 1648.0),
                        ("melt_kA", 14.2),
                        ("race_margin_us", 216),
                        ("combined_jitter_us", 66),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 14.2 kA cruise: 1680 C looks like a flux-hopper spike, not "
                "skin contact, and TK-3 volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Slag-cap 1680 C won by 216 us, so the mold is loading heat, not "
                "still cooling. Holding 14.2 kA predicts next-sample 1648 C > 1620 cap. "
                "MODIFY: melt 14.2 -> 9.6 kA. Observed after clamp 1594 C < 1620. A full "
                "REJECT is not indicated: a sound ESR pass accepts 9.6 kA.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "slag_skin_C",
                            OrderedDict(
                                [
                                    ("cap", 1620.0),
                                    ("observed", 1680.0),
                                    ("predicted_unclamped_next", 1648.0),
                                    ("clamped_melt_kA", 9.6),
                                    ("observed_after_clamp", 1594.0),
                                ]
                            ),
                        ),
                        (
                            "melt_kA",
                            OrderedDict(
                                [
                                    ("proposed", 14.2),
                                    ("clamped", 9.6),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 216),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 3.27),
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
            ("name", "clamped_melt_current"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("melt_kA", 9.6),
                        ("flux_feed_kg_min", 2.4),
                        ("ingot_t", 18.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: melt 14.2 -> 9.6 kA. Process-correct vs the 1620 C slag-skin "
                "cap. Slag-crust tear still occurs at 22.800 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held slag-skin at 1594 C. At 22.800 ms stored "
                "hoop in the slag crust still tore a 26 mm skin. Clamp reduced dump energy; "
                "it did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("melt", "clamp executed; peak 1594 C < 1620"),
                        ("slag_crust", "26 mm tear at 22.800 ms"),
                        ("repair", "15 min mold isolate (abort_s=900)"),
                        ("mission", "TK-3 ESR pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither slag-cap nor melt-current predicted the hoop charge; ae.slag.tear is a new channel at 22.800 ms, 15.640 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min mold isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min mold isolate after a 26 mm slag-crust tear. Safety head -0.58 "
                "prices the split; task_progress stays +0.32 because the melt clamp completed "
                "under the 1620 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.slag.cap (6.280 ms, 1680 C)"),
                        ("loser", "enc.melt.kA (6.496 ms, 14.2 kA)"),
                        ("margin_us", 216),
                        (
                            "counterfactual_if_reversed",
                            "Current-first by < 216 us inside the 500 us window would have kept "
                            "14.2 kA cruise; predicted next-sample 1648 C would have exceeded "
                            "the 1620 cap even without the hoop charge. The MODIFY is still the "
                            "correct process. The tear is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22800),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.800 ms slag-crust tear (tick t_us=22800), inside "
                "the 42 ms raster. The correct MODIFY at 7.160 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=900 isolate tick.",
            ),
        ]
    )
    spikes = [
        spike("enc.melt.ctx", 1.220, 0.42),
        spike("tc.slag.cap", 2.520, 0.61),
        spike("enc.melt.kA", 3.810, 0.50),
        spike("tc.slag.cap", 6.280, 1.31),
        spike("enc.melt.kA", 6.496, 1.14),
        spike("ctrl.gate", 7.160, 0.98),
        spike("tc.slag.cap", 8.540, 0.80),
        spike("enc.melt.kA", 11.420, 0.62),
        spike("ctrl.gate", 14.920, 0.84),
        spike("ae.slag.tear", 22.800, 1.46),
        spike("ae.slag.tear", 24.560, 0.91),
        spike("enc.melt.ctx", 31.400, 0.41),
        spike("tc.slag.cap", 38.200, 0.53),
    ]
    ras = raster_core(
        42,
        72,
        28,
        85,
        routing(
            "thalamic-relay.esr-cap",
            "spikenaut.policy.melt-clamp",
            [
                ("relay.tc.cap", "policy.current_clamp", 0.66),
                ("relay.enc.melt", "policy.current_hold", 0.30),
                ("relay.ae.tear", "policy.current_clamp", -0.45),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at cap win (6.280 ms) opens a 50 ms "
            "eligibility trace that still covers the 22.800 ms slag-crust tear",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.50),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("current_clamp", 36, 0.50, 278.0, 5),
                    pop("current_hold", 36, 0.50, 55.6, 1),
                    pop("slag_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r44-236"),
            (
                "title",
                "Thoria-Kettle TK-3 / Remelt-Bay RB-7: slag-cap beats melt-current by 216 us; correct "
                "MODIFY still eats an in-window slag-crust tear (partnered negative total -0.46)",
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
                    "42 ms raster. total -0.46 = 0.32 + -0.58 + -0.16 + 0.02 + -0.06. Named mold "
                    "isolate (abort_s=900) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "esr-ingot-melt",
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
                    "15 min mold isolate.",
                    1,
                ),
            ),
        ]
    )


def record_237():
    ticks = [
        tick(1760, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(4180, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(4332, -0.03, -0.01, -0.03, -0.02, 0.01),
        tick(4920, -0.07, -0.04, -0.09, -0.05, 0.02),
        tick(6410, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(1320000000, -0.02, -0.01, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("dp.argon.ctx", 0.880, 0.40),
        spike("load.press.MPa", 1.760, 0.58),
        spike("load.shadow.ksi", 2.520, 0.51),
        spike("load.press.MPa", 4.180, 1.32),
        spike("load.shadow.ksi", 4.332, 1.15),
        spike("ctrl.gate", 4.920, 1.00),
        spike("load.press.MPa", 6.410, 0.74),
        spike("load.shadow.ksi", 8.100, 0.61),
        spike("ctrl.gate", 12.000, 0.82),
        spike("dp.argon.ctx", 16.200, 0.42),
        spike("load.press.MPa", 20.600, 0.53),
        spike("load.shadow.ksi", 23.200, 0.47),
    ]
    excerpt = independent_excerpt(44237, 88, 24000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "HIP-Skid HS-4 on Nitrid-Fell NF-2 is armed for a 4.2 MPa/min argon ramp "
                "with live vessel 86.0 MPa against a 105.0 MPa canister cap. A unit-shadow "
                "tag still reports the same 86 as ksi on a sibling engineering-unit bus. "
                "MPa-first should ACCEPT the ramp; a weak supervisor that binds the ksi "
                "shadow onto the MPa cap will REJECT a legal move.",
            ),
            ("domain", "hip-isostatic-press"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Execute the 4.2 MPa/min argon ramp while vessel pressure stays <= 105.0 MPa; "
                "do not spend a ksi shadow on the press hold.",
            ),
            ("t0_us", 1756794621000237),
            ("gate_latency_us", 740),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.12, 4.44]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "load.press.MPa 86.0 MPa",
                                "load.shadow.ksi 86 ksi unit-shadow",
                            ],
                        ),
                        (
                            "semantics",
                            "MPa-first should ACCEPT 4.2 MPa/min (86.0 MPa < 105.0 MPa cap). "
                            "Shadow-first tempts a weak supervisor to treat 86 ksi as 593 MPa.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one vessel Hall sample minus unit-shadow encoder "
                            "group delay on this dual-unit skid.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 152 us vs combined jitter ~54 us (press 24 + shadow 30): 2.8x over "
                            "a 2.0x trust floor. Order is correctly MPa-first. The error is which "
                            "unit the REJECT is bound to, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "vessel Hall probe, 4 kHz, 24 us jitter",
                    "unit-shadow tag, 4 kHz, 30 us jitter",
                    "argon differential pressure (context)",
                    "canister thermocouple (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("press_cap_MPa", 105.0),
                        ("press_MPa", 86.0),
                        ("shadow_ksi", 86.0),
                        ("shadow_as_MPa", 593.0),
                        ("proposed_ramp_MPa_min", 4.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. HS-4 canister latched; argon ramp 4.2 MPa/min armed on NF-2.",
                    "2. Vessel 86.0 MPa; unit-shadow 86 ksi on a separate engineering-unit bus.",
                    "3. Argon-dp precursor at 0.880 ms.",
                    "4. Race window [4.120, 4.440] ms.",
                    "5. load.press.MPa 86.0 MPa at 4.180 ms (winner).",
                    "6. load.shadow.ksi 86 ksi at 4.332 ms (loser by 152 us).",
                    "7. Gate at 4.920 ms: REJECT hold 0.00 MPa/min (incorrect).",
                    "8. Legal ramp cancelled; vessel still 86.0 MPa < 105.0 MPa cap.",
                    "9. ksi shadow remains a unit tag, not a pressure.",
                    "10. Delayed missed_window_s=1320 (22 min argon-quality window) while the skid waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "argon_ramp_42"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ramp_MPa_min", 4.2),
                        ("hold", False),
                        ("unit", "MPa"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("press_MPa", 86.0),
                        ("press_cap_MPa", 105.0),
                        ("unit_live", "MPa"),
                        ("shadow_ksi", 86.0),
                        ("shadow_as_MPa", 593.0),
                        ("unit_shadow", "ksi"),
                        ("proposed_ramp_MPa_min", 4.2),
                        ("race_margin_us", 152),
                        ("combined_jitter_us", 54),
                        ("missed_window_s", 1320),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.2 MPa/min argon ramp because vessel 86.0 MPa is under "
                "the 105.0 MPa canister cap; 86 ksi is a different unit bus, not 593 MPa.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Shadow 86 ksi looks like a pressure excursion over a 105 MPa cap once the "
                "supervisor treats ksi as MPa (593 MPa apparent). MPa-first is treated as a "
                "noisy echo of the same loop. Over-caution on a dual-unit skid is the stated doctrine.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "press_MPa",
                            OrderedDict(
                                [
                                    ("cap", 105.0),
                                    ("observed", 86.0),
                                    ("executed_ramp_MPa_min", 0.0),
                                    ("unit", "MPa"),
                                ]
                            ),
                        ),
                        (
                            "shadow_ksi",
                            OrderedDict(
                                [
                                    ("observed", 86.0),
                                    ("misbound_as_MPa", 593.0),
                                    ("misbound_as", "press_excursion"),
                                    ("unit", "ksi"),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 152),
                                    ("combined_jitter_us", 54),
                                    ("ratio", 2.81),
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
            ("name", "press_hold_wrong_unit"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ramp_MPa_min", 0.0),
                        ("hold", True),
                        ("unit", "MPa"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): ramp 4.2 -> 0.00 MPa/min. Routing relay.unit.ksi_shadow -> "
                "policy.press_hold; vessel 86.0 MPa left unused as a go signal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT held HS-4 at 0.00 MPa/min. Vessel 86.0 MPa was under the 105.0 MPa "
                "cap; 86 ksi was a unit-shadow, not 593 MPa. 22 min argon-quality window "
                "missed (missed_window_s=1320). Correct gate was ACCEPT of the 4.2 MPa/min ramp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("press", "held; ramp 0.00 MPa/min; vessel still 86.0 MPa < 105.0 MPa"),
                        ("shadow", "86 ksi unused, still a unit tag not a pressure"),
                        ("skid", "22 min argon-quality window missed"),
                        ("mission", "ramp deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "MPa-first was the correct order and the vessel number was legal; the REJECT spent that win on the ksi shadow.",
                    "Delayed (missed_window_s=1320): NF-2 loses the 22 min argon-quality window; next window 5.4 h.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT the 4.2 MPa/min argon ramp; leave 86 ksi to its own unit bus.",
                        ),
                        ("correct_unit", "MPa"),
                        ("wrong_unit", "ksi"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("ramp_MPa_min", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "Missed 22 min argon-quality window (task/efficiency); vessel never exceeded 86.0 MPa (safety near-miss of a false hold).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "load.press.MPa (4.180 ms, 86.0 MPa)"),
                        ("loser", "load.shadow.ksi (4.332 ms, 86 ksi)"),
                        ("margin_us", 152),
                        (
                            "counterfactual_if_reversed",
                            "Shadow-first by < 152 us would still be a unit tag, not 593 MPa; "
                            "a correct gate binds load.press.MPa to press_go either way. The wrong "
                            "REJECT spent the MPa win on the wrong unit.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4920),
            (
                "reward_inflection_note",
                "Task, efficiency, and coherence drop at the wrong REJECT (4.920 ms, tick 4). "
                "The 22 min missed window is delayed surprise, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        24,
        88,
        36,
        76,
        routing(
            "relay.unit.ksi_shadow",
            "policy.press_hold",
            [
                ("relay.unit.ksi_shadow", "policy.press_hold", 0.73),
                ("relay.load.press", "policy.press_hold", 0.21),
            ],
            "acetylcholine",
            0.06,
            "unit_cap_stdp; ACh tags the (wrong) press_hold bind at the ksi shadow",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
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
                    pop("press_hold", 48, 0.50, 260.4, 4),
                    pop("press_go", 48, 0.80, 6.5, 0),
                    pop("unit_ctx", 32, 0.55, 97.7, 1),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r44-237"),
            (
                "title",
                "WRONG-REJECT at Nitrid-Fell NF-2 / HIP-Skid HS-4: vessel 86.0 MPa < 105.0 MPa cap; "
                "supervisor treats 86 ksi shadow as a 593 MPa excursion",
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
                    "Wrong-reject. Sidecar arithmetic 86.0 < 105.0 on MPa is true; REJECT bound "
                    "to ksi shadow. total -0.58 = -0.20 + -0.10 + -0.22 + -0.12 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "hip-isostatic-press",
                    [
                        "reject",
                        "wrong-gate",
                        "wrong-unit-shadow",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct MPa-first race can still be a wrong gate "
                    "when the REJECT binds a ksi shadow onto the press hold. Convictable from "
                    "unit IDs and caps without HIP physics.",
                    2,
                    supervisor_error_type="wrong-reject",
                ),
            ),
        ]
    )


def record_238():
    ticks = [
        tick(2680, 0.01, 0.05, 0.01, 0.01, 0.01),
        tick(5760, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5931, 0.02, 0.07, 0.02, 0.02, 0.01),
        tick(6860, 0.03, 0.12, 0.04, 0.03, 0.02),
        tick(9020, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(540000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("tc.riser.ctx", 1.380, 0.43),
        spike("rtd.riser.C", 2.680, 0.62),
        spike("ir.regen.glint", 4.180, 0.49),
        spike("rtd.riser.C", 5.760, 1.35),
        spike("ir.regen.glint", 5.931, 1.12),
        spike("ctrl.gate", 6.860, 1.03),
        spike("rtd.riser.C", 9.020, 0.77),
        spike("tc.riser.ctx", 13.200, 0.44),
        spike("ir.regen.glint", 17.100, 0.58),
        spike("ctrl.gate", 23.400, 0.81),
        spike("rtd.riser.C", 30.000, 0.54),
        spike("tc.riser.ctx", 36.600, 0.38),
        spike("ir.regen.glint", 39.100, 0.46),
    ]
    excerpt = independent_excerpt(44238, 104, 40000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Slide-Valve SV-4 is frozen on Riser-Wold RW-5's HIL FCC riser while a dense-phase "
                "RTD reports 548 C against a 560 C conversion floor. A regen-flue IR, lit by the "
                "pad lamp spectrum, still reads 612 C apparent. Riser-first latches REJECT hold; "
                "glint-first would commit a 18 t/h feed on an under-floor riser.",
            ),
            ("domain", "fcc-riser-cracker"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not open the slide valve unless riser outlet >= 560 C; keep feed 0.0 t/h "
                "until the injected cold-oil packet drops.",
            ),
            ("t0_us", 1756794621000238),
            ("gate_latency_us", 1100),
            ("race_window_us", 380),
            ("race_window_rel_ms", [5.7, 6.08]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.riser.C 548 C",
                                "ir.regen.glint 612 C apparent",
                            ],
                        ),
                        (
                            "semantics",
                            "Riser-first latches REJECT hold 0.0 t/h; glint-first would commit "
                            "18 t/h on an apparent 612 C under-read of a cold-oil packet.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one dense-phase RTD slot versus regen-IR integration on this "
                            "FCC HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 171 us vs combined jitter ~58 us (riser 26 + IR 32): 2.9x "
                            "over a 2.0x trust floor. Pad injects the lamp 110-150 us before the "
                            "riser RTD (geometric lag, not a sensor fault); the apparent "
                            "612 C packet is still the loser in this 380 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "dense-phase riser RTD, 5 kHz burst, 26 us jitter",
                    "regen-flue IR, 200 Hz, 32 us jitter",
                    "riser skin thermocouple (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("riser_floor_C", 560.0),
                        ("observed_riser_C", 548.0),
                        ("regen_apparent_C", 612.0),
                        ("proposed_feed_t_h", 18.0),
                        ("lamp_inject_lead_us", [110, 150]),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("pad", "Riser-Wold RW-5 FCC riser mockup"),
                        ("injected", "cold-oil packet + regen-flue lamp spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop FCC riser. Invented plant; not a live cat-cracker.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Slide-Valve SV-4 on the RW-5 HIL riser; feed 18 t/h armed.",
                    "2. Lamp injected 110-150 us before riser RTD sees the cold-oil packet.",
                    "3. Skin precursor at 1.380 ms.",
                    "4. Race window [5.700, 6.080] ms.",
                    "5. rtd.riser.C 548 C at 5.760 ms (winner).",
                    "6. ir.regen.glint 612 C at 5.931 ms (loser by 171 us).",
                    "7. Gate at 6.860 ms: REJECT hold 0.0 t/h; do not feed 18 t/h.",
                    "8. Riser remains under floor this cycle; conversion floor held.",
                    "9. Catalyst recycle queued on the pad.",
                    "10. Delayed (abort_s=540): 9 min riser retune and lamp-spectrum retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "feed_riser_18"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 18.0),
                        ("hold", False),
                        ("regen_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("riser_C", 548.0),
                        ("riser_floor_C", 560.0),
                        ("regen_apparent_C", 612.0),
                        ("race_margin_us", 171),
                        ("combined_jitter_us", 58),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18 t/h feed because regen-flue apparent 612 C looks "
                "over the 560 C floor, treating riser 548 C as a noisy sheath echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Riser 548 C is under the 560 C conversion floor. Regen-flue apparent "
                "612 C is a HIL lamp under-read of a cold-oil packet, not a clearance. REJECT: hold "
                "0.0 t/h; do not commit 18 t/h across the riser.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "riser_C",
                            OrderedDict(
                                [
                                    ("floor", 560.0),
                                    ("observed_riser", 548.0),
                                    ("regen_apparent", 612.0),
                                ]
                            ),
                        ),
                        (
                            "feed_t_h",
                            OrderedDict(
                                [
                                    ("proposed", 18.0),
                                    ("executed", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 171),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 2.95),
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
            ("name", "hold_for_riser_floor"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 0.0),
                        ("hold", True),
                        ("regen_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0.0 t/h; 18 t/h feed cancelled. Riser 548 < 560 floor.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Slide-Valve SV-4 at 0.0 t/h. Riser under floor this cycle; "
                "conversion floor held. Regen-flue apparent was not treated as a riser clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("slide_valve", "held; feed 0.0 t/h"),
                        ("riser", "still under 560 C this cycle"),
                        ("regen_ir", "612 C unused as clearance"),
                        ("mission", "feed deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: lamp was injected 110-150 us before the riser RTD, yet riser still won the 380 us race.",
                    "Delayed (abort_s=540): pad policy update forbids treating regen-flue apparent as a riser substitute after a 9 min retune.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.riser.C (5.760 ms, 548 C)"),
                        ("loser", "ir.regen.glint (5.931 ms, 612 C apparent)"),
                        ("margin_us", 171),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 171 us inside the 380 us window would have committed "
                            "18 t/h with riser 548 < 560 floor. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6860),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (6.860 ms, tick 4) as the hold "
                "locks in over the illegal feed.",
            ),
        ]
    )
    ras = raster_core(
        40,
        104,
        22,
        92,
        routing(
            "thalamic-relay.fcc-riser",
            "spikenaut.policy.slide-hold",
            [
                ("relay.rtd.riser", "policy.slide_hold", 0.69),
                ("relay.ir.regen", "policy.slide_commit", 0.27),
                ("relay.tc.riser", "policy.slide_hold", 0.11),
            ],
            "dopamine",
            0.09,
            "conversion_stdp; DA at riser win (5.760 ms) tags slide_hold over slide_commit",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.38),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("slide_hold", 52, 0.50, 253.0, 5),
                    pop("slide_commit", 40, 0.50, 65.8, 1),
                    pop("riser_veto", 32, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r44-238"),
            (
                "title",
                "Riser-Wold RW-5 HIL / Slide-Valve SV-4: riser 548 C beats regen-flue 612; "
                "correct REJECT holds the FCC feed",
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
                    "Correct REJECT. Riser under floor; regen-flue lamp under-read unused as clearance. "
                    "total +0.78 = 0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "fcc-riser-cracker",
                    [
                        "reject",
                        "hil-riser",
                        "riser-vs-regen",
                        "conversion-floor",
                        "hil",
                    ],
                    "Teaches that a HIL regen-flue lamp under-read can lose to dense-phase RTD inside a "
                    "380 us window; reversing 171 us would have selected an illegal FCC feed.",
                    3,
                ),
            ),
        ]
    )


def record_239():
    ticks = [
        tick(3040, 0.04, 0.03, 0.02, 0.01, 0.00),
        tick(6840, 0.08, 0.07, 0.03, 0.02, 0.01),
        tick(7058, 0.05, 0.05, 0.02, 0.02, 0.01),
        tick(7280, 0.11, 0.09, 0.04, 0.03, 0.01),
        tick(9480, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(420000000, 0.02, 0.02, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("pt.hood.ctx", 1.540, 0.42),
        spike("rtd.shell.C", 3.040, 0.59),
        spike("ir.hood.glint", 4.980, 0.48),
        spike("rtd.shell.C", 6.840, 1.31),
        spike("ir.hood.glint", 7.058, 1.09),
        spike("ctrl.gate", 7.280, 0.96),
        spike("rtd.shell.C", 9.480, 0.73),
        spike("pt.hood.ctx", 13.700, 0.45),
        spike("ir.hood.glint", 18.200, 0.57),
        spike("ctrl.gate", 22.500, 0.80),
        spike("rtd.shell.C", 26.700, 0.51),
        spike("pt.hood.ctx", 29.200, 0.38),
    ]
    excerpt = independent_excerpt(44239, 60, 30000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Doctor-Bar DB-7 at Crepe-Noll CN-9 still holds a 1100 m/min reel while a "
                "198 C yankee-shell pulse sits over a 185 C crepe cap. A hood IR on the same "
                "canopy still claims 162 C cool-glint. Shell-first latches a speed "
                "clamp; glint-first would keep 1100 m/min into a close-out surge.",
            ),
            ("domain", "tissue-yankee-dryer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Reel CN-9 only if yankee shell <= 185 C; otherwise clamp "
                "speed so the crepe surge is not made at 1100 m/min.",
            ),
            ("t0_us", 1756794621000239),
            ("gate_latency_us", 440),
            ("race_window_us", 520),
            ("race_window_rel_ms", [6.75, 7.27]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.shell.C 198 C",
                                "ir.hood.glint 162 C cool-glint",
                            ],
                        ),
                        (
                            "semantics",
                            "Shell-first latches reel clamp 1100 -> 820 m/min; glint-first keeps "
                            "1100 m/min on a false-cool hood.",
                        ),
                        (
                            "window_derivation",
                            "520 us = one 2 kHz shell-RTD sample versus hood-IR decode on this "
                            "yankee bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 218 us vs combined jitter ~71 us (shell 33 + hood 38): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 218 us inside the 520 us "
                            "window would have kept 1100 m/min into a 198 C pulse.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "yankee-shell RTD, 2 kHz, 33 us jitter",
                    "hood IR camera, 200 Hz, 38 us jitter",
                    "hood-air PT (context)",
                    "doctor-bar load cell (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("crepe_cap_C", 185.0),
                        ("observed_shell_C", 198.0),
                        ("proposed_speed_m_min", 1100.0),
                        ("hood_glint_C", 162.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Doctor-Bar indexed onto CN-9 yankee; DB-7 armed at 1100 m/min.",
                    "2. Hood IR reports 162 C cool-glint; shell already sees 198 C.",
                    "3. Hood-PT precursor at 1.540 ms.",
                    "4. Race window [6.750, 7.270] ms.",
                    "5. rtd.shell.C 198 C at 6.840 ms (winner).",
                    "6. ir.hood.glint 162 C at 7.058 ms (loser by 218 us).",
                    "7. Gate at 7.280 ms: MODIFY reel 1100 -> 820 m/min.",
                    "8. Speed applies; next-sample shell 181 C < 185 cap.",
                    "9. Sheet occupies; next parent roll queued.",
                    "10. Delayed (yankee_reseq_s=420): dispatcher resequences the following parent +7 min.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "reel_1100"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_min", 1100.0),
                        ("steam_kPa", 220.0),
                        ("yankee_id", 9),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("shell_C", 198.0),
                        ("crepe_cap_C", 185.0),
                        ("hood_cool", True),
                        ("race_margin_us", 218),
                        ("combined_jitter_us", 71),
                        ("yankee_reseq_s", 420),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1100 m/min reel because the hood IR claims the canopy "
                "is cool, treating shell 198 C as a sidelobe.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Shell 198 C won by 218 us, so the pulse is inside the 185 C crepe cap. "
                "Hood-IR cool-glint is not a shell temperature. MODIFY: reel 1100 -> 820 m/min. "
                "A full REJECT (kill the sheet) is not indicated: 820 m/min is a legal catch-and-pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "shell_C",
                            OrderedDict(
                                [
                                    ("cap", 185.0),
                                    ("observed", 198.0),
                                    ("hood_cool", True),
                                    ("observed_after_clamp", 181.0),
                                ]
                            ),
                        ),
                        (
                            "speed_m_min",
                            OrderedDict(
                                [
                                    ("proposed", 1100.0),
                                    ("clamped", 820.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 218),
                                    ("combined_jitter_us", 71),
                                    ("ratio", 3.07),
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
            ("name", "clamped_reel_820"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_min", 820.0),
                        ("steam_kPa", 220.0),
                        ("yankee_id", 9),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: reel 1100 -> 820 m/min. Process-correct vs the 185 C crepe cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct MODIFY held DB-7 at 820 m/min. Next-sample shell 181 C under the "
                "185 C cap. Hood 162 C cool-glint was not treated as a shell clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("reel", "clamped 1100 -> 820 m/min"),
                        ("shell", "181 C < 185 cap after clamp"),
                        ("hood", "162 C unused as clearance"),
                        ("mission", "parent roll completed under cap"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Hood-IR cool-glint lagged the shell pulse by 218 us; order, not amplitude, selected the clamp.",
                    "Delayed (yankee_reseq_s=420): dispatcher resequences the following parent +7 min. Not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.shell.C (6.840 ms, 198 C)"),
                        ("loser", "ir.hood.glint (7.058 ms, 162 C)"),
                        ("margin_us", 218),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 218 us inside the 520 us window would have kept "
                            "1100 m/min into a 198 C pulse over the 185 cap. The MODIFY is "
                            "the correct process either way once shell RTD is bound.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7280),
            (
                "reward_inflection_note",
                "Task and safety step up at the MODIFY gate (7.280 ms, tick 4). Tick 6 is "
                "yankee_reseq_s=420.",
            ),
        ]
    )
    ras = raster_core(
        30,
        60,
        44,
        79,
        routing(
            "thalamic-relay.yankee-shell",
            "spikenaut.policy.speed-clamp",
            [
                ("relay.rtd.shell", "policy.speed_clamp", 0.64),
                ("relay.ir.hood", "policy.glint_hold", 0.29),
                ("relay.pt.hood", "policy.speed_clamp", 0.12),
            ],
            "serotonin",
            0.07,
            "crepe_stdp; 5-HT at shell win (6.840 ms) tags speed_clamp over glint_hold",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.52),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("speed_clamp", 30, 0.50, 256.4, 4),
                    pop("glint_hold", 30, 0.50, 64.1, 1),
                    pop("shell_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r44-239"),
            (
                "title",
                "Crepe-Noll CN-9 / Doctor-Bar DB-7: shell 198 C beats hood cool-glint; "
                "correct MODIFY clamps reel 1100 -> 820 m/min",
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
                    "Correct MODIFY. Shell over cap; hood cool-glint unused. total +0.92 = "
                    "0.34 + 0.30 + 0.14 + 0.10 + 0.04.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "tissue-yankee-dryer",
                    [
                        "modify",
                        "designed",
                        "shell-vs-hood",
                        "crepe-cap",
                    ],
                    "Teaches that a cool-glint hood IR can lose to a legal yankee-shell RTD inside "
                    "a 520 us window; reversing 218 us would have kept an illegal 1100 m/min reel.",
                    4,
                ),
            ),
        ]
    )


def record_240():
    ticks = [
        tick(1580, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(3740, 0.10, 0.08, 0.04, 0.03, 0.02),
        tick(3858, 0.06, 0.05, 0.03, 0.02, 0.01),
        tick(4300, 0.14, 0.10, 0.05, 0.04, 0.02),
        tick(6120, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(280000000, 0.03, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("pt.pot.ctx", 0.700, 0.39),
        spike("rtd.pot.C", 1.580, 0.57),
        spike("ir.kettle.glint", 2.400, 0.48),
        spike("rtd.pot.C", 3.740, 1.29),
        spike("ir.kettle.glint", 3.858, 1.10),
        spike("ctrl.gate", 4.300, 0.97),
        spike("rtd.pot.C", 6.120, 0.76),
        spike("ir.kettle.glint", 8.800, 0.61),
        spike("ctrl.gate", 12.200, 0.83),
        spike("pt.pot.ctx", 15.900, 0.41),
        spike("rtd.pot.C", 19.400, 0.54),
        spike("ir.kettle.glint", 21.200, 0.46),
    ]
    excerpt = independent_excerpt(44240, 84, 22000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Sink-Roll SR-8 in Zinc-Fen ZF-4 is already at 458 C pot while a "
                "kettle pyrometer glint still reports 512 against a 480 C dross cap that the "
                "pot RTD has not crossed. Pot-first should ACCEPT the already-legal "
                "1.85 m/s strip; glint-first would hold a legal line on lighting.",
            ),
            ("domain", "galvanize-pot-line"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Run SR-8 when pot RTD is <= 480 C; do not spend a kettle pyrometer glint "
                "on a hold.",
            ),
            ("t0_us", 1756794621000240),
            ("gate_latency_us", 560),
            ("race_window_us", 240),
            ("race_window_rel_ms", [3.7, 3.94]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.pot.C 458 C",
                                "ir.kettle.glint 512 lighting",
                            ],
                        ),
                        (
                            "semantics",
                            "Pot-first ACCEPTS the already-legal 458 C strip. Glint-first "
                            "would REJECT a legal line on a 512 C lighting.",
                        ),
                        (
                            "window_derivation",
                            "240 us = one pot-RTD sample minus kettle-pyrometer integration on this "
                            "pot-line simulation.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 118 us vs combined jitter ~50 us (RTD 22 + IR 28): 2.4x over "
                            "a 2.0x trust floor. Reversing order by < 118 us inside the 240 us "
                            "window would have invented a dross hold on an already-legal 458 C pot.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "pot RTD, 2 kHz, 22 us jitter",
                    "kettle pyrometer, 200 Hz, 28 us jitter",
                    "pot PT (context)",
                    "sink-roll torque (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("dross_cap_C", 480.0),
                        ("observed_pot_C", 458.0),
                        ("kettle_glint_C", 512.0),
                        ("proposed_speed_m_s", 1.85),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. SR-8 seeded; zinc at 458 C pot under 480 dross cap.",
                    "2. Kettle pyrometer glint 512 from kettle lighting, not dross cake.",
                    "3. Pot-PT precursor at 0.700 ms.",
                    "4. Race window [3.700, 3.940] ms.",
                    "5. rtd.pot.C 458 C at 3.740 ms (winner).",
                    "6. ir.kettle.glint 512 at 3.858 ms (loser by 118 us).",
                    "7. Gate at 4.300 ms: ACCEPT 1.85 m/s as proposed.",
                    "8. Strip executes; pot remains 458 C < 480.",
                    "9. Coil emptied; next pass queued.",
                    "10. Delayed (survey_hold_s=280): 4.7 min coating survey. Not a safety inflection.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "strip_185"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_s", 1.85),
                        ("hold", False),
                        ("pot_kPa", 22.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("pot_C", 458.0),
                        ("dross_cap_C", 480.0),
                        ("kettle_glint_C", 512.0),
                        ("race_margin_us", 118),
                        ("combined_jitter_us", 50),
                        ("survey_hold_s", 280),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.85 m/s because pot RTD 458 C is under the 480 C "
                "dross cap; kettle 512 C is lighting, not dross.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Pot RTD 458 C is under the 480 C dross cap. Kettle 512 C is a "
                "lighting glint, not dross load. ACCEPT the proposed 1.85 m/s; do "
                "not invent a hold.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "pot_C",
                            OrderedDict(
                                [
                                    ("cap", 480.0),
                                    ("observed", 458.0),
                                    ("kettle_glint_C", 512.0),
                                ]
                            ),
                        ),
                        (
                            "speed_m_s",
                            OrderedDict(
                                [
                                    ("proposed", 1.85),
                                    ("executed", 1.85),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 118),
                                    ("combined_jitter_us", 50),
                                    ("ratio", 2.36),
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
            ("name", "strip_185"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("speed_m_s", 1.85),
                        ("hold", False),
                        ("pot_kPa", 22.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: proposed 1.85 m/s executed unchanged. Pot 458 C < 480; kettle glint unused.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT ran SR-8 at 458 C pot. Kettle 512 C was lighting, not dross. "
                "The proposal was already legal; reversing 118 us would have invented a hold.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("roll", "strip executed; pot 458 C < 480"),
                        ("kettle_ir", "512 C glint unused as dross"),
                        ("pot", "held 22.0 kPa through the pass"),
                        ("mission", "strip committed"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Kettle 512 C is a legal lighting glint, not a high-pot alarm; pot-first discarded a false hold.",
                    "Delayed (4.7 min / survey_hold_s=280): coating survey. Not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.pot.C (3.740 ms, 458 C)"),
                        ("loser", "ir.kettle.glint (3.858 ms, 512 lighting)"),
                        ("margin_us", 118),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 118 us inside the 240 us window would have held "
                            "the line on a false high-pot story. The proposal was already "
                            "under the 480 cap, so the correct gate is still ACCEPT.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4300),
            (
                "reward_inflection_note",
                "Task and safety step up at the ACCEPT gate (4.300 ms, tick 4). Tick 6 is "
                "survey_hold_s=280.",
            ),
        ]
    )
    ras = raster_core(
        22,
        84,
        32,
        59,
        routing(
            "thalamic-relay.pot-rtd",
            "spikenaut.policy.strip-accept",
            [
                ("relay.rtd.pot", "policy.strip_go", 0.62),
                ("relay.ir.kettle", "policy.glint_hold", 0.28),
                ("relay.pt.pot", "policy.strip_go", 0.14),
            ],
            "adenosine",
            0.16,
            "pre_post_stdp; adenosine at pot win (3.740 ms) opens 160 ms eligibility covering the 4.300 ms accept",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.24),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("strip_go", 42, 0.50, 297.6, 3),
                    pop("glint_hold", 42, 0.50, 19.8, 0),
                    pop("dross_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r44-240"),
            (
                "title",
                "Zinc-Fen ZF-4 / Sink-Roll SR-8: pot 458 C beats kettle glint; "
                "correct ACCEPT of an already-legal 1.85 m/s (total +1.16)",
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
                    "Correct ACCEPT. Pot 458 C < 480; kettle glint is lighting, not dross. "
                    "total +1.16 = 0.44 + 0.34 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "galvanize-pot-line",
                    [
                        "accept",
                        "simulated-lighting",
                        "pot-vs-kettle",
                        "strip",
                        "simulated",
                    ],
                    "Teaches that a kettle lighting glint can lose to a legal pot RTD "
                    "inside a 240 us window; reversing 118 us would have invented a hold on an "
                    "already-legal strip.",
                    5,
                ),
            ),
        ]
    )
