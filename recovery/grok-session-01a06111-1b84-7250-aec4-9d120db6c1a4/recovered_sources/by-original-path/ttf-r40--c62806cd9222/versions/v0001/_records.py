def record_216():
    ticks = [
        tick(2056, -0.02, 0.01, -0.02, -0.01, 0.01),
        tick(5140, -0.04, 0.01, -0.04, -0.02, 0.01),
        tick(5370, -0.03, 0.01, -0.03, -0.01, 0.01),
        tick(5900, -0.06, 0.02, -0.08, -0.03, 0.02),
        tick(6260, -0.02, 0.01, -0.03, -0.01, 0.01),
        tick(1080000000, -0.01, 0.00, -0.02, 0.00, 0.00),
    ]
    spikes = [
        spike("enc.drum.ctx", 1.120, 0.41),
        spike("pv.drum.bar", 2.050, 0.58),
        spike("echo.sp.bar", 3.180, 0.50),
        spike("pv.drum.bar", 5.140, 1.33),
        spike("echo.sp.bar", 5.370, 1.16),
        spike("ctrl.gate", 5.900, 0.99),
        spike("pv.drum.bar", 7.200, 0.76),
        spike("echo.sp.bar", 9.440, 0.61),
        spike("ctrl.gate", 14.880, 0.84),
        spike("enc.drum.ctx", 18.400, 0.42),
        spike("pv.drum.bar", 24.200, 0.54),
        spike("echo.sp.bar", 27.100, 0.47),
    ]
    excerpt = independent_excerpt(40216, 80, 28000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Coke-Drum D-4 on Bitumen-Cairn BC-6 already sits at 1.18 bar live PV when "
                "a 1.72 bar setpoint echo still rings the analog loop. Published switch trip "
                "is 1.60 bar on the live PV; a weak supervisor treats the echo as process and "
                "holds a legal quench switch.",
            ),
            ("domain", "delayed-coker"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Switch D-4 to quench at 1.18 bar live PV, keep PV < 1.60 bar trip, and finish "
                "the 18 min quench window.",
            ),
            ("t0_us", 1756794621000216),
            ("gate_latency_us", 760),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.140, 5.500]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pv.drum.bar 1.18 bar live",
                                "echo.sp.bar 1.72 bar setpoint echo",
                            ],
                        ),
                        (
                            "semantics",
                            "PV-first should ACCEPT the quench switch (1.18 bar < 1.60 bar trip). "
                            "Echo-first would only delay confirmation of the same legal live PV.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one drum PT sample versus the SP-echo publisher on this "
                            "2.5 kHz coker bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 70 us (PV 32 + echo 38): 3.3x over "
                            "a 2.0x trust floor. Order is correctly PV-first. The error is binding "
                            "the setpoint echo as if it were live PV, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "drum PT, 2.5 kHz, 32 us jitter, axis pv_bar",
                    "setpoint analog echo, 1 kHz, 38 us jitter",
                    "drum-switch encoder (context)",
                    "steam-quench FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("pv_bar", 1.18),
                        ("trip_bar", 1.60),
                        ("echo_sp_bar", 1.72),
                        ("echo_is_process", False),
                        ("proposed_switch", True),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Drum D-4 indexed on Bitumen-Cairn BC-6; live 1.18 bar, quench switch armed.",
                    "2. Published live trip 1.60 bar; SP echo 1.72 bar is not a process variable.",
                    "3. Encoder precursor at 1.120 ms.",
                    "4. Race window [5.140, 5.500] ms.",
                    "5. pv.drum.bar 1.18 bar at 5.140 ms (winner).",
                    "6. echo.sp.bar 1.72 bar at 5.370 ms (loser by 230 us).",
                    "7. Gate at 5.900 ms: wrong REJECT holds the quench switch.",
                    "8. Drum idle; live PV never crossed 1.60 bar.",
                    "9. 18 min quench window missed.",
                    "10. QA: correct gate was ACCEPT; leave switch; bind live 1.18 vs 1.60 trip.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "coker_quench_switch"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("switch_to_quench", True),
                        ("pv_bar", 1.18),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("pv_bar", 1.18),
                        ("trip_bar", 1.60),
                        ("echo_sp_bar", 1.72),
                        ("echo_is_process", False),
                        ("ft_axis", "pv_bar"),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 70),
                        ("t_gate_us", 5900),
                        ("missed_window_s", 1080),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes the quench switch because live PV 1.18 bar is 0.42 bar under "
                "the published 1.60 bar trip and the 1.72 bar reading is a setpoint echo, not PV.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Setpoint echo 1.72 bar is over the 1.60 bar trip (true vs that echo loop). "
                "REJECT: hold the quench switch until the echo recovers under 1.60 bar so the "
                "drum does not see an over-pressure event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "drum_pressure_bar",
                            OrderedDict(
                                [
                                    ("published_live_trip", 1.60),
                                    ("observed_live", 1.18),
                                    ("echo_sp_applied", 1.72),
                                    ("echo_is_process", False),
                                    ("executed_switch", False),
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
            ("name", "coker_hold_echo_as_pv"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("switch_to_quench", False),
                        ("pv_bar", 1.18),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): quench switch held. Routing relay.echo.sp -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live 1.18 bar "
                "never violated the 1.60 bar trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze D-4 with the quench switch held while live PV stayed "
                "1.18 bar under the 1.60 bar trip. 18 min quench window missed. Correct gate "
                "was ACCEPT of the already-legal switch.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("drum", "held; quench switch abandoned"),
                        ("pv_bar", "still 1.18 bar, under 1.60 bar published trip"),
                        ("cycle", "18 min quench window missed"),
                        ("echo", "1.72 bar SP echo false-positive, not process"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 1.72 bar loop is a setpoint echo; echo_is_process is false and it is not a published live trip.",
                    "Delayed (18 min): sister-drum D-5 ran the same quench window after QA rebound the live trip; D-4's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live 1.18 bar < published 1.60 bar trip; leave the quench switch.",
                        ),
                        ("correct_trip_bar", 1.60),
                        ("wrong_echo_bar", 1.72),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("switch_to_quench", False), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "18 min missed quench window (task/efficiency); live PV never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pv.drum.bar (5.140 ms, 1.18 bar)"),
                        ("loser", "echo.sp.bar (5.370 ms, 1.72 bar echo)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "Echo-first by < 230 us would still show live 1.18 bar < 1.60 bar. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the PV win "
                            "on a setpoint echo.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5900),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (5.900 ms, tick 4). The 18 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 1080.0),
            ("missed_window_s", 1080),
        ]
    )
    ras = raster_core(
        28,
        80,
        30,
        67,
        routing(
            "relay.echo.sp",
            "policy.hold_reject",
            [
                ("relay.echo.sp", "policy.hold_reject", 0.71),
                ("relay.pv.drum", "policy.hold_reject", 0.22),
            ],
            "acetylcholine",
            0.08,
            "echo_as_pv_stdp; ACh tags the (wrong) hold_reject bind at the live PV win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("missed_window_s", 1080),
                ("delayed_surprise_s", 1080),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 40, 0.50, 250.0, 4),
                    pop("go_accept", 40, 0.80, 8.0, 0),
                    pop("pv_trip_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r40-216"),
            (
                "title",
                "WRONG-REJECT at Bitumen-Cairn BC-6 / Coke-Drum D-4: live 1.18 bar is legal vs "
                "published 1.60 bar trip; supervisor bound a 1.72 bar setpoint echo as PV",
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
                    "Wrong-reject. Sidecar arithmetic 1.18 < 1.60 is true; clamp bound to a "
                    "1.72 bar SP echo. total -0.36 = -0.18 + 0.06 + -0.22 + -0.08 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "delayed-coker",
                    [
                        "reject",
                        "wrong-gate",
                        "sp-echo-as-pv",
                        "echo-as-process",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live<trip read can still be a wrong gate when "
                    "routing.table[0].to is policy.hold_reject and executed switch is held.",
                    1,
                    supervisor_error_type="wrong-reject",
                ),
            ),
        ]
    )


