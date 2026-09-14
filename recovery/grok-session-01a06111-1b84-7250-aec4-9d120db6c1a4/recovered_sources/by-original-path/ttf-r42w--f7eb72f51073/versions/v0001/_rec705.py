def record_705():
    ticks = [
        tick(1960, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5080, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(5260, 0.08, 0.05, 0.03, 0.02, 0.01),
        tick(5440, 0.12, 0.09, 0.06, 0.04, 0.02),
        tick(5980, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(240000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.boat.ctx", 0.86, 0.44),
        spike("tc.still.C", 1.96, 0.61),
        spike("dp.cond.kPa", 3.38, 0.52),
        spike("tc.still.C", 5.08, 1.30),
        spike("dp.cond.kPa", 5.26, 1.12),
        spike("ctrl.gate", 5.44, 0.99),
        spike("tc.still.C", 8.02, 0.77),
        spike("dp.cond.kPa", 11.35, 0.58),
        spike("ctrl.gate", 14.80, 0.83),
        spike("tc.still.C", 18.10, 0.54),
        spike("enc.boat.ctx", 21.05, 0.39),
    ]
    excerpt = independent_excerpt(42705, 80, 24000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Thulium-metal distiller D-4 at Thulia-Fen TF-2 is already metering 0.38 kg/h "
                "under a 0.55 kg/h condenser ceiling while the still sits at 1280 C against a "
                "1360 C thermal trip. DP-first would extra-clamp a legal metal string; "
                "still-TC-first ACCEPTS the filed 0.38 kg/h Tm distillate.",
            ),
            ("domain", "thulium-metal-distiller"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold the 0.38 kg/h index while still stays <= 1360 C and index stays <= 0.55 "
                "kg/h; do not extra-clamp a legal Tm distiller.",
            ),
            ("t0_us", 1756850400000705),
            ("gate_latency_us", 360),
            ("race_window_us", 320),
            ("race_window_rel_ms", [5.0, 5.32]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.still.C 1280 C under 1360",
                                "dp.cond.kPa 7.8 smear under 6.0 look",
                            ],
                        ),
                        (
                            "semantics",
                            "Still-TC-first ACCEPTS the already-legal 0.38 kg/h index. DP-first "
                            "would extra-clamp because 7.8 kPa looks over a 6.0 kPa condenser look.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one still-TC slot versus condenser-DP group delay on this "
                            "thulium distiller skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (TC 26 + DP 32): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have extra-clamped a legal 1280 C / 0.38 kg/h pass.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "still-crown thermocouple, 4 kHz, 26 us jitter",
                    "condenser DP transmitter, 1 kHz, 32 us jitter",
                    "boat-index encoder (context)",
                    "end-seal IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("still_trip_C", 1360.0),
                        ("observed_still_C", 1280.0),
                        ("cond_dp_kPa", 7.8),
                        ("index_cap_kg_h", 0.55),
                        ("proposed_index_kg_h", 0.38),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Distiller D-4 in pass; 0.38 kg/h index armed.",
                    "2. Still 1280 C under 1360 trip; index 0.38 under 0.55 kg/h condenser.",
                    "3. Boat encoder precursor at 0.860 ms.",
                    "4. Race window [5.000, 5.320] ms.",
                    "5. tc.still.C 1280 C at 5.080 ms (winner).",
                    "6. dp.cond.kPa 7.8 at 5.260 ms (loser by 180 us).",
                    "7. Gate at 5.440 ms: ACCEPT 0.38 kg/h; executed identical to proposed.",
                    "8. Still stays 1282 C < 1360; index 0.381 kg/h < 0.55.",
                    "9. DP remaining a packing glint did not require an extra clamp.",
                    "10. Delayed (survey_s=240): 4 min metal-assay coupon on the boat lock.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_tm_index"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("index_kg_h", 0.38),
                        ("still_C", 1280.0),
                        ("cond_dp_kPa", 7.8),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("still_C", 1280.0),
                        ("still_trip_C", 1360.0),
                        ("cond_dp_kPa", 7.8),
                        ("index_cap_kg_h", 0.55),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 0.38 kg/h index: still 1280 C is under the "
                "1360 C trip and 0.38 kg/h is under 0.55 kg/h condenser.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Still 1280 C won by 180 us and is under the 1360 C trip. Condenser DP 7.8 kPa "
                "is a junction glint, not a thermal miss. ACCEPT the filed 0.38 kg/h index. "
                "Executed identical to proposed. An extra clamp is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "still_C",
                            OrderedDict(
                                [
                                    ("trip", 1360.0),
                                    ("observed", 1280.0),
                                    ("executed_index_kg_h", 0.38),
                                ]
                            ),
                        ),
                        (
                            "cond_dp_kPa",
                            OrderedDict([("look", 6.0), ("observed", 7.8)]),
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
            ("name", "hold_tm_index"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("index_kg_h", 0.38),
                        ("still_C", 1280.0),
                        ("cond_dp_kPa", 7.8),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 0.38 kg/h index. Still 1280 C < 1360 trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 0.38 kg/h index. Still stayed 1282 C under 1360. "
                "DP remaining a packing glint was the losing channel and did not justify an extra clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("index", "held; 0.38 kg/h"),
                        ("still", "1282 C < 1360"),
                        ("dp", "7.8 kPa glint unused as thermal miss"),
                        ("metal", "pass continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Condenser DP 7.8 kPa losing a 180 us race did not predict a thermal miss; reversing 180 us would have extra-clamped a legal 1280 C still.",
                    "Delayed (survey_s=240): 4 min metal-assay coupon on the boat lock; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.still.C (5.080 ms, 1280 C)"),
                        ("loser", "dp.cond.kPa (5.260 ms, 7.8 kPa)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "DP-first by < 180 us inside the 320 us window would have "
                            "extra-clamped a legal still. Still-TC-first confirms the filed index.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5440),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (5.440 ms, tick 4). The 4 min metal-assay coupon is "
                "delayed surprise bound to survey_s=240, not the inflection.",
            ),
            ("delayed_surprise_s", 240),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "kernelized_events"),
            ("sim_scope", "none"),
            ("survey_s", 240),
            ("delayed_surprise_s", 240),
            ("isi_histogram", isi_histogram(spikes)),
        ]
    )
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.tm-tc",
            "spikenaut.policy.index-accept",
            [
                ("relay_still_C", "policy_index_accept", 0.69),
                ("relay_dp_cond", "policy_extra_clamp", 0.21),
            ],
            "octopamine",
            0.05,
            "still_confirm_stdp; octopamine tags the index_accept bind at the still-TC win",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("index_accept", 45, 0.5, 210.0, 3),
                    pop("extra_clamp", 40, 0.85, 40.0, 1),
                    pop("dp_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r42-705"),
            (
                "title",
                "Thulia-Fen TF-2 / Distiller D-4: still 1280 C beats condenser DP 7.8 kPa by "
                "180 us; ACCEPT already-legal 0.38 kg/h Tm index with ISI histogram",
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
                    "Clean ACCEPT of an already-legal Tm distiller index. total 1.14 = 0.44 + "
                    "0.30 + 0.20 + 0.12 + 0.08. Tick 6 binds survey_s=240.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "thulium-metal-distiller",
                    [
                        "accept",
                        "designed",
                        "still-vs-dp",
                        "index-legal",
                        "isi-histogram",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging condenser DP losing a 180 us race does not require "
                    "a wait when still temperature is already under the thermal trip. ISI "
                    "histogram is a same-channel sidecar, not a second LIF.",
                    5,
                ),
            ),
        ]
    )

