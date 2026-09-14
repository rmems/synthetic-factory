def record_361():
    excerpt, extra = lif_361_excerpt()
    ticks = [
        tick(2080, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5200, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5380, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5920, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22400, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(840000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    spikes = [
        spike("enc.kiln.rpm", 1.160, 0.41),
        spike("tc.bed.C", 2.080, 0.58),
        spike("enc.kiln.rpm", 3.400, 0.50),
        spike("tc.bed.C", 5.200, 1.31),
        spike("enc.kiln.rpm", 5.380, 1.12),
        spike("ctrl.gate", 5.920, 0.97),
        spike("tc.bed.C", 8.200, 0.82),
        spike("enc.kiln.rpm", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.tire.crack", 22.400, 1.48),
        spike("ae.tire.crack", 24.200, 0.93),
        spike("enc.kiln.rpm", 30.200, 0.40),
        spike("tc.bed.C", 36.400, 0.55),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Rotary-kiln Eu2O3 charge K-9 at Europia-Wath EW-6 already prints bed-mid 892 C "
                "against an 840 C tire-cap while the rotation encoder still sits a legal 1.80 rpm "
                "under 2.40. Bed-first clamps rotation 1.80 -> 0.90 rpm; encoder-first would keep "
                "cruise because 1.80 rpm is still under the 2.40 rpm drive cap. A kiln-tire crack "
                "already seated on the riding ring does not appear on bed or rpm until the AE dump.",
            ),
            ("domain", "europium-oxide-calciner"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep K-9 bed <= 840 C and finish the Eu2O3 calcine without dumping grog through "
                "a cracked riding-ring tire.",
            ),
            ("t0_us", 1756857300000361),
            ("gate_latency_us", 720),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.200, 5.560]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.bed.C 892 over 840 cap",
                                "enc.kiln.rpm 1.80 with drive 1.80 under 2.40",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first latches rotation clamp 1.80 -> 0.90 rpm; encoder-first keeps "
                            "1.80 rpm on a 'still under drive-rpm cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one bed-well TC slot versus the kiln-rotation encoder publisher "
                            "on this Eu2O3 calciner bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (TC 28 + rpm 34): 2.90x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 1.80 rpm; predicted next-sample 856 C > 840 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed-well TC, 2 kHz, 28 us jitter",
                    "kiln rotation encoder, 1 kHz, 34 us jitter",
                    "riding-ring AE puck (context)",
                    "Eu2O3 feed tach (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 840.0),
                        ("observed_bed_C", 892.0),
                        ("kiln_rpm", 1.80),
                        ("drive_cap_rpm", 2.40),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. K-9 indexed on Europia-Wath EW-6; rotation 1.80 rpm; bed 892 C.",
                    "2. Drive 1.80 rpm under 2.40; calcine armed.",
                    "3. Encoder precursor at 1.160 ms.",
                    "4. Race window [5.200, 5.560] ms.",
                    "5. tc.bed.C 892 at 5.200 ms (winner).",
                    "6. enc.kiln.rpm 1.80 at 5.380 ms (loser by 180 us).",
                    "7. Gate at 5.920 ms: MODIFY clamp 1.80 -> 0.90 rpm.",
                    "8. After clamp bed 828 C <= 840; drive still 0.90 rpm.",
                    "9. At 22.400 ms a kiln-tire crack dumps 0.3 t grog.",
                    "10. 14 min kiln isolate (abort_s=840); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_kiln_rotation"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("kiln_rpm", 1.80),
                        ("bed_C", 892.0),
                        ("drive_rpm", 1.80),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 892.0),
                        ("bed_cap_C", 840.0),
                        ("predicted_unclamped_next_C", 856.0),
                        ("kiln_rpm", 1.80),
                        ("drive_cap_rpm", 2.40),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.80 rpm because the drive is under 2.40, treating the "
                "892 C bed as a still-wet charge rather than a tire-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 892 C won by 180 us, so the kiln is over the 840 C tire cap, not still a "
                "drive-rpm story. Holding 1.80 rpm predicts next-sample 856 > 840. MODIFY: rotation "
                "1.80 -> 0.90 rpm. Observed after clamp 828 C <= 840. A full REJECT is not indicated: "
                "a clean calcine accepts 0.90 rpm.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 840.0),
                                    ("observed", 892.0),
                                    ("predicted_unclamped_next", 856.0),
                                    ("clamped_kiln_rpm", 0.90),
                                    ("observed_after_clamp", 828.0),
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
            ("name", "clamped_kiln_rotation"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("kiln_rpm", 0.90),
                        ("bed_C", 828.0),
                        ("drive_rpm", 0.90),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: rotation 1.80 -> 0.90 rpm. Process-correct vs the 840 C tire cap. "
                "Riding ring still cracks at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held bed at 828 C. At 22.400 ms a kiln-tire crack "
                "already seated on the riding ring dumped 0.3 t of Eu2O3 grog. Clamp reduced dump "
                "energy; it did not prevent the crack. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bed", "clamp executed; peak 828 C <= 840 cap"),
                        ("tire", "cracked at 22.400 ms; 0.3 t grog"),
                        ("repair", "14 min kiln isolate (abort_s=840)"),
                        ("mission", "EW-6 calcine incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither bed TC nor rotation encoder predicted the seated kiln-tire crack; ae.tire.crack is a new channel at 22.400 ms, 16.480 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=840): 14 min kiln isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "14 min kiln isolate after the riding-ring crack. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the rpm clamp completed under the 840 C "
                "cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bed.C (5.200 ms, 892 C)"),
                        ("loser", "enc.kiln.rpm (5.380 ms, 1.80 rpm)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Rpm-first by < 180 us inside the 360 us window would have kept "
                            "1.80 rpm; predicted next-sample 856 C would have missed the 840 "
                            "cap even without the crack. The MODIFY is still the correct "
                            "process. The crack is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms kiln-tire crack (tick t_us=22400), inside the 42 ms "
                "raster. The correct MODIFY at 5.920 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=840 isolation tick.",
            ),
            ("delayed_surprise_s", 840),
        ]
    )
    dw = 0.36
    ras = raster_core(
        42,
        76,
        24,
        77,
        routing(
            "thalamic-relay.eu-bed",
            "spikenaut.policy.rpm-clamp",
            [
                ("relay.tc.bed", "policy.rpm_clamp", 0.68),
                ("relay.enc.kiln", "policy.rpm_hold", 0.29),
                ("relay.ae.tire", "policy.rpm_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at bed win (5.200 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.400 ms kiln-tire crack",
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
                    pop_budget("rpm_clamp", 50, 0.50, 220.0, dw),
                    pop_budget("rpm_hold", 40, 0.80, 50.0, dw),
                    pop("tire_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r73-361"),
            (
                "title",
                "Europia-Wath EW-6 / Kiln K-9: bed 892 C beats kiln rpm by 180 us; "
                "correct MODIFY still eats an in-window kiln-tire crack (partnered negative "
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
                    "kiln isolate (abort_s=840) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "europium-oxide-calciner",
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
                    "14 min kiln isolate.",
                    1,
                ),
            ),
        ]
    )


def record_362():
    ticks = [
        tick(2192, 0.02, -0.03, -0.02, -0.01, 0.01),
        tick(5480, 0.03, -0.04, -0.03, -0.02, 0.01),
        tick(5640, 0.02, -0.03, -0.03, -0.02, 0.01),
        tick(6120, -0.24, -0.10, -0.06, -0.03, 0.02),
        tick(6440, -0.04, -0.03, -0.02, -0.01, 0.01),
        tick(540000000, -0.01, -0.01, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("tc.jacket.C", 1.100, 0.42),
        spike("tt.shower.C", 2.192, 0.57),
        spike("tc.jacket.C", 3.400, 0.49),
        spike("tt.shower.C", 5.480, 1.30),
        spike("tc.jacket.C", 5.640, 1.11),
        spike("ctrl.gate", 6.120, 0.96),
        spike("tt.shower.C", 8.400, 0.80),
        spike("tc.jacket.C", 10.200, 0.63),
        spike("ctrl.gate", 12.400, 0.84),
        spike("tt.shower.C", 16.400, 0.41),
        spike("tc.jacket.C", 22.100, 0.54),
        spike("tt.shower.C", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(73362, 96, 28000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Showerhead TT on Molyfluor-Staith MS-5 / Reactor R-4 sits at 186.0 C against a "
                "160.0 C MoF6 deposition cap while cascade master MF6 is 28.0 sccm and the slave "
                "jacket is already a legal 42 C under an 80 C inner cap. Live-master-first should "
                "cut MF6 28.0 -> 12.0 sccm; a weak supervisor binds the inner jacket loop and trims "
                "slave SP 42 -> 18 C, leaving MF6 at 28.0 sccm.",
            ),
            ("domain", "molybdenum-hexafluoride-cvd"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep R-4 showerhead <= 160 C, leave slave jacket at the planned 42 C, "
                "and bind the live master TT rather than the inner cascade loop.",
            ),
            ("t0_us", 1756857301000362),
            ("gate_latency_us", 640),
            ("race_window_us", 320),
            ("race_window_rel_ms", [5.480, 5.800]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tt.shower.C 186.0 over 160.0 cap",
                                "tc.jacket.C 42 leftover cascade-slave SP",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-master-first should latch a timely MF6 cut 28.0 -> 12.0 sccm; "
                            "slave-loop bind is a false 'already on the inner loop' trim of jacket "
                            "42 -> 18 C that leaves master MF6 open.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one live-master TT slot versus the leftover slave-jacket "
                            "publisher on this MoF6 CVD PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 60 us (live 28 + slave 32). Order is "
                            "correctly live-master-first. The error is which cascade leg the cut "
                            "is spent on, not the magnitude of the live showerhead.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live showerhead TT, 2 kHz, 28 us jitter, tag=R4_TT.MASTER",
                    "cascade slave jacket TC, 1 kHz, 32 us jitter, C=42",
                    "MF6 MFC (context)",
                    "chamber PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_C", 160.0),
                        ("live_C", 186.0),
                        ("master_sccm", 28.0),
                        ("slave_jacket_C", 42.0),
                        ("slave_inner_cap_C", 80.0),
                        ("cascade_both_live", True),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. R-4 LIVE already depositing; showerhead 186.0 C; MF6 28.0 sccm; jacket 42 C.",
                    "2. Both cascade legs LIVE; inner loop is the slave jacket.",
                    "3. Slave-jacket precursor at 1.100 ms.",
                    "4. Race window [5.480, 5.800] ms.",
                    "5. tt.shower.C 186.0 at 5.480 ms (winner).",
                    "6. tc.jacket.C 42 at 5.640 ms (loser by 160 us).",
                    "7. Gate at 6.120 ms: WRONG-MODIFY binds the slave loop.",
                    "8. Jacket SP 42 -> 18 C; MF6 left 28.0; live showerhead stays 184.2 C.",
                    "9. Off-spec MoF6 film; master MV was the legal cut.",
                    "10. Delayed (abort_s=540): 9 min off-spec cycle while R-4 is re-pumped.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_cascade_mof6"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("master_sccm", 28.0),
                        ("slave_jacket_C", 42.0),
                        ("cascade_leg", "none"),
                        ("chamber_Pa", 180.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 186.0),
                        ("cap_C", 160.0),
                        ("master_sccm", 28.0),
                        ("slave_jacket_C", 42.0),
                        ("slave_inner_cap_C", 80.0),
                        ("cascade_both_live", True),
                        ("t_gate_us", 6120),
                        ("correct_master_sccm", 12.0),
                        ("correct_slave_jacket_C", 42.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 60),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 28.0 sccm master MF6: leftover slave jacket 42 C "
                "looks like the active inner loop, so the 186.0 C live TT is treated as a shadow of the jacket.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Showerhead 186.0 C exceeds the 160.0 C cap (true). Trim the highlighted slave "
                "jacket 42 -> 18 C because the inner loop is the faceplate SP. Leave MF6 "
                "at 28.0 sccm.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "showerhead_C",
                            OrderedDict(
                                [
                                    ("cap", 160.0),
                                    ("live", 186.0),
                                    ("executed_slave_jacket_C", 18.0),
                                    ("executed_master_sccm", 28.0),
                                    ("correct_master_sccm", 12.0),
                                ]
                            ),
                        ),
                        (
                            "cascade_bind",
                            OrderedDict(
                                [
                                    ("t_gate_us", 6120),
                                    ("cascade_leg", "slave"),
                                    ("cascade_both_live", True),
                                    ("wrong_leg", True),
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
            ("name", "slave_trim_wrong_leg"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("master_sccm", 28.0),
                        ("slave_jacket_C", 18.0),
                        ("cascade_leg", "slave"),
                        ("chamber_Pa", 180.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / cascade-slave-as-master): jacket SP 42 -> 18 C while live "
                "186.0 C stays over 160. Routing relay.tt.master -> policy.slave_trim; no positive "
                "weight to policy.master_cut.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY spent the live showerhead win on the slave jacket. Live 186.0 C was over "
                "the 160.0 C cap at t_gate; MF6 stayed 28.0 sccm. Peak 184.2 C kept R-4 off-spec. "
                "9 min re-pump (abort_s=540). Correct gate was MODIFY master 28.0 -> 12.0 sccm at "
                "t_gate_us=6120, leaving jacket at 42 C.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live_still", "R-4 master left 28.0 sccm; peak 184.2 > 160 cap"),
                        ("cascade", "slave jacket 42 -> 18; master unbound"),
                        ("dump", "9 min MoF6 re-pump, R-4 hold"),
                        ("mission", "film cut deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-master-first was the correct order and the showerhead number was over cap; the MODIFY spent that win on a slave-loop trim.",
                    "Delayed (abort_s=540): MS-5 holds 9 min while R-4 is re-pumped; next batch 11 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY master MF6 28.0 -> 12.0 sccm at t_gate_us=6120; leave slave jacket at 42 C; bind live showerhead TT.",
                        ),
                        ("correct_leg", "master"),
                        ("wrong_leg", "slave"),
                        ("t_gate_us", 6120),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("slave_jacket_C", 18.0),
                                    ("master_sccm", 28.0),
                                    ("cascade_leg", "slave"),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "9 min off-spec MoF6 cycle (task/efficiency); live showerhead stayed 184.2 C while the cut was spent on the inner cascade loop (safety near-miss of a correct-magnitude wrong-leg clamp).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tt.shower.C (5.480 ms, 186.0 C LIVE)"),
                        ("loser", "tc.jacket.C (5.640 ms, 42 C leftover slave SP)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Slave-first by < 160 us would still be 186.0 C over the 160.0 C "
                            "cap; a correct gate binds tt.shower.C to policy.master_cut at t_gate "
                            "either way. The wrong MODIFY spent the live win on the slave loop.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6120),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the slave-loop bind (6.120 ms, tick 4). "
                "The 9 min re-pump is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 540),
        ]
    )
    dw = 0.32
    ras = raster_core(
        28,
        96,
        32,
        86,
        routing(
            "thalamic-relay.mof6-cascade",
            "spikenaut.policy.slave-trim",
            [
                ("relay.tt.master", "policy.slave_trim", 0.74),
                ("relay.tc.jacket", "policy.slave_trim", 0.21),
            ],
            "acetylcholine",
            0.05,
            "cascade_leg_stdp; ACh tags the (wrong) slave_trim bind at the live showerhead win",
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
            ("decision_window_ms", dw),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("slave_trim", 48, 0.45, 300.0, dw),
                    pop("master_cut", 48, 0.90),
                    pop("shower_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r73-362"),
            (
                "title",
                "WRONG-MODIFY at Molyfluor-Staith MS-5 / Reactor R-4: live 186.0 C read correctly; "
                "cut spent on slave jacket while master MF6 stays 28.0 sccm (cascade-slave-as-master)",
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
                    "Wrong-modify / cascade-slave-as-master. Sidecar arithmetic 186.0 > 160.0 "
                    "on live is true; MODIFY bound to slave_trim. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "molybdenum-hexafluoride-cvd",
                    [
                        "modify",
                        "wrong-gate",
                        "cascade-slave-as-master",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live-first race can still be a wrong gate "
                    "when the MODIFY spends the cut on the cascade slave. Convictable from "
                    "live_C > cap_C, cascade_leg=slave, and routing without MoF6 kinetics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_363():
    ticks = [
        tick(1968, 0.01, 0.06, 0.01, 0.01, 0.01),
        tick(4920, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5200, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(6020, 0.04, 0.14, 0.04, 0.04, 0.02),
        tick(6500, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.pull", 0.980, 0.41),
        spike("ae.melt.pps", 1.968, 0.57),
        spike("enc.pull", 3.200, 0.49),
        spike("ae.melt.pps", 4.920, 1.35),
        spike("enc.pull", 5.200, 1.12),
        spike("ctrl.gate", 6.020, 0.98),
        spike("ae.melt.pps", 8.800, 0.81),
        spike("enc.pull", 12.400, 0.62),
        spike("ctrl.gate", 16.200, 0.84),
        spike("ae.melt.pps", 24.100, 0.52),
        spike("enc.pull", 32.400, 0.39),
        spike("ae.melt.pps", 40.200, 0.44),
        spike("ctrl.gate", 44.800, 0.70),
    ]
    excerpt = independent_excerpt(73363, 112, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "On the Antimonide-Croft AC-HIL GaSb puller, melt AE on P-6 is bursting at 56 pps "
                "against a 16 pps distress trip while the pull encoder remains 1.40 mm/min, 0.60 shy "
                "of the 2.00 mm/min raise permit. AE-first holds raise; encoder-first would lift "
                "1.40 -> 1.90 mm/min because the seed looks quiet. The HIL melt mockup is the "
                "authority, not the boule-floor recipe.",
            ),
            ("domain", "gallium-antimonide-czochralski"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep P-6 from raising pull into a melt-growl while encoder speed remains under "
                "its own raise permit.",
            ),
            ("t0_us", 1756857302000363),
            ("gate_latency_us", 1100),
            ("race_window_us", 480),
            ("race_window_rel_ms", [4.920, 5.400]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.melt.pps 56 over 16 cap",
                                "enc.pull 1.40 under 2.00 raise permit",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; encoder-first raises pull 1.40 -> 1.90 mm/min on a "
                            "'seed still quiet' model.",
                        ),
                        (
                            "window_derivation",
                            "480 us = one AE puck slot versus the pull-encoder publisher on this "
                            "HIL GaSb puller bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 280 us vs combined jitter 58 us (AE 26 + encoder 32): 4.83x over "
                            "a 2.0x trust floor. Reversing order by < 280 us inside the 480 us "
                            "window would have raised pull into a melt growl.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "melt AE puck, 50 kHz, 26 us jitter",
                    "pull encoder, 1 kHz, 32 us jitter",
                    "seed TC (context)",
                    "crucible RPM (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 16.0),
                        ("observed_ae_pps", 56.0),
                        ("pull_mm_min", 1.40),
                        ("pull_permit_mm_min", 2.00),
                        ("proposed_pull_mm_min", 1.90),
                        ("held_pull_mm_min", 1.40),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. P-6 HIL indexed; 1.90 mm/min pull raise armed.",
                    "2. Encoder 1.40 mm/min under 2.00; AE 56 pps over 16.",
                    "3. Encoder precursor at 0.980 ms.",
                    "4. Race window [4.920, 5.400] ms.",
                    "5. ae.melt.pps 56 at 4.920 ms (winner).",
                    "6. enc.pull 1.40 at 5.200 ms (loser by 280 us).",
                    "7. Gate at 6.020 ms: REJECT hold, do not raise.",
                    "8. Pull left 1.40 mm/min; encoder left under permit.",
                    "9. Melt inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min GaSb reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "raise_pull"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pull_mm_min", 1.90),
                        ("hold", False),
                        ("seed_C", 712.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 56.0),
                        ("ae_cap_pps", 16.0),
                        ("pull_mm_min", 1.40),
                        ("pull_permit_mm_min", 2.00),
                        ("race_margin_us", 280),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.90 mm/min pull because encoder 1.40 is under 2.00, treating the "
                "56 pps AE as crucible hash rather than a melt growl.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Melt AE 56 pps won by 280 us, so the boule is growling, not still a "
                "pull-encoder story. Encoder 1.40 mm/min is under 2.00 and does not authorize a raise. "
                "REJECT: hold pull 1.90 -> 1.40 mm/min. A MODIFY that only trims rotation would leave the growl.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ae_pps",
                            OrderedDict(
                                [
                                    ("cap", 16.0),
                                    ("observed", 56.0),
                                    ("executed_pull_mm_min", 1.40),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 280),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 4.83),
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
            ("name", "hold_pull"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pull_mm_min", 1.40),
                        ("hold", True),
                        ("seed_C", 712.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: pull 1.90 -> 1.40 mm/min hold. Encoder left under its own permit.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held P-6. AE 56 pps beat pull encoder 1.40 mm/min by 280 us. Encoder was "
                "legal; the melt was not. 8 min GaSb reset (abort_s=480) is delayed survey, "
                "not a process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("pull", "held at 1.40 mm/min"),
                        ("encoder", "left 1.40 < 2.00 permit"),
                        ("melt", "8 min GaSb reset (abort_s=480)"),
                        ("mission", "HIL pull raise not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Pull encoder never crossed its permit; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min GaSb reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.melt.pps (4.920 ms, 56 pps)"),
                        ("loser", "enc.pull (5.200 ms, 1.40 mm/min)"),
                        ("margin_us", 280),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 280 us inside the 480 us window would have raised "
                            "pull into a melt growl. The REJECT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6020),
            (
                "reward_inflection_note",
                "Safety rises at the correct REJECT (6.020 ms, tick 4). The 8 min reset is delayed "
                "surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    dw = 0.48
    ras = raster_core(
        46,
        112,
        20,
        103,
        routing(
            "thalamic-relay.gasb-ae",
            "spikenaut.policy.pull-hold",
            [
                ("relay.ae.melt", "policy.pull_hold", 0.71),
                ("relay.enc.pull", "policy.pull_raise", 0.24),
            ],
            "dopamine",
            0.15,
            "hold_stdp; DA tags the pull_hold bind at the melt-AE win",
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
                    pop_budget("pull_hold", 70, 0.48, 180.0, dw),
                    pop("pull_raise", 50, 0.85),
                    pop("ae_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r73-363"),
            (
                "title",
                "Antimonide-Croft AC-HIL / Puller P-6: melt AE beats pull encoder by 280 us; "
                "REJECT hold-pull, do not raise",
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
                    "Correct REJECT. AE 56 pps > 16 cap; encoder 1.40 mm/min legal. "
                    "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "gallium-antimonide-czochralski",
                    [
                        "reject",
                        "hil",
                        "melt-ae",
                        "encoder-underread",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches AE-vs-encoder order on a HIL GaSb puller: routing.table[0] to "
                    "policy.pull_hold with pull encoder as the losing raise.",
                    3,
                ),
            ),
        ]
    )


def record_364():
    ticks = [
        tick(2224, 0.05, 0.03, 0.02, 0.01, 0.01),
        tick(5560, 0.08, 0.05, 0.03, 0.02, 0.01),
        tick(5720, 0.04, 0.03, 0.02, 0.01, 0.01),
        tick(6140, 0.12, 0.07, 0.04, 0.04, 0.02),
        tick(6460, 0.06, 0.03, 0.02, 0.01, 0.01),
        tick(240000000, 0.03, 0.01, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.pwr.kW", 1.200, 0.40),
        spike("tc.melt.C", 2.224, 0.58),
        spike("enc.pwr.kW", 3.600, 0.50),
        spike("tc.melt.C", 5.560, 1.32),
        spike("enc.pwr.kW", 5.720, 1.10),
        spike("ctrl.gate", 6.140, 0.97),
        spike("tc.melt.C", 8.400, 0.80),
        spike("enc.pwr.kW", 11.200, 0.62),
        spike("ctrl.gate", 14.800, 0.85),
        spike("tc.melt.C", 18.200, 0.54),
        spike("enc.pwr.kW", 22.400, 0.41),
        spike("tc.melt.C", 24.800, 0.48),
        spike("ctrl.gate", 25.600, 0.70),
    ]
    excerpt = independent_excerpt(73364, 64, 26000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "A CFD twin of ampoule A-7 at Cesiod-Fell CF-2 puts the CsI melt at 742 C, "
                "32 K over the 710 C freeze cap, while furnace power is only 4.8 kW versus a "
                "6.0 kW bus trip. Melt-first clamps power 4.8 -> 3.1 kW; power-first would "
                "keep cruise because 4.8 kW still looks legal.",
            ),
            ("domain", "cesium-iodide-bridgman"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Keep A-7 melt <= 710 C and finish the CsI freeze without a bus dump.",
            ),
            ("t0_us", 1756857303000364),
            ("gate_latency_us", 580),
            ("race_window_us", 320),
            ("race_window_rel_ms", [5.560, 5.880]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.melt.C 742 over 710 cap",
                                "enc.pwr.kW 4.8 under 6.0 trip",
                            ],
                        ),
                        (
                            "semantics",
                            "Melt-first latches power clamp 4.8 -> 3.1 kW; power-first keeps 4.8 on a "
                            "'still under bus trip' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one melt-TC slot versus the furnace-power encoder publisher on this "
                            "simulated CsI Bridgman bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 56 us (melt 24 + power 32): 2.86x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 320 us "
                            "window would have kept 4.8 kW; predicted next-sample 724 C > 710 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "ampoule melt TC tree, 2 kHz, 24 us jitter",
                    "furnace power encoder, 1 kHz, 32 us jitter",
                    "translation LVDT (context)",
                    "baffle IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("melt_cap_C", 710.0),
                        ("observed_melt_C", 742.0),
                        ("power_kW", 4.8),
                        ("bus_trip_kW", 6.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. A-7 CFD indexed on Cesiod-Fell CF-2; power 4.8 kW; melt 742 C.",
                    "2. Bus 4.8 kW under 6.0; freeze armed.",
                    "3. Power precursor at 1.200 ms.",
                    "4. Race window [5.560, 5.880] ms.",
                    "5. tc.melt.C 742 at 5.560 ms (winner).",
                    "6. enc.pwr.kW 4.8 at 5.720 ms (loser by 160 us).",
                    "7. Gate at 6.140 ms: MODIFY clamp 4.8 -> 3.1 kW.",
                    "8. After clamp melt 698 C <= 710; bus still 3.1 kW.",
                    "9. No later world charge this circuit.",
                    "10. Delayed (survey_s=240): 4 min pyrometry tag on the next freeze.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_furnace_power"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("power_kW", 4.8),
                        ("melt_C", 742.0),
                        ("translate_mm_h", 1.20),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("melt_C", 742.0),
                        ("melt_cap_C", 710.0),
                        ("predicted_unclamped_next_C", 724.0),
                        ("power_kW", 4.8),
                        ("bus_trip_kW", 6.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 56),
                        ("survey_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.8 kW because the bus is under 6.0, treating the "
                "742 C melt as a still-legal freeze rather than a cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Melt 742 C won by 160 us, so the ampoule is over the 710 C freeze cap, not still a "
                "bus-power story. Holding 4.8 kW predicts next-sample 724 C > 710. "
                "MODIFY: power 4.8 -> 3.1 kW. Observed after clamp 698 C <= 710. A full REJECT "
                "is not indicated: a clean freeze accepts 3.1 kW.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "melt_C",
                            OrderedDict(
                                [
                                    ("cap", 710.0),
                                    ("observed", 742.0),
                                    ("predicted_unclamped_next", 724.0),
                                    ("clamped_power_kW", 3.1),
                                    ("observed_after_clamp", 698.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 160),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 2.86),
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
            ("name", "clamped_furnace_power"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("power_kW", 3.1),
                        ("melt_C", 698.0),
                        ("translate_mm_h", 1.20),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: power 4.8 -> 3.1 kW. Process-correct vs the 710 C freeze cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct MODIFY held melt at 698 C under the 710 C cap. Power seated at 3.1 kW "
                "without a later world charge. Delayed pyrometry tags the melt-first bind on the next freeze.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("melt", "clamp executed; peak 698 C <= 710"),
                        ("power", "3.1 kW held"),
                        ("bus", "stayed 3.1 kW under 6.0"),
                        ("qc", "4 min pyrometry tag on next freeze"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Melt fell 742 -> 698 C inside two TC slots after the clamp; bus never approached 6.0 kW.",
                    "Delayed (survey_s=240): pyrometry writes the melt-first bind onto the next CsI freeze.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.melt.C (5.560 ms, 742 C)"),
                        ("loser", "enc.pwr.kW (5.720 ms, 4.8 kW)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Power-first by < 160 us inside the 320 us window would have kept "
                            "4.8 kW; predicted next-sample 724 C would have exceeded the 710 C "
                            "cap. The MODIFY is the correct process either way once melt wins.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6140),
            (
                "reward_inflection_note",
                "Task and safety inflect at the correct clamp (6.140 ms, tick 4). The 4 min pyrometry "
                "tag is delayed surprise bound to raster.delayed_surprise_s=240, not the inflection.",
            ),
            ("delayed_surprise_s", 240),
        ]
    )
    dw = 0.32
    ras = raster_core(
        26,
        64,
        38,
        63,
        routing(
            "thalamic-relay.csi-melt",
            "spikenaut.policy.power-clamp",
            [
                ("relay.tc.melt", "policy.power_clamp", 0.69),
                ("relay.enc.pwr", "policy.power_hold", 0.28),
            ],
            "octopamine",
            0.08,
            "pre_post_stdp; octopamine at melt win (5.560 ms) tags the power_clamp bind",
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
            ("decision_window_ms", dw),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("power_clamp", 40, 0.50, 310.0, dw),
                    pop_budget("power_hold", 40, 0.50, 80.0, dw),
                    pop("melt_cap_veto", 16, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r73-364"),
            (
                "title",
                "Cesiod-Fell CF-2 / Ampoule A-7: melt 742 C beats furnace 4.8 kW by 160 us; "
                "correct MODIFY clamps power 4.8 -> 3.1 kW with no later world charge",
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
                    "Correct MODIFY. Melt 742 -> 698 C under 710 cap. "
                    "total +0.90 = 0.38 + 0.22 + 0.14 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "cesium-iodide-bridgman",
                    [
                        "modify",
                        "melt-first",
                        "tick6-sidecar-bound",
                        "simulated",
                    ],
                    "Teaches melt-vs-power order on a simulated CsI Bridgman: routing.table[0] to "
                    "policy.power_clamp with furnace encoder as the losing hold.",
                    4,
                ),
            ),
        ]
    )


def record_365():
    ticks = [
        tick(2144, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(5360, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(5520, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(6060, 0.16, 0.10, 0.07, 0.05, 0.02),
        tick(6420, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(300000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    params = OrderedDict(
        [
            ("cell_kA", 6.40),
            ("bath_C", 1012.0),
            ("hood_ir_C", 1184.0),
        ]
    )
    spikes = [
        spike("ir.hood.C", 1.400, 0.40),
        spike("tc.bath.C", 2.144, 0.55),
        spike("ir.hood.C", 4.000, 0.48),
        spike("tc.bath.C", 5.360, 1.28),
        spike("ir.hood.C", 5.520, 1.08),
        spike("ctrl.gate", 6.060, 0.96),
        spike("tc.bath.C", 10.400, 0.78),
        spike("ir.hood.C", 14.200, 0.60),
        spike("ctrl.gate", 18.800, 0.84),
        spike("tc.bath.C", 21.100, 0.50),
        spike("ir.hood.C", 23.200, 0.38),
        spike("ctrl.gate", 23.600, 0.66),
    ]
    excerpt = independent_excerpt(73365, 80, 24000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Electrolytic cell C-11 at Terbia-Quern TQ-9 is already holding bath-center 1012 C "
                "under a 1080 C freeze cap while hood IR is a quiet 1184 C under the 1280 C smear "
                "trip. Bath-first accepts the already-legal 6.40 kA; IR-first would REJECT a legal "
                "TbF3 reduction on a leftover hood-glint smear.",
            ),
            ("domain", "terbium-fluoride-electrolyzer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish C-11 reduction at 6.40 kA while bath stays <= 1080 C.",
            ),
            ("t0_us", 1756857304000365),
            ("gate_latency_us", 700),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.360, 5.720]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.bath.C 1012 under 1080 cap",
                                "ir.hood.C 1184 smear vs 1280 trip",
                            ],
                        ),
                        (
                            "semantics",
                            "Bath-first latches ACCEPT of 6.40 kA; IR-first would REJECT an "
                            "already-legal reduction on a leftover hood-glint smear model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one bath-well TC slot versus the hood-IR publisher on this "
                            "TbF3 cell bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 70 us (bath 30 + IR 40): 2.29x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 360 us "
                            "window would have REJECTED an already-legal 6.40 kA reduction.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bath-well TC, 1 kHz, 30 us jitter",
                    "hood IR, 1 kHz, 40 us jitter",
                    "cell current encoder (context)",
                    "off-gas HF NDIR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bath_cap_C", 1080.0),
                        ("observed_bath_C", 1012.0),
                        ("hood_ir_C", 1184.0),
                        ("hood_trip_C", 1280.0),
                        ("cell_kA", 6.40),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. C-11 indexed on Terbia-Quern TQ-9; 6.40 kA armed; bath 1012 C.",
                    "2. Hood IR 1184 C under 1280; bath under 1080 cap.",
                    "3. IR precursor at 1.400 ms.",
                    "4. Race window [5.360, 5.720] ms.",
                    "5. tc.bath.C 1012 at 5.360 ms (winner).",
                    "6. ir.hood.C 1184 at 5.520 ms (loser by 160 us).",
                    "7. Gate at 6.060 ms: ACCEPT already-legal 6.40 kA.",
                    "8. Bath stays 1012; IR smear unchanged.",
                    "9. No freeze this circuit.",
                    "10. Delayed (dwell_s=300): 5 min spectro tag on the next pot.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_cell_current"),
            ("parameters", OrderedDict(params.items())),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bath_C", 1012.0),
                        ("bath_cap_C", 1080.0),
                        ("hood_ir_C", 1184.0),
                        ("hood_trip_C", 1280.0),
                        ("cell_kA", 6.40),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 70),
                        ("dwell_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 6.40 kA because bath 1012 C is under 1080; hood IR "
                "1184 C is treated as a glint smear, not a bath miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bath 1012 C won by 160 us and is under the 1080 C freeze cap. "
                "Hood IR 1184 C is under the 1280 C trip and does not authorize a hold. "
                "ACCEPT: leave 6.40 kA. A MODIFY cut would stall an already-legal reduction.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bath_C",
                            OrderedDict(
                                [
                                    ("cap", 1080.0),
                                    ("observed", 1012.0),
                                    ("executed_cell_kA", 6.40),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 160),
                                    ("combined_jitter_us", 70),
                                    ("ratio", 2.29),
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
            ("name", "hold_cell_current"),
            ("parameters", OrderedDict(params.items())),
            ("gate_effect", "ACCEPT: leave 6.40 kA; bath 1012; IR smear legal."),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 6.40 kA reduction. Bath 1012 beat hood IR 1184 "
                "by 160 us. 5 min spectro tag (dwell_s=300) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("current", "6.40 kA held"),
                        ("bath", "1012 < 1080 cap"),
                        ("cell", "C-11 on-spec"),
                        ("qc", "5 min spectro tag (dwell_s=300)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Hood IR never approached 1280 C; bath was already under cap.",
                    "Delayed (dwell_s=300): 5 min spectro tag after the pot.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bath.C (5.360 ms, 1012 C)"),
                        ("loser", "ir.hood.C (5.520 ms, 1184 C)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 160 us inside the 360 us window would have "
                            "REJECTED an already-legal reduction. The ACCEPT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6060),
            (
                "reward_inflection_note",
                "Task and safety rise at the correct ACCEPT (6.060 ms, tick 4). The 5 min spectro "
                "tag is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 300),
        ]
    )
    dw = 0.36
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.tbf3-bath",
            "spikenaut.policy.current-go",
            [
                ("relay.tc.bath", "policy.current_go", 0.67),
                ("relay.ir.hood", "policy.current_hold", 0.25),
            ],
            "serotonin",
            0.12,
            "accept_stdp; 5-HT tags the bath win as an already-legal reduction",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("dwell_s", 300),
                ("delayed_surprise_s", 300),
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
                    pop_budget("current_go", 50, 0.45, 160.0, dw),
                    pop("current_hold", 32, 0.90),
                    pop("bath_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r73-365"),
            (
                "title",
                "Terbia-Quern TQ-9 / Cell C-11: bath 1012 C beats hood IR 1184 C by 160 us; "
                "correct ACCEPT of an already-legal 6.40 kA reduction",
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
                    "Correct ACCEPT. Bath 1012 < 1080; IR 1184 < 1280. "
                    "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "terbium-fluoride-electrolyzer",
                    [
                        "accept",
                        "designed",
                        "bath-vs-ir",
                        "current-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal hood-IR smear can lose to bath temperature inside a 360 us "
                    "window; reversing 160 us would have REJECTED an already-legal reduction.",
                    5,
                ),
            ),
        ]
    )
