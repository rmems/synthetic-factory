def record_463():
    ticks = [
        tick(2810, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(7180, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7366, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7980, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(8200, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(420000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("tc.still.ctx", 1.420, 0.43),
        spike("ae.cond.pps", 2.880, 0.61),
        spike("enc.take.kg", 4.550, 0.49),
        spike("ae.cond.pps", 7.180, 1.34),
        spike("enc.take.kg", 7.366, 1.11),
        spike("ctrl.gate", 7.980, 1.02),
        spike("ae.cond.pps", 10.200, 0.78),
        spike("tc.still.ctx", 14.800, 0.44),
        spike("enc.take.kg", 19.400, 0.58),
        spike("ctrl.gate", 24.600, 0.81),
        spike("ae.cond.pps", 31.200, 0.53),
        spike("enc.take.kg", 38.800, 0.46),
        spike("tc.still.ctx", 42.100, 0.37),
    ]
    excerpt = independent_excerpt(89463, 108, 44000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Still ZT-1 on the Zirconyl-Thwaite ZT-HIL pad is armed for a 0.18 kg/h ZrCl4 "
                "takeoff while a condenser AE packet reads 62 pps against an 18 pps move cap. A "
                "takeoff-mass encoder, lit by the pad lamp, still reads 2.4 kg under a 6.0 kg "
                "travel look. AE-first latches REJECT hold; encoder-first would commit a 0.18 "
                "kg/h takeoff into a live condenser rattle.",
            ),
            ("domain", "zirconium-tetrachloride-still"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not raise Still ZT-1 takeoff unless condenser AE <= 18 pps; keep takeoff "
                "0.0 kg/h until the injected condenser band recovers.",
            ),
            ("t0_us", 1756850400000463),
            ("gate_latency_us", 860),
            ("race_window_us", 320),
            ("race_window_rel_ms", [7.10, 7.42]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.cond.pps 62 pps",
                                "enc.take.kg 2.4 kg under 6.0",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches REJECT hold 0.0 kg/h takeoff; encoder-first would "
                            "commit a 0.18 kg/h raise on an apparent 2.4 kg under-read.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one condenser-AE sample versus encoder integration on this "
                            "zirconium HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 186 us vs combined jitter 58 us (AE 26 + ENC 32): 3.2x over a "
                            "2.0x trust floor. Pad injects the encoder lamp 110-150 us before the "
                            "AE (geometric lag, not a sensor fault); the 2.4 kg packet is still "
                            "the loser in this 320 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "condenser AE puck, 5 kHz burst, 26 us jitter",
                    "takeoff mass encoder, 200 Hz, 32 us jitter",
                    "still thermocouple (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cond_cap_pps", 18.0),
                        ("observed_cond_pps", 62.0),
                        ("take_kg", 2.4),
                        ("take_look_kg", 6.0),
                        ("proposed_raise_kg_h", 0.18),
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
                            "Zirconyl-Thwaite ZT-HIL ZrCl4 sublimation still mockup with physical takeoff screw",
                        ),
                        ("injected", "condenser AE burst + encoder lamp spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop zirconium tetrachloride still. Invented plant; not a live Zr shop.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Still ZT-1 on the ZT-HIL pad; 0.18 kg/h takeoff armed.",
                    "2. Encoder lamp injected 110-150 us before AE sees 62 pps.",
                    "3. Still-TC precursor at 1.420 ms.",
                    "4. Race window [7.100, 7.420] ms.",
                    "5. ae.cond.pps 62 pps at 7.180 ms (winner).",
                    "6. enc.take.kg 2.4 kg at 7.366 ms (loser by 186 us).",
                    "7. Gate at 7.980 ms: REJECT hold 0.0 kg/h; do not raise 0.18.",
                    "8. Condenser remains over 18 pps this cycle; takeoff cap held.",
                    "9. Screw re-seat queued on the pad.",
                    "10. Delayed (abort_s=420): 7 min band re-settle and lamp-spectrum retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "raise_zrcl4_takeoff"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("raise_kg_h", 0.18),
                        ("hold", False),
                        ("encoder_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("cond_pps", 62.0),
                        ("cond_cap_pps", 18.0),
                        ("take_kg", 2.4),
                        ("take_look_kg", 6.0),
                        ("race_margin_us", 186),
                        ("combined_jitter_us", 58),
                        ("abort_s", 420),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 0.18 kg/h takeoff raise because encoder 2.4 kg looks under "
                "the 6.0 kg travel look, treating AE 62 pps as a noisy bus echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Condenser AE 62 pps is over the 18 pps takeoff-move cap. Encoder 2.4 kg is a HIL "
                "lamp under-read, not a clearance. REJECT: hold 0.0 kg/h; do not commit a "
                "0.18 kg/h raise.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "cond_pps",
                            OrderedDict(
                                [
                                    ("cap", 18.0),
                                    ("observed", 62.0),
                                    ("take_kg", 2.4),
                                ]
                            ),
                        ),
                        (
                            "raise_kg_h",
                            OrderedDict([("proposed", 0.18), ("executed", 0.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 186),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 3.21),
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
            ("name", "hold_for_condenser_drop"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("raise_kg_h", 0.0),
                        ("hold", True),
                        ("encoder_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0.0 kg/h; 0.18 kg/h raise cancelled. AE 62 > 18 pps cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Still ZT-1 at 0.0 kg/h takeoff. Condenser band over cap "
                "this cycle; takeoff cap held. Encoder apparent was not treated as an AE clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("takeoff", "held; 0.0 kg/h"),
                        ("condenser", "still over 18 pps this cycle"),
                        ("encoder", "2.4 kg unused as clearance"),
                        ("mission", "raise deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: encoder lamp was injected 110-150 us before the AE puck, yet condenser AE still won the 320 us race.",
                    "Delayed (abort_s=420): pad policy update forbids treating takeoff encoder kg as a condenser-AE substitute after a 7 min re-settle.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.cond.pps (7.180 ms, 62 pps)"),
                        ("loser", "enc.take.kg (7.366 ms, 2.4 kg)"),
                        ("margin_us", 186),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 186 us inside the 320 us window would have committed "
                            "a 0.18 kg/h raise with AE 62 > 18 pps cap. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7980),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (7.980 ms, tick 4) as the hold "
                "lands. The 7 min re-settle is delayed surprise bound to abort_s=420.",
            ),
        ]
    )
    ras = raster_core(
        44,
        108,
        22,
        105,
        routing(
            "thalamic-relay.zt-ae",
            "spikenaut.policy.takeoff-hold",
            [
                ("relay_cond_pps", "policy_takeoff_hold", 0.70),
                ("relay_enc_take", "policy_enc_raise", 0.24),
            ],
            "dopamine",
            0.15,
            "cond_hold_stdp; DA tags the takeoff_hold bind at the condenser-AE win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 420),
                ("delayed_surprise_s", 420),
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
                    pop("takeoff_hold", 70, 0.48, 220.0, 5),
                    pop("enc_raise", 50, 0.85),
                    pop("ae_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r89-463"),
            (
                "title",
                "Zirconyl-Thwaite ZT-HIL / Still ZT-1: condenser AE 62 pps beats takeoff encoder "
                "2.4 kg by 186 us; correct REJECT holds the ZrCl4 takeoff",
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
                    "Correct REJECT. Condenser AE over cap beats encoder under-read. "
                    "total 0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06. Tick 6 binds abort_s=420.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "zirconium-tetrachloride-still",
                    [
                        "reject",
                        "hil",
                        "condenser-ae",
                        "encoder-underread",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a HIL takeoff-encoder under-read losing a 186 us race does not "
                    "clear a condenser-AE over-rate. Hold is distillable from pps vs cap.",
                    3,
                ),
            ),
        ]
    )


def record_464():
    ticks = [
        tick(3220, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(7920, 0.08, 0.05, 0.04, 0.03, 0.02),
        tick(8112, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(8360, 0.12, 0.09, 0.05, 0.04, 0.02),
        tick(8980, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(180000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.ag.ctx", 1.105, 0.43),
        spike("visc.broth.cP", 3.220, 0.59),
        spike("ir.shaft.C", 5.010, 0.50),
        spike("visc.broth.cP", 7.920, 1.27),
        spike("ir.shaft.C", 8.112, 1.09),
        spike("ctrl.gate", 8.360, 0.97),
        spike("visc.broth.cP", 11.200, 0.78),
        spike("ir.shaft.C", 14.880, 0.61),
        spike("ctrl.gate", 18.400, 0.84),
        spike("visc.broth.cP", 22.050, 0.56),
        spike("enc.ag.ctx", 24.100, 0.40),
    ]
    excerpt = independent_excerpt(89464, 54, 26000, 13, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("feed_t_h", 5.2),
            ("visc_cP", 4600.0),
            ("shaft_C", 31.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Gum tank X-9 at Xanthan-Toft XT-2 is already holding broth viscosity at "
                "4600 cP over an 1800 cP floor with a 5.2 t/h molasses feed already "
                "filed under the 8.0 t/h inlet ceiling. Shaft-IR-first would extra-clamp a "
                "legal broth; viscosity-first ACCEPTS the filed 5.2 t/h xanthan pass.",
            ),
            ("domain", "xanthan-gum-fermenter"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold the 5.2 t/h molasses feed while viscosity stays >= 1800 cP and feed stays <= "
                "8.0 t/h; do not extra-clamp a legal xanthan fermenter.",
            ),
            ("t0_us", 1756850400000464),
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
                                "visc.broth.cP 4600 cP over 1800 floor",
                                "ir.shaft.C 31 C smear under 55 look",
                            ],
                        ),
                        (
                            "semantics",
                            "Viscosity-first ACCEPTS the already-legal 5.2 t/h feed. Shaft-first "
                            "would extra-clamp because 31 C looks under a 55 C broth look.",
                        ),
                        (
                            "window_derivation",
                            "440 us = one viscometer slot versus shaft-IR group delay on this "
                            "fermenter skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 192 us vs combined jitter 66 us (visc 32 + IR 34): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 192 us inside the 440 us "
                            "window would have extra-clamped a legal 4600 cP / 5.2 t/h pass.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "broth torque viscometer, 1 kHz, 32 us jitter",
                    "agitator-shaft IR pyrometer, 2 kHz, 34 us jitter",
                    "agitator encoder (context)",
                    "OUR offgas (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("visc_floor_cP", 1800.0),
                        ("observed_visc_cP", 4600.0),
                        ("shaft_C", 31.0),
                        ("feed_cap_t_h", 8.0),
                        ("proposed_feed_t_h", 5.2),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "unstructured kinetic + apparent-viscosity mixer, seed 89464; "
                            "10-zone aerated gum tank; NOT lumped-CSTR, NOT U-RANS, NOT a wet-stand",
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
                    "1. Gum tank X-9 in pass; 5.2 t/h molasses armed.",
                    "2. Viscosity 4600 cP over 1800 floor; feed 5.2 under 8.0 t/h inlet.",
                    "3. Agitator encoder precursor at 1.105 ms.",
                    "4. Race window [7.800, 8.240] ms.",
                    "5. visc.broth.cP 4600 cP at 7.920 ms (winner).",
                    "6. ir.shaft.C 31 C at 8.112 ms (loser by 192 us).",
                    "7. Gate at 8.360 ms: ACCEPT 5.2 t/h; executed identical to proposed.",
                    "8. Viscosity stays 4580 cP > 1800; feed 5.21 t/h < 8.0.",
                    "9. Shaft remaining a bearing glint did not require an extra clamp.",
                    "10. Delayed (survey_s=180): 180 s titer coupon on the harvest lock.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_xanthan_feed"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("visc_cP", 4600.0),
                        ("visc_floor_cP", 1800.0),
                        ("shaft_C", 31.0),
                        ("feed_cap_t_h", 8.0),
                        ("race_margin_us", 192),
                        ("combined_jitter_us", 66),
                        ("survey_s", 180),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 5.2 t/h feed: viscosity 4600 cP is over the "
                "1800 cP floor and 5.2 t/h is under 8.0 t/h inlet.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Viscosity 4600 cP won by 192 us and is over the 1800 cP floor. Shaft "
                "31 C is a bearing glint, not a broth miss. ACCEPT the filed 5.2 t/h "
                "feed. Executed identical to proposed. An extra clamp is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "visc_cP",
                            OrderedDict(
                                [
                                    ("floor", 1800.0),
                                    ("observed", 4600.0),
                                    ("executed_feed_t_h", 5.2),
                                ]
                            ),
                        ),
                        (
                            "shaft_C",
                            OrderedDict([("look", 55.0), ("observed", 31.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 192),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 2.91),
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
            ("name", "hold_xanthan_feed"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 5.2 t/h feed. Viscosity 4600 cP > 1800 floor.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 5.2 t/h molasses feed. Viscosity stayed 4580 cP over "
                "1800. Shaft remaining a bearing glint was the losing channel and did not "
                "justify an extra clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held; 5.2 t/h"),
                        ("visc", "4580 cP > 1800 floor"),
                        ("shaft", "31 C glint unused as broth miss"),
                        ("broth", "pass continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Shaft IR 31 C losing a 192 us race did not predict a viscosity miss; reversing 192 us would have extra-clamped a legal 4600 cP pass.",
                    "Delayed (survey_s=180): 180 s titer coupon on the harvest lock; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "visc.broth.cP (7.920 ms, 4600 cP)"),
                        ("loser", "ir.shaft.C (8.112 ms, 31 C)"),
                        ("margin_us", 192),
                        (
                            "counterfactual_if_reversed",
                            "Shaft-first by < 192 us inside the 440 us window would have extra-clamped "
                            "a legal pass. Viscosity-first confirms the filed feed.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 8360),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (8.360 ms, tick 4). The 180 s titer coupon "
                "is delayed surprise bound to survey_s=180, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        26,
        54,
        38,
        53,
        routing(
            "thalamic-relay.visc-probe",
            "spikenaut.policy.feed-accept",
            [
                ("relay_visc_cP", "policy_feed_accept", 0.66),
                ("relay_shaft_IR", "policy_extra_clamp", 0.23),
            ],
            "serotonin",
            0.12,
            "visc_confirm_stdp; 5-HT tags the feed_accept bind at the viscometer win",
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
            ("id", "ttf-r89-464"),
            (
                "title",
                "Xanthan-Toft XT-2 / Gum tank X-9: viscosity 4600 cP beats shaft IR 31 C by 192 us; "
                "ACCEPT already-legal 5.2 t/h xanthan molasses feed",
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
                    "Clean ACCEPT of an already-legal xanthan molasses feed. "
                    "total 1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08. Tick 6 binds survey_s=180.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "xanthan-gum-fermenter",
                    [
                        "accept",
                        "simulated",
                        "visc-vs-shaft",
                        "feed-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging shaft IR losing a 192 us race does not require an "
                    "extra clamp when broth viscosity is already over the gum floor.",
                    4,
                ),
            ),
        ]
    )


def record_465():
    ticks = [
        tick(1980, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(4980, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(5156, 0.08, 0.05, 0.03, 0.02, 0.01),
        tick(5360, 0.12, 0.09, 0.06, 0.04, 0.02),
        tick(6020, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(300000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.drum.ctx", 0.880, 0.44),
        spike("ppm.in.liquor", 1.980, 0.61),
        spike("ir.drum.C", 3.410, 0.52),
        spike("ppm.in.liquor", 4.980, 1.30),
        spike("ir.drum.C", 5.156, 1.12),
        spike("ctrl.gate", 5.360, 0.99),
        spike("ppm.in.liquor", 8.050, 0.77),
        spike("ir.drum.C", 11.400, 0.58),
        spike("ctrl.gate", 14.900, 0.83),
        spike("ppm.in.liquor", 18.200, 0.54),
        spike("enc.drum.ctx", 21.100, 0.39),
    ]
    excerpt = independent_excerpt(89465, 82, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("zn_t_h", 1.8),
            ("in_ppm", 214.0),
            ("drum_C", 38.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Cementation drum IN-5 at Indium-Grain IG-9 reads pregnant liquor indium at "
                "214 ppm against a 90 ppm cementation floor with a 1.8 t/h zinc-dust feed already "
                "filed under the 3.0 t/h drum ceiling. Drum-IR-first would extra-clamp a legal "
                "liquor; ppm-first ACCEPTS the filed 1.8 t/h pass.",
            ),
            ("domain", "indium-cementation-cell"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold the 1.8 t/h zinc-dust feed while liquor In stays >= 90 ppm and feed stays <= "
                "3.0 t/h; do not extra-clamp a legal indium cementation drum.",
            ),
            ("t0_us", 1756850400000465),
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
                                "ppm.in.liquor 214 ppm over 90 floor",
                                "ir.drum.C 38 C smear under 70 look",
                            ],
                        ),
                        (
                            "semantics",
                            "ppm-first ACCEPTS the already-legal 1.8 t/h zinc dust. Drum-IR-first would "
                            "extra-clamp because 38 C looks under a 70 C liquor look.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one liquor-ppm slot versus drum-IR group delay on this "
                            "cementation skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 176 us vs combined jitter 58 us (ppm 26 + IR 32): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 176 us inside the 300 us "
                            "window would have extra-clamped a legal 214 ppm / 1.8 t/h pass.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "pregnant-liquor ICP-OES ppm, 4 kHz packet, 26 us jitter",
                    "drum-shell IR pyrometer, 1 kHz, 32 us jitter",
                    "drum encoder (context)",
                    "header DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("in_floor_ppm", 90.0),
                        ("observed_in_ppm", 214.0),
                        ("drum_C", 38.0),
                        ("zn_cap_t_h", 3.0),
                        ("proposed_zn_t_h", 1.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Drum IN-5 in pass; 1.8 t/h zinc dust armed.",
                    "2. Liquor In 214 ppm over 90 floor; feed 1.8 under 3.0 t/h drum.",
                    "3. Drum encoder precursor at 0.880 ms.",
                    "4. Race window [4.900, 5.200] ms.",
                    "5. ppm.in.liquor 214 ppm at 4.980 ms (winner).",
                    "6. ir.drum.C 38 C at 5.156 ms (loser by 176 us).",
                    "7. Gate at 5.360 ms: ACCEPT 1.8 t/h; executed identical to proposed.",
                    "8. In stays 212 ppm > 90; feed 1.81 t/h < 3.0.",
                    "9. Drum remaining a shell glint did not require an extra clamp.",
                    "10. Delayed (survey_s=300): 5 min In titer on the cement header.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_in_zn_feed"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("in_ppm", 214.0),
                        ("in_floor_ppm", 90.0),
                        ("drum_C", 38.0),
                        ("zn_cap_t_h", 3.0),
                        ("race_margin_us", 176),
                        ("combined_jitter_us", 58),
                        ("survey_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 1.8 t/h zinc dust: liquor In 214 ppm is over the "
                "90 ppm floor and 1.8 t/h is under 3.0 t/h drum.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Liquor In 214 ppm won by 176 us and is over the 90 ppm floor. Drum IR 38 C is a "
                "shell glint, not a liquor miss. ACCEPT the filed 1.8 t/h zinc dust. Executed "
                "identical to proposed. An extra clamp is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "in_ppm",
                            OrderedDict(
                                [
                                    ("floor", 90.0),
                                    ("observed", 214.0),
                                    ("executed_zn_t_h", 1.8),
                                ]
                            ),
                        ),
                        (
                            "drum_C",
                            OrderedDict([("look", 70.0), ("observed", 38.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 176),
                                    ("combined_jitter_us", 58),
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
            ("name", "hold_in_zn_feed"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 1.8 t/h zinc dust. In 214 ppm > 90 floor.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 1.8 t/h zinc-dust feed. Liquor In stayed 212 ppm over "
                "90. Drum remaining a shell glint was the losing channel and did not justify an "
                "extra clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("zn", "held; 1.8 t/h"),
                        ("in_ppm", "212 ppm > 90"),
                        ("drum", "38 C glint unused as liquor miss"),
                        ("cement", "pass continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Drum IR 38 C losing a 176 us race did not predict a liquor miss; reversing 176 us would have extra-clamped a legal 214 ppm drum.",
                    "Delayed (survey_s=300): 5 min In titer on the cement header; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ppm.in.liquor (4.980 ms, 214 ppm)"),
                        ("loser", "ir.drum.C (5.156 ms, 38 C)"),
                        ("margin_us", 176),
                        (
                            "counterfactual_if_reversed",
                            "Drum-IR-first by < 176 us inside the 300 us window would have extra-clamped "
                            "a legal drum. ppm-first confirms the filed zinc dust.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5360),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (5.360 ms, tick 4). The 5 min In titer "
                "is delayed surprise bound to survey_s=300, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        24,
        82,
        28,
        55,
        routing(
            "thalamic-relay.in-ppm",
            "spikenaut.policy.feed-accept",
            [
                ("relay_in_ppm", "policy_feed_accept", 0.69),
                ("relay_drum_IR", "policy_extra_clamp", 0.21),
            ],
            "adenosine",
            0.05,
            "ppm_confirm_stdp; adenosine tags the feed_accept bind at the liquor-ppm win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 300),
                ("delayed_surprise_s", 300),
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
            ("id", "ttf-r89-465"),
            (
                "title",
                "Indium-Grain IG-9 / Drum IN-5: liquor In 214 ppm beats drum IR 38 C by 176 us; "
                "ACCEPT already-legal 1.8 t/h zinc-dust feed",
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
                    "Clean ACCEPT of an already-legal indium zinc-dust feed. "
                    "total 1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08. Tick 6 binds survey_s=300.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "indium-cementation-cell",
                    [
                        "accept",
                        "designed",
                        "ppm-vs-drum",
                        "feed-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging drum IR losing a 176 us race does not require a "
                    "wait when liquor indium is already over the cementation floor.",
                    5,
                ),
            ),
        ]
    )