def record_217():
    excerpt, extra = lif_217_excerpt()
    extra = OrderedDict(list(extra.items()) + [("abort_s", 840), ("delayed_surprise_s", 840)])
    ticks = [
        tick(2512, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(6280, 0.07, -0.04, -0.03, 0.01, -0.01),
        tick(6498, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(7100, 0.08, -0.06, -0.03, 0.02, -0.02),
        tick(22400, 0.06, -0.38, -0.04, -0.02, -0.02),
        tick(840000000, 0.02, -0.05, -0.02, 0.00, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Yankee-Y9 at Crepe-Nave CN-3 is already doctoring at 18.0 N/m while hood IR "
                "sits at 198 C against a 125 C yankee-surface cap. A hood-first latch clamps "
                "the doctor; a doctor-first story would keep the 18.0 N/m cruise. Stored "
                "adhesion in the coating ribbon is not yet an observable of either race channel.",
            ),
            ("domain", "tissue-yankee-dryer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the CN-3 crepe pass, keep yankee-surface skin <= 125 C, and leave the "
                "coating ribbon unmarked.",
            ),
            ("t0_us", 1756794621000217),
            ("gate_latency_us", 820),
            ("race_window_us", 480),
            ("race_window_rel_ms", [6.280, 6.760]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.hood.t 198 C pulse",
                                "enc.doctor.nm 18.0 N/m cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Hood-first latches doctor 18.0 -> 12.4 N/m; doctor-first keeps "
                            "cruise on a still-cooling surface model.",
                        ),
                        (
                            "window_derivation",
                            "480 us = one 1 kHz hood-IR sample minus doctor-load encoder group "
                            "delay on this yankee bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 218 us vs combined jitter ~72 us (hood 34 + doctor 38): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 218 us inside the 480 us window "
                            "would have kept 18.0 N/m cruise; predicted next-sample 128 C > 125 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "hood IR pyrometer, 1 kHz, 34 us timestamp jitter",
                    "doctor-load encoder, 500 Hz, 38 us jitter",
                    "coating AE puck (context until the ribbon snap)",
                    "yankee-steam PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("surface_cap_C", 125.0),
                        ("observed_hood_C", 198.0),
                        ("proposed_doctor_N_m", 18.0),
                        ("yankee_steam_bar", 3.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Yankee-Y9 indexed onto CN-3; coating ribbon armed at 18.0 N/m.",
                    "2. Cruise 18.0 N/m; hood IR 198 C against 125 C surface cap.",
                    "3. Doctor precursor at 1.240 ms; hood warm-start 198 C.",
                    "4. Race window [6.280, 6.760] ms opens on the yankee bus.",
                    "5. ir.hood.t 198 C at 6.280 ms (winner).",
                    "6. enc.doctor.nm 18.0 N/m at 6.498 ms (loser by 218 us).",
                    "7. Gate at 7.100 ms (winner + 820 us): MODIFY clamp 18.0 -> 12.4 N/m.",
                    "8. Clamp executes; next-sample surface 118 C < 125 cap.",
                    "9. At 22.400 ms stored adhesion still snaps a 40 mm coating ribbon; AE burst.",
                    "10. Grind/recoat 14 min (abort_s=840); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_doctor_load"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("doctor_N_m", 18.0),
                        ("yankee_steam_bar", 3.4),
                        ("crepe_ratio", 1.18),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("hood_C", 198.0),
                        ("surface_cap_C", 125.0),
                        ("predicted_unclamped_next_C", 128.0),
                        ("doctor_N_m", 18.0),
                        ("race_margin_us", 218),
                        ("combined_jitter_us", 72),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.0 N/m cruise: 198 C looks like a hood-air spike, not "
                "surface contact, and CN-3 crepe volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Hood IR 198 C won by 218 us, so the yankee surface is loading heat, not "
                "still cooling. Holding 18.0 N/m predicts next-sample 128 C > 125 cap. "
                "MODIFY: doctor 18.0 -> 12.4 N/m. Observed after clamp 118 C < 125. A full "
                "REJECT is not indicated: a sound crepe pass accepts 12.4 N/m.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "surface_C",
                            OrderedDict(
                                [
                                    ("cap", 125.0),
                                    ("observed_hood", 198.0),
                                    ("predicted_unclamped_next", 128.0),
                                    ("clamped_doctor_N_m", 12.4),
                                    ("observed_after_clamp", 118.0),
                                ]
                            ),
                        ),
                        (
                            "doctor_N_m",
                            OrderedDict(
                                [
                                    ("proposed", 18.0),
                                    ("clamped", 12.4),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 218),
                                    ("combined_jitter_us", 72),
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
            ("name", "clamped_doctor_load"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("doctor_N_m", 12.4),
                        ("yankee_steam_bar", 3.4),
                        ("crepe_ratio", 1.18),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: doctor 18.0 -> 12.4 N/m. Process-correct vs the 125 C surface "
                "cap. Coating-ribbon snap still occurs at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held yankee-surface skin at 118 C. At 22.400 ms stored "
                "adhesion in the coating still snapped a 40 mm ribbon. Clamp reduced dump energy; "
                "it did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("doctor", "clamp executed; peak 118 C < 125"),
                        ("coating_ribbon", "40 mm snap at 22.400 ms"),
                        ("repair", "14 min grind/recoat (abort_s=840)"),
                        ("mission", "CN-3 crepe pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither hood IR nor doctor predicted the adhesion charge; ae.ribbon is a new channel at 22.400 ms, 15.300 ms after the gate, still inside the 44 ms raster.",
                    "Delayed (abort_s=840): 14 min grind/recoat. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "14 min grind/recoat after a 40 mm coating-ribbon snap. Safety head -0.58 "
                "prices the split; task_progress stays +0.32 because the doctor clamp completed "
                "under the 125 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.hood.t (6.280 ms, 198 C)"),
                        ("loser", "enc.doctor.nm (6.498 ms, 18.0 N/m)"),
                        ("margin_us", 218),
                        (
                            "counterfactual_if_reversed",
                            "Doctor-first by < 218 us inside the 480 us window would have kept "
                            "18.0 N/m cruise; predicted next-sample 128 C would have exceeded "
                            "the 125 cap even without the adhesion charge. The MODIFY is still the "
                            "correct process. The snap is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms coating-ribbon snap (tick t_us=22400), inside "
                "the 44 ms raster. The correct MODIFY at 7.100 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=840 isolate tick.",
            ),
            ("delayed_surprise_s", 840.0),
            ("abort_s", 840),
        ]
    )
    spikes = [
        spike("enc.yankee.ctx", 1.240, 0.42),
        spike("ir.hood.t", 2.512, 0.61),
        spike("enc.doctor.nm", 3.880, 0.50),
        spike("ir.hood.t", 6.280, 1.31),
        spike("enc.doctor.nm", 6.498, 1.14),
        spike("ctrl.gate", 7.100, 0.98),
        spike("ir.hood.t", 8.620, 0.80),
        spike("enc.doctor.nm", 11.400, 0.62),
        spike("ctrl.gate", 15.200, 0.84),
        spike("ae.ribbon", 22.400, 1.46),
        spike("ae.ribbon", 24.180, 0.91),
        spike("enc.yankee.ctx", 31.200, 0.41),
        spike("ir.hood.t", 38.100, 0.53),
        spike("enc.doctor.nm", 42.600, 0.46),
    ]
    ras = raster_core(
        44,
        76,
        26,
        87,
        routing(
            "thalamic-relay.yankee-hood",
            "spikenaut.policy.doctor-clamp",
            [
                ("relay.ir.hood", "policy.doctor_clamp", 0.66),
                ("relay.enc.doctor", "policy.doctor_hold", 0.30),
                ("relay.ae.ribbon", "policy.doctor_clamp", -0.45),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at hood win (6.280 ms) opens a 50 ms "
            "eligibility trace that still covers the 22.400 ms coating-ribbon snap",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.48),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("doctor_clamp", 38, 0.50, 280.0, 5),
                    pop("doctor_hold", 38, 0.50, 52.0, 1),
                    pop("hood_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r40-217"),
            (
                "title",
                "Crepe-Nave CN-3 / Yankee-Y9: hood IR beats doctor by 218 us; correct "
                "MODIFY still eats an in-window coating-ribbon snap (partnered negative total -0.46)",
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
                    "44 ms raster. total -0.46 = 0.32 + -0.58 + -0.16 + 0.02 + -0.06. Named grind "
                    "isolate (abort_s=840) is not netted into task_progress.",
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
                        "partnered-negative-total",
                        "independent-lif-raster",
                        "sidecar-sim-only",
                        "in-window-world-charge",
                        "designed",
                    ],
                    "A critic can see the world-charge as a LIF burst inside the raster while "
                    "process heads stay honest. Credit assignment is spikes, not prose across a "
                    "14 min grind/recoat.",
                    2,
                ),
            ),
        ]
    )


def record_218():
    ticks = [
        tick(2328, 0.01, 0.05, 0.01, 0.01, 0.01),
        tick(5820, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(6000, 0.02, 0.07, 0.02, 0.02, 0.01),
        tick(6900, 0.03, 0.12, 0.04, 0.03, 0.02),
        tick(7320, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(540000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("tc.matte.ctx", 1.410, 0.43),
        spike("so2.offgas.pct", 2.328, 0.62),
        spike("ir.settler.t", 4.050, 0.49),
        spike("so2.offgas.pct", 5.820, 1.35),
        spike("ir.settler.t", 6.000, 1.12),
        spike("ctrl.gate", 6.900, 1.03),
        spike("so2.offgas.pct", 9.120, 0.77),
        spike("tc.matte.ctx", 13.400, 0.44),
        spike("ir.settler.t", 17.200, 0.58),
        spike("ctrl.gate", 24.100, 0.81),
        spike("so2.offgas.pct", 31.000, 0.54),
        spike("tc.matte.ctx", 37.800, 0.38),
        spike("ir.settler.t", 44.200, 0.46),
    ]
    excerpt = independent_excerpt(40218, 112, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Settler-S6 on Matte-Fell MF-2's HIL pad is frozen at 82 t/h while an SO2 "
                "NDIR cell reports 14.8 vol pct against a 12.0 vol pct offgas cap. Settler IR, "
                "lit by the pad lamp spectrum, still reads 1180 C apparent. SO2-first latches "
                "REJECT hold; IR-first would commit a 90 t/h raise on an under-read freeze risk.",
            ),
            ("domain", "copper-flash-smelter"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not raise feed unless offgas SO2 <= 12.0 vol pct; keep 82 t/h until the "
                "injected SO2 packet drops.",
            ),
            ("t0_us", 1756794621000218),
            ("gate_latency_us", 1080),
            ("race_window_us", 420),
            ("race_window_rel_ms", [5.820, 6.240]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "so2.offgas.pct 14.8 vol pct",
                                "ir.settler.t 1180 C apparent",
                            ],
                        ),
                        (
                            "semantics",
                            "SO2-first latches REJECT hold at 82 t/h; IR-first would commit "
                            "90 t/h on an apparent 1180 C freeze-risk under-read.",
                        ),
                        (
                            "window_derivation",
                            "420 us = one NDIR SO2 slot versus settler-IR integration on this "
                            "flash-smelter HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter ~60 us (SO2 28 + IR 32): 3.0x "
                            "over a 2.0x trust floor. Pad injects the lamp 110-150 us before the "
                            "SO2 cell (geometric lag, not a sensor fault); the apparent "
                            "1180 C packet is still the loser in this 420 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "NDIR SO2 cell, 5 kHz burst, 28 us jitter",
                    "settler IR pyrometer, 200 Hz, 32 us jitter",
                    "matte thermocouple (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("so2_cap_volpct", 12.0),
                        ("observed_so2_volpct", 14.8),
                        ("settler_apparent_C", 1180.0),
                        ("proposed_feed_t_h", 90.0),
                        ("current_feed_t_h", 82.0),
                        ("lamp_inject_lead_us", [110, 150]),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("pad", "Matte-Fell MF-2 settler mockup"),
                        ("injected", "SO2 impurity packet + settler-IR lamp spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop flash settler. Invented plant; not a live smelter.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Settler-S6 on the MF-2 HIL pad; feed raise 90 t/h armed.",
                    "2. Lamp injected 110-150 us before SO2 cell sees the impurity packet.",
                    "3. Matte precursor at 1.410 ms.",
                    "4. Race window [5.820, 6.240] ms.",
                    "5. so2.offgas.pct 14.8 vol pct at 5.820 ms (winner).",
                    "6. ir.settler.t 1180 C at 6.000 ms (loser by 180 us).",
                    "7. Gate at 6.900 ms: REJECT hold 82 t/h; do not raise to 90 t/h.",
                    "8. Settler remains over SO2 cap this cycle; feed raise held.",
                    "9. Flux recycle queued on the pad.",
                    "10. Delayed (abort_s=540): 9 min settler retune and lamp-spectrum retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "raise_feed_90"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 90.0),
                        ("hold", False),
                        ("ir_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("so2_volpct", 14.8),
                        ("so2_cap_volpct", 12.0),
                        ("settler_apparent_C", 1180.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 90 t/h because settler IR apparent 1180 C looks under a "
                "1240 C freeze floor, treating SO2 14.8 vol pct as a noisy sheath echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Offgas SO2 14.8 vol pct is over the 12.0 vol pct cap. Settler IR apparent "
                "1180 C is a HIL lamp under-read of freeze risk, not a clearance. REJECT: hold "
                "82 t/h; do not commit 90 t/h across the settler.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "so2_volpct",
                            OrderedDict(
                                [
                                    ("cap", 12.0),
                                    ("observed_so2", 14.8),
                                    ("settler_apparent_C", 1180.0),
                                ]
                            ),
                        ),
                        (
                            "feed_t_h",
                            OrderedDict(
                                [
                                    ("proposed", 90.0),
                                    ("executed", 82.0),
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
            ("name", "hold_for_so2_cap"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 82.0),
                        ("hold", True),
                        ("ir_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 82 t/h; 90 t/h raise cancelled. SO2 14.8 > 12.0 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Settler-S6 at 82 t/h. Settler over SO2 cap this cycle; "
                "feed raise held. Settler IR apparent was not treated as an SO2 clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held; speed 82 t/h"),
                        ("settler", "still over 12.0 vol pct this cycle"),
                        ("ir", "1180 C unused as clearance"),
                        ("mission", "raise deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: lamp was injected 110-150 us before the SO2 cell, yet SO2 still won the 420 us race.",
                    "Delayed (abort_s=540): pad policy update forbids treating settler IR apparent as an SO2 substitute after a 9 min settler retune.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "so2.offgas.pct (5.820 ms, 14.8 vol pct)"),
                        ("loser", "ir.settler.t (6.000 ms, 1180 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 180 us inside the 420 us window would have committed "
                            "90 t/h with SO2 14.8 > 12.0 cap. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6900),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (6.900 ms, tick 4) as the hold "
                "locks in over the illegal raise.",
            ),
            ("delayed_surprise_s", 540.0),
            ("abort_s", 540),
        ]
    )
    ras = raster_core(
        46,
        112,
        18,
        93,
        routing(
            "thalamic-relay.smelter-so2",
            "spikenaut.policy.feed-hold",
            [
                ("relay.so2.offgas", "policy.feed_hold", 0.69),
                ("relay.ir.settler", "policy.feed_raise", 0.27),
                ("relay.tc.matte", "policy.feed_hold", 0.11),
            ],
            "dopamine",
            0.09,
            "so2_stdp; DA at SO2 win (5.820 ms) tags feed_hold over feed_raise",
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
            ("decision_window_ms", 0.42),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("feed_hold", 52, 0.50, 240.0, 5),
                    pop("feed_raise", 52, 0.80, 12.0, 0),
                    pop("so2_veto", 32, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r40-218"),
            (
                "title",
                "Matte-Fell MF-2 HIL / Settler-S6: SO2 14.8 vol pct beats settler IR 1180 C; "
                "correct REJECT holds the 90 t/h raise",
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
                    "Correct REJECT. SO2 over cap; settler-IR lamp under-read unused as clearance. "
                    "total +0.78 = 0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "copper-flash-smelter",
                    [
                        "reject",
                        "hil-settler",
                        "so2-vs-ir",
                        "offgas-cap",
                        "hil",
                    ],
                    "Teaches that an SO2 NDIR over cap can beat a lamp-lit settler IR inside a "
                    "420 us window; reversing 180 us would have invented a raise on an illegal feed.",
                    3,
                ),
            ),
        ]
    )


def record_219():
    ticks = [
        tick(1536, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(3840, 0.10, 0.06, 0.04, 0.02, 0.01),
        tick(4008, 0.08, 0.05, 0.03, 0.02, 0.01),
        tick(4460, 0.12, 0.10, 0.05, 0.03, 0.02),
        tick(4720, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(300000000, 0.03, 0.03, 0.02, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.strip.ctx", 0.920, 0.40),
        spike("rtd.bath.t", 1.536, 0.58),
        spike("ir.dross.t", 2.410, 0.49),
        spike("rtd.bath.t", 3.840, 1.28),
        spike("ir.dross.t", 4.008, 1.10),
        spike("ctrl.gate", 4.460, 0.97),
        spike("rtd.bath.t", 6.200, 0.74),
        spike("enc.strip.ctx", 11.400, 0.43),
        spike("ir.dross.t", 16.800, 0.56),
        spike("ctrl.gate", 21.200, 0.80),
        spike("rtd.bath.t", 26.400, 0.52),
        spike("ir.dross.t", 29.100, 0.45),
    ]
    excerpt = independent_excerpt(40219, 56, 30000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Kettle-Z11 in the Spelter-Holt SH-5 simulated bath already holds 456 C when "
                "a NIR dross glint prints 512 C. Published kettle cap is 480 C on the bath RTD; "
                "the glint is lighting, not cake. Bath-first should ACCEPT the already-legal "
                "1.8 m/min strip.",
            ),
            ("domain", "galvanize-kettle"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold 1.8 m/min strip on Z11, keep bath RTD < 480 C cap, and finish the 5 min "
                "survey hold.",
            ),
            ("t0_us", 1756794621000219),
            ("gate_latency_us", 620),
            ("race_window_us", 260),
            ("race_window_rel_ms", [3.840, 4.100]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bath.t 456 C live",
                                "ir.dross.t 512 C lighting glint",
                            ],
                        ),
                        (
                            "semantics",
                            "Bath-first should ACCEPT 1.8 m/min (456 C < 480 C cap). Glint-first "
                            "would only delay confirmation of the same legal bath temperature.",
                        ),
                        (
                            "window_derivation",
                            "260 us = one bath RTD slot versus the NIR dross publisher on this "
                            "simulated kettle bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 168 us vs combined jitter 52 us (bath 24 + dross 28): 3.2x over "
                            "a 2.0x trust floor. Order is correctly bath-first. The glint is lighting, "
                            "not a dross cake.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bath RTD, 4 kHz, 24 us jitter",
                    "NIR dross imager, 2 kHz, 28 us jitter",
                    "strip-speed encoder (context)",
                    "kettle wall TC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bath_C", 456.0),
                        ("cap_C", 480.0),
                        ("dross_glint_C", 512.0),
                        ("proposed_m_min", 1.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Kettle-Z11 indexed on Spelter-Holt SH-5 simulated bath; 1.8 m/min armed.",
                    "2. Published bath cap 480 C; NIR 512 C is a lighting glint.",
                    "3. Strip precursor at 0.920 ms.",
                    "4. Race window [3.840, 4.100] ms.",
                    "5. rtd.bath.t 456 C at 3.840 ms (winner).",
                    "6. ir.dross.t 512 C at 4.008 ms (loser by 168 us).",
                    "7. Gate at 4.460 ms: ACCEPT 1.8 m/min already legal.",
                    "8. Bath stays 456 C under 480 C cap.",
                    "9. Glint unused as a hold.",
                    "10. Delayed (survey_hold_s=300): 5 min dross-camera lighting survey.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "strip_18_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("strip_m_min", 1.8),
                        ("bath_C", 456.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bath_C", 456.0),
                        ("cap_C", 480.0),
                        ("dross_glint_C", 512.0),
                        ("race_margin_us", 168),
                        ("combined_jitter_us", 52),
                        ("survey_hold_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.8 m/min because bath RTD 456 C is 24 C under the "
                "published 480 C cap and the 512 C NIR is a lighting glint, not cake.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bath RTD 456 C is under the 480 C kettle cap. NIR 512 C is lighting, not "
                "dross cake. ACCEPT: leave 1.8 m/min.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bath_C",
                            OrderedDict(
                                [
                                    ("cap", 480.0),
                                    ("observed", 456.0),
                                    ("dross_glint", 512.0),
                                    ("executed_m_min", 1.8),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 168),
                                    ("combined_jitter_us", 52),
                                    ("ratio", 3.23),
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
            ("name", "strip_18_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("strip_m_min", 1.8),
                        ("bath_C", 456.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: strip 1.8 m/min unchanged. Routing relay.rtd.bath -> policy.strip_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left Z11 at 1.8 m/min. Bath 456 C stayed under the 480 C cap. "
                "NIR glint unused as a hold.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("strip", "1.8 m/min held legal"),
                        ("bath_C", "still 456 C, under 480 C cap"),
                        ("dross", "512 C glint unused"),
                        ("mission", "survey hold 5 min"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "NIR 512 C is a lighting glint on simulated dross, not a cake temperature.",
                    "Delayed (survey_hold_s=300): 5 min camera lighting survey confirms the glint class.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bath.t (3.840 ms, 456 C)"),
                        ("loser", "ir.dross.t (4.008 ms, 512 C glint)"),
                        ("margin_us", 168),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 168 us would still show bath 456 C < 480 C. A "
                            "correct gate ACCEPTs either way; reversing 168 us would have invented "
                            "a hold on an already-legal strip.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4460),
            (
                "reward_inflection_note",
                "Task and safety step up at the ACCEPT gate (4.460 ms, tick 4).",
            ),
            ("delayed_surprise_s", 300.0),
            ("survey_hold_s", 300),
        ]
    )
    ras = raster_core(
        30,
        56,
        38,
        64,
        routing(
            "relay.rtd.bath",
            "policy.strip_go",
            [
                ("relay.rtd.bath", "policy.strip_go", 0.62),
                ("relay.ir.dross", "policy.glint_hold", 0.28),
                ("relay.enc.strip", "policy.strip_go", 0.14),
            ],
            "serotonin",
            0.16,
            "pre_post_stdp; 5-HT at bath win (3.840 ms) opens 160 ms eligibility covering the 4.460 ms accept",
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
            ("decision_window_ms", 0.26),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("strip_go", 32, 0.50, 280.0, 2),
                    pop("glint_hold", 32, 0.50, 24.0, 0),
                    pop("cake_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r40-219"),
            (
                "title",
                "Spelter-Holt SH-5 / Kettle-Z11: bath 456 C beats NIR dross glint; "
                "correct ACCEPT of an already-legal 1.8 m/min (total +1.10)",
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
                    "Correct ACCEPT. Bath 456 C < 480; NIR glint is lighting, not cake. "
                    "total +1.10 = 0.44 + 0.32 + 0.18 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "galvanize-kettle",
                    [
                        "accept",
                        "simulated-lighting",
                        "bath-vs-nir",
                        "already-legal",
                        "simulated",
                    ],
                    "Teaches that a NIR dross lighting glint can lose to a legal bath RTD "
                    "inside a 260 us window; reversing 168 us would have invented a hold on an "
                    "already-legal strip.",
                    4,
                ),
            ),
        ]
    )


def record_220():
    ticks = [
        tick(1688, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(4220, 0.10, 0.07, 0.04, 0.02, 0.01),
        tick(4400, 0.08, 0.06, 0.03, 0.02, 0.01),
        tick(4900, 0.12, 0.10, 0.06, 0.04, 0.03),
        tick(5120, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(360000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("pt.argon.ctx", 0.880, 0.40),
        spike("tc.furnace.t", 1.688, 0.59),
        spike("pt.jacket.bar", 2.540, 0.50),
        spike("tc.furnace.t", 4.220, 1.29),
        spike("pt.jacket.bar", 4.400, 1.11),
        spike("ctrl.gate", 4.900, 0.98),
        spike("tc.furnace.t", 7.110, 0.76),
        spike("pt.jacket.bar", 10.200, 0.61),
        spike("ctrl.gate", 14.600, 0.83),
        spike("pt.argon.ctx", 18.400, 0.42),
        spike("tc.furnace.t", 22.100, 0.54),
        spike("pt.jacket.bar", 23.600, 0.46),
    ]
    excerpt = independent_excerpt(40220, 64, 24000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Vessel-H8 at Isostat-Wold IW-4 is already soaking at 1030 bar when furnace "
                "TC 1120 C races jacket PT 48 bar. Published furnace cap is 1160 C and jacket "
                "cap is 55 bar; the soak is already legal. Furnace-first should ACCEPT.",
            ),
            ("domain", "hot-isostatic-press"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 1030 bar / 1120 C soak on H8, keep furnace < 1160 C and jacket < 55 bar, "
                "and finish the 6 min resequence.",
            ),
            ("t0_us", 1756794621000220),
            ("gate_latency_us", 680),
            ("race_window_us", 220),
            ("race_window_rel_ms", [4.220, 4.440]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.furnace.t 1120 C",
                                "pt.jacket.bar 48 bar",
                            ],
                        ),
                        (
                            "semantics",
                            "Furnace-first should ACCEPT 1030 bar soak (1120 C < 1160 C cap). "
                            "Jacket-first would only delay confirmation of the same legal soak.",
                        ),
                        (
                            "window_derivation",
                            "220 us = one furnace TC sample versus jacket PT on this HIP bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 56 us (furnace 26 + jacket 30): 3.2x over "
                            "a 2.0x trust floor. Order is correctly furnace-first. Both channels are "
                            "under cap; the soak is already legal.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "furnace TC, 4 kHz, 26 us jitter",
                    "jacket PT, 2 kHz, 30 us jitter",
                    "argon supply PT (context)",
                    "hearth encoder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("furnace_C", 1120.0),
                        ("furnace_cap_C", 1160.0),
                        ("jacket_bar", 48.0),
                        ("jacket_cap_bar", 55.0),
                        ("proposed_bar", 1030.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Vessel-H8 indexed on Isostat-Wold IW-4; 1030 bar / 1120 C soak armed.",
                    "2. Published furnace cap 1160 C; jacket cap 55 bar.",
                    "3. Argon precursor at 0.880 ms.",
                    "4. Race window [4.220, 4.440] ms.",
                    "5. tc.furnace.t 1120 C at 4.220 ms (winner).",
                    "6. pt.jacket.bar 48 bar at 4.400 ms (loser by 180 us).",
                    "7. Gate at 4.900 ms: ACCEPT 1030 bar already legal.",
                    "8. Furnace stays 1120 C under 1160 C; jacket 48 bar under 55 bar.",
                    "9. Soak continues.",
                    "10. Delayed (reseq_s=360): 6 min next-heat resequence.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hip_soak_1030"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pressure_bar", 1030.0),
                        ("furnace_C", 1120.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("furnace_C", 1120.0),
                        ("furnace_cap_C", 1160.0),
                        ("jacket_bar", 48.0),
                        ("jacket_cap_bar", 55.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 56),
                        ("reseq_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1030 bar soak because furnace 1120 C is 40 C under the "
                "1160 C cap and jacket 48 bar is 7 bar under the 55 bar cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Furnace 1120 C is under the 1160 C cap and jacket 48 bar is under the 55 bar "
                "cap. ACCEPT: leave 1030 bar soak.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "furnace_C",
                            OrderedDict(
                                [
                                    ("cap", 1160.0),
                                    ("observed", 1120.0),
                                    ("executed_bar", 1030.0),
                                ]
                            ),
                        ),
                        (
                            "jacket_bar",
                            OrderedDict(
                                [
                                    ("cap", 55.0),
                                    ("observed", 48.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 56),
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
            ("name", "hip_soak_1030"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pressure_bar", 1030.0),
                        ("furnace_C", 1120.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: 1030 bar soak unchanged. Routing relay.tc.furnace -> policy.soak_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left H8 at 1030 bar / 1120 C. Furnace and jacket stayed under "
                "cap. Soak continues into the 6 min resequence.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("vessel", "1030 bar soak held legal"),
                        ("furnace_C", "still 1120 C, under 1160 C cap"),
                        ("jacket_bar", "still 48 bar, under 55 bar cap"),
                        ("mission", "resequence 6 min"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Jacket 48 bar lost the race but was never a trip; both channels under cap.",
                    "Delayed (reseq_s=360): 6 min next-heat resequence after the soak window.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.furnace.t (4.220 ms, 1120 C)"),
                        ("loser", "pt.jacket.bar (4.400 ms, 48 bar)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Jacket-first by < 180 us would still show furnace 1120 C < 1160 C. A "
                            "correct gate ACCEPTs either way.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4900),
            (
                "reward_inflection_note",
                "Task and safety step up at the ACCEPT gate (4.900 ms, tick 4).",
            ),
            ("delayed_surprise_s", 360.0),
            ("reseq_s", 360),
        ]
    )
    ras = raster_core(
        24,
        64,
        34,
        52,
        routing(
            "relay.tc.furnace",
            "policy.soak_go",
            [
                ("relay.tc.furnace", "policy.soak_go", 0.64),
                ("relay.pt.jacket", "policy.jacket_hold", 0.24),
                ("relay.pt.argon", "policy.soak_go", 0.12),
            ],
            "histamine",
            0.12,
            "pre_post_stdp; histamine at furnace win (4.220 ms) opens 120 ms eligibility covering the 4.900 ms accept",
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
            ("decision_window_ms", 0.22),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("soak_go", 36, 0.50, 320.0, 3),
                    pop("jacket_hold", 36, 0.50, 18.0, 0),
                    pop("overtemp_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r40-220"),
            (
                "title",
                "Isostat-Wold IW-4 / Vessel-H8: furnace 1120 C beats jacket 48 bar; "
                "correct ACCEPT of an already-legal 1030 bar soak (total +1.20)",
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
                    "Correct ACCEPT. Furnace 1120 C < 1160; jacket 48 bar < 55. "
                    "total +1.20 = 0.46 + 0.34 + 0.20 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "hot-isostatic-press",
                    [
                        "accept",
                        "already-legal",
                        "furnace-vs-jacket",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches that a mid-soak furnace under cap can confirm an already-legal HIP "
                    "without a jacket hitch becoming a hold.",
                    5,
                ),
            ),
        ]
    )
