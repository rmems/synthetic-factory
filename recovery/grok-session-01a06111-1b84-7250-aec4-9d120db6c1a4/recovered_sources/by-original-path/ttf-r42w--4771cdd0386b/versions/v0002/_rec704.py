def record_704():
    ticks = [
        tick(3180, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(8040, 0.08, 0.05, 0.04, 0.03, 0.02),
        tick(8228, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(8480, 0.12, 0.09, 0.05, 0.04, 0.02),
        tick(8940, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(180000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.kiln.ctx", 1.09, 0.43),
        spike("tc.bed.C", 3.18, 0.59),
        spike("ir.hood.C", 5.00, 0.50),
        spike("tc.bed.C", 8.04, 1.27),
        spike("ir.hood.C", 8.228, 1.09),
        spike("ctrl.gate", 8.48, 0.97),
        spike("tc.bed.C", 11.15, 0.78),
        spike("ir.hood.C", 14.80, 0.61),
        spike("ctrl.gate", 18.30, 0.84),
        spike("tc.bed.C", 21.90, 0.56),
        spike("enc.kiln.ctx", 24.05, 0.40),
    ]
    excerpt = independent_excerpt(42704, 64, 26000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Rotary Er2O3 bed C-7 at Erbia-Clough EC-5 measures 842 C on the axial TC "
                "tree, 78 K shy of the 920 C brick trip, and the screw is already filed at "
                "4.8 t/h under a 6.0 t/h ceiling. A hood pyrometer glint of 980 C still sits "
                "under a 1040 C look-up plaque. Confirming the bed keeps the legal charge; "
                "believing the hood would trim a kiln that is already inside both caps.",
            ),
            ("domain", "erbium-oxide-calciner"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold the 4.8 t/h charge while bed stays <= 920 C and feed stays <= 6.0 t/h; "
                "do not extra-clamp a legal Er2O3 calciner.",
            ),
            ("t0_us", 1756850400000704),
            ("gate_latency_us", 440),
            ("race_window_us", 460),
            ("race_window_rel_ms", [7.95, 8.41]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.bed.C 842 C under 920",
                                "ir.hood.C 980 C smear under 1040 look",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first ACCEPTS the already-legal 4.8 t/h charge. Hood-first "
                            "would extra-clamp because 980 C looks under a 1040 C freeze-lid look.",
                        ),
                        (
                            "window_derivation",
                            "460 us = one bed-TC slot versus hood-IR group delay on this "
                            "erbia-calciner skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 188 us vs combined jitter 66 us (TC 32 + IR 34): 2.8x over "
                            "a 2.0x trust floor. Reversing order by < 188 us inside the 460 us "
                            "window would have extra-clamped a legal 842 C / 4.8 t/h pass.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "rotary-bed thermocouple tree, 1 kHz, 32 us jitter",
                    "hood IR pyrometer, 2 kHz, 34 us jitter",
                    "screw encoder (context)",
                    "off-gas DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 920.0),
                        ("observed_bed_C", 842.0),
                        ("hood_C", 980.0),
                        ("feed_cap_tph", 6.0),
                        ("proposed_feed_tph", 4.8),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "1-D axial bed + radiation kernel, seed 42704; 8-zone Er2O3 "
                            "calciner; NOT lumped-CSTR, NOT U-RANS, NOT a wet-stand",
                        ),
                        (
                            "fidelity_limits",
                            "Rigid brick lining; no bed-motion. Raster is kernelized events, "
                            "not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Calciner C-7 in pass; 4.8 t/h charge armed.",
                    "2. Bed 842 C under 920 trip; feed 4.8 under 6.0 t/h screw.",
                    "3. Screw encoder precursor at 1.090 ms.",
                    "4. Race window [7.950, 8.410] ms.",
                    "5. tc.bed.C 842 C at 8.040 ms (winner).",
                    "6. ir.hood.C 980 C at 8.228 ms (loser by 188 us).",
                    "7. Gate at 8.480 ms: ACCEPT 4.8 t/h; executed identical to proposed.",
                    "8. Bed stays 844 C < 920; feed 4.81 t/h < 6.0.",
                    "9. Hood remaining a shell glint did not require an extra clamp.",
                    "10. Delayed (survey_s=180): 180 s Er titer on the cooler lock.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_er2o3_feed"),
            (
                "parameters",
                OrderedDict(
                    [("feed_tph", 4.8), ("bed_C", 842.0), ("hood_C", 980.0)]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 842.0),
                        ("bed_cap_C", 920.0),
                        ("hood_C", 980.0),
                        ("feed_cap_tph", 6.0),
                        ("race_margin_us", 188),
                        ("combined_jitter_us", 66),
                        ("survey_s", 180),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 4.8 t/h charge: bed 842 C is under the "
                "920 C trip and 4.8 t/h is under 6.0 t/h screw.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 842 C won by 188 us and is under the 920 C trip. Hood 980 C is a shell "
                "glint, not a thermal miss. ACCEPT the filed 4.8 t/h charge. Executed identical "
                "to proposed. An extra clamp is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 920.0),
                                    ("observed", 842.0),
                                    ("executed_feed_tph", 4.8),
                                ]
                            ),
                        ),
                        ("hood_C", OrderedDict([("look", 1040.0), ("observed", 980.0)])),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 188),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 2.85),
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
            ("name", "hold_er2o3_feed"),
            (
                "parameters",
                OrderedDict(
                    [("feed_tph", 4.8), ("bed_C", 842.0), ("hood_C", 980.0)]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 4.8 t/h charge. Bed 842 C < 920 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 4.8 t/h Er2O3 charge. Bed stayed 844 C under "
                "920 C. Hood remaining a shell glint was the losing channel and did not justify "
                "an extra clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held; 4.8 t/h"),
                        ("bed", "844 C < 920 C"),
                        ("hood", "980 C glint unused as thermal miss"),
                        ("oxide", "pass continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Hood IR 980 C losing a 188 us race did not predict a thermal miss; reversing 188 us would have extra-clamped a legal 842 C pass.",
                    "Delayed (survey_s=180): 180 s Er titer on the cooler lock; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bed.C (8.040 ms, 842 C)"),
                        ("loser", "ir.hood.C (8.228 ms, 980 C)"),
                        ("margin_us", 188),
                        (
                            "counterfactual_if_reversed",
                            "Hood-first by < 188 us inside the 460 us window would have "
                            "extra-clamped a legal pass. Bed-first confirms the filed charge.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 8480),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (8.480 ms, tick 4). The 180 s Er titer is delayed "
                "surprise bound to survey_s=180, not the inflection.",
            ),
            ("delayed_surprise_s", 180),
        ]
    )
    ras = raster_core(
        26,
        64,
        40,
        67,
        routing(
            "thalamic-relay.er-bed",
            "spikenaut.policy.feed-accept",
            [
                ("relay_bed_C", "policy_feed_accept", 0.66),
                ("relay_hood_IR", "policy_extra_clamp", 0.23),
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
                ("survey_s", 180),
                ("delayed_surprise_s", 180),
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
                    pop("feed_accept", 50, 0.5, 175.0, 4),
                    pop("extra_clamp", 40, 0.85, 40.0, 1),
                    pop("hood_veto", 22, 0.8),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r42-704"),
            (
                "title",
                "Erbia-Clough EC-5 / Calciner C-7: bed 842 C beats hood IR 980 C by 188 us; "
                "ACCEPT already-legal 4.8 t/h Er2O3 charge",
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
                    "Clean ACCEPT of an already-legal Er2O3 charge. total 1.06 = 0.40 + 0.28 + "
                    "0.18 + 0.12 + 0.08. Tick 6 binds survey_s=180.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "erbium-oxide-calciner",
                    ["accept", "simulated", "bed-vs-hood", "feed-legal", "tick6-sidecar-bound"],
                    "Teaches that a lagging hood IR losing a 188 us race does not require an "
                    "extra clamp when the rotary bed is already under the thermal trip.",
                    4,
                ),
            ),
        ]
    )

