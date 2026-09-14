def record_272():
    ticks = [
        tick(2280, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5620, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5796, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6180, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6540, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("so2.bedB.pct", 1.160, 0.42),
        spike("so2.bedA.pct", 2.280, 0.57),
        spike("so2.bedB.pct", 3.620, 0.49),
        spike("so2.bedA.pct", 5.620, 1.29),
        spike("so2.bedB.pct", 5.796, 1.10),
        spike("ctrl.gate", 6.180, 0.96),
        spike("so2.bedA.pct", 8.400, 0.80),
        spike("so2.bedB.pct", 10.400, 0.63),
        spike("ctrl.gate", 11.200, 0.84),
        spike("so2.bedA.pct", 16.600, 0.41),
        spike("so2.bedB.pct", 22.200, 0.54),
        spike("so2.bedA.pct", 25.400, 0.38),
    ]
    excerpt = independent_excerpt(51272, 92, 26000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Oleum-Thwaite OT-5 contact plant is mid-pass with two parallel converter strings. "
                "Live Bed-A SO2 is 12.40 percent against a 10.00 percent stack cap while idle "
                "Bed-B still prints 7.20 percent under that same cap. A-first should dump quench "
                "4.2 -> 7.8 t/h on Bed-A; a weak supervisor files the 2.4 t/h bump onto idle Bed-B.",
            ),
            ("domain", "sulfuric-contact-converter"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the OT-5 pass with Bed-A SO2 <= 10.00 percent, leave idle Bed-B parked, "
                "and keep the 7.8 t/h quench on the live string.",
            ),
            ("t0_us", 1756850400000272),
            ("gate_latency_us", 540),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.62, 5.98]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "so2.bedA.pct 12.40 on live string",
                                "so2.bedB.pct 7.20 on idle string",
                            ],
                        ),
                        (
                            "semantics",
                            "A-first should latch a hard quench 4.2 -> 7.8 t/h on Bed-A; "
                            "B-first is a false idle-string bump on a parked converter.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one Bed-A UV slot versus the Bed-B UV publisher on this "
                            "dual-string contact bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 176 us vs combined jitter 58 us (A 26 + B 32). Order is "
                            "correctly A-first. The error is which string the MODIFY binds, "
                            "not which actuator class.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "Bed-A UV SO2 cell, 2 kHz, 26 us jitter, string=live",
                    "Bed-B UV SO2 cell, 1 kHz, 32 us jitter, string=idle",
                    "quench-flow orifice (context)",
                    "converter inlet PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("so2_cap_pct", 10.00),
                        ("observed_so2_A_pct", 12.40),
                        ("observed_so2_B_pct", 7.20),
                        ("live_bed_id", "A"),
                        ("idle_bed_id", "B"),
                        ("cycle_phase", "pass"),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Dual-string pass; Bed-A live 12.40 percent SO2; Bed-B idle 7.20.",
                    "2. Cap 10.00 percent applies to the live string only.",
                    "3. Bed-B precursor at 1.160 ms.",
                    "4. Race window [5.620, 5.980] ms.",
                    "5. so2.bedA.pct 12.40 at 5.620 ms (winner).",
                    "6. so2.bedB.pct 7.20 at 5.796 ms (loser by 176 us).",
                    "7. Gate at 6.180 ms: WRONG-MODIFY binds idle Bed-B (wrong-string).",
                    "8. Quench 1.0 -> 2.4 t/h on B; Bed-A peaks 14.10 percent.",
                    "9. Converter trip; string recycle.",
                    "10. Delayed (abort_s=720): 12 min converter recycle while Bed-A is quenched and reseeded.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_dual_string"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("quench_t_h", 4.2),
                        ("bed_id", "A"),
                        ("so2_A_pct", 12.40),
                        ("so2_B_pct", 7.20),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("so2_A_pct", 12.40),
                        ("so2_B_pct", 7.20),
                        ("so2_cap_pct", 10.00),
                        ("live_bed_id", "A"),
                        ("idle_bed_id", "B"),
                        ("cycle_phase", "pass"),
                        ("t_gate_us", 6180),
                        ("correct_quench_t_h", 7.8),
                        ("correct_bed_id", "A"),
                        ("race_margin_us", 176),
                        ("combined_jitter_us", 58),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 4.2 t/h on Bed-A because idle Bed-B 7.20 percent is "
                "under the 10.00 cap, treating the 12.40 percent live string as a still-warming UV cell.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Bed-B 7.20 percent is still under the 10.00 percent cap (true of the idle string). "
                "Bump quench 1.0 -> 2.4 t/h on Bed-B as a precaution because the pass is not a "
                "heat-up. Leave Bed-A 12.40 percent as a noisy UV cell until the next dual-string refresh.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "so2_pct",
                            OrderedDict(
                                [
                                    ("cap", 10.00),
                                    ("observed_live_A", 12.40),
                                    ("observed_idle_B", 7.20),
                                    ("correct_at_t_gate", 7.8),
                                    ("executed_quench_t_h", 2.4),
                                    ("executed_bed_id", "B"),
                                    ("cycle_phase", "pass"),
                                ]
                            ),
                        ),
                        (
                            "string",
                            OrderedDict(
                                [
                                    ("t_gate_us", 6180),
                                    ("live_bed_id", "A"),
                                    ("executed_bed_id", "B"),
                                    ("wrong_string", True),
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
            ("name", "quench_idle_string"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("quench_t_h", 2.4),
                        ("bed_id", "B"),
                        ("so2_A_pct", 12.40),
                        ("so2_B_pct", 7.20),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / wrong-string): 2.4 t/h bump bound to idle Bed-B while live "
                "Bed-A 12.40 percent > 10.00 cap. Routing relay.so2.A -> policy.quench_B; "
                "no positive weight to policy.quench_A.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY bound idle Bed-B and applied a 2.4 t/h quench bump. Live Bed-A "
                "12.40 percent was over the 10.00 cap at t_gate. Peak 14.10 percent tripped the "
                "converter. 12 min recycle (abort_s=720). Correct gate was MODIFY quench "
                "4.2 -> 7.8 t/h on live Bed-A at t_gate_us=6180.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bed_A", "untouched; peak 14.10 > 10.00 cap"),
                        ("bed_B", "idle string bumped 1.0 -> 2.4 t/h"),
                        ("recycle", "12 min converter recycle, Bed-A reseed"),
                        ("mission", "pass deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "A-first was the correct order and the live number was over cap; the MODIFY spent that win on the idle parallel bank.",
                    "Delayed (abort_s=720): OT-5 holds 12 min while Bed-A is quenched and reseeded; next drop 16 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY quench 4.2 -> 7.8 t/h at t_gate_us=6180; bed_id=A; leave idle Bed-B parked.",
                        ),
                        ("correct_actuator", "quench_A"),
                        ("wrong_string", "B"),
                        ("live_bed_id", "A"),
                        ("idle_bed_id", "B"),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("quench_t_h", 2.4),
                                    ("bed_id", "B"),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min converter recycle (task/efficiency); Bed-A peaked 14.10 percent on an idle-string bind (safety near-miss of a live-over-cap quench).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "so2.bedA.pct (5.620 ms, 12.40 percent)"),
                        ("loser", "so2.bedB.pct (5.796 ms, 7.20 percent)"),
                        ("margin_us", 176),
                        (
                            "counterfactual_if_reversed",
                            "B-first by < 176 us would still be under the 10.00 cap on an idle "
                            "string; a correct gate binds so2.bedA.pct to policy.quench_A at t_gate "
                            "either way. The wrong MODIFY spent the live win on the parked bank.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6180),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the idle-string bind (6.180 ms, tick 4). "
                "The 12 min converter recycle is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 720),
        ]
    )
    dw = 0.36
    ras = raster_core(
        26,
        92,
        32,
        77,
        routing(
            "thalamic-relay.so2-idle",
            "spikenaut.policy.quench-B",
            [
                ("relay.so2.A", "policy.quench_B", 0.76),
                ("relay.so2.B", "policy.quench_B", 0.18),
            ],
            "acetylcholine",
            0.08,
            "timing_cap_stdp; ACh tags the (wrong) quench_B bind at the Bed-A win",
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
                    pop_budget("quench_B", 48, 0.45, 300.0, dw),
                    pop("quench_A", 48, 0.90),
                    pop("string_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r51-272"),
            (
                "title",
                "WRONG-MODIFY at Oleum-Thwaite OT-5 / Bed-A: live SO2 12.40 percent read correctly; "
                "2.4 t/h quench bound to idle Bed-B (wrong-string)",
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
                    "Wrong-modify / wrong-string. Sidecar arithmetic 12.40 > 10.00 on live A vs "
                    "7.20 idle B is true; MODIFY bound to quench_B. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "sulfuric-contact-converter",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-string",
                        "idle-parallel-bank",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live-first race can still be a wrong gate "
                    "when the MODIFY binds the idle parallel bank. Convictable from bed_id and "
                    "routing to without sulfuric physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )
