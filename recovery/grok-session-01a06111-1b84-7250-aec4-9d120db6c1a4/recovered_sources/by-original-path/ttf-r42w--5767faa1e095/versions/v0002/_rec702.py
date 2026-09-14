def record_702():
    ticks = [
        tick(2180, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5510, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5694, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6040, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6420, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(1080000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.cycle.ctx", 1.02, 0.42),
        spike("pt.live.bar", 2.18, 0.57),
        spike("hart.burst.eu", 3.12, 0.88),
        spike("pt.live.bar", 5.51, 1.29),
        spike("hart.burst.eu", 5.694, 1.10),
        spike("ctrl.gate", 6.04, 0.96),
        spike("fv.hold.stem", 6.42, 1.18),
        spike("pt.live.bar", 7.85, 0.80),
        spike("hart.burst.eu", 10.18, 0.63),
        spike("ctrl.gate", 13.40, 0.84),
        spike("enc.cycle.ctx", 18.20, 0.41),
        spike("pt.live.bar", 22.00, 0.54),
        spike("fv.hold.stem", 26.20, 0.38),
    ]
    excerpt = independent_excerpt(42702, 96, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Kettle PT on Holmia-Knap HK-6 / ST-8 sits at 2.40 bar (valid 8.16 mA loop) "
                "under a published 5.60 bar HoCl3 trip while the planner still wants 3.6 t/h "
                "of distillate. A leftover HART burst-mode STATUS word 0x80, 6200 ms stale, "
                "is being linearly scaled as if it were 4-20 mA and therefore prints 7.20 bar. "
                "The gate is whether that STATUS nibble is allowed to masquerade as a PV.",
            ),
            ("domain", "holmium-chloride-still"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Execute the 3.6 t/h HoCl3 distillate while live kettle stays <= 5.60 bar; do "
                "not spend a HART burst-mode STATUS word as if it were the live PV.",
            ),
            ("t0_us", 1756850400000702),
            ("gate_latency_us", 530),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.4, 5.76]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.live.bar 2.40 bar valid 8.16 mA",
                                "hart.burst.eu 7.20 bar burst-mode STATUS as EU",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-first should ACCEPT 3.6 t/h (2.40 bar < 5.60 bar cap). "
                            "Burst-first tempts a weak supervisor to treat HART STATUS 0x80 as "
                            "a 7.20 bar live PV.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one live-PT sample minus HART burst-mode publisher delay "
                            "on this HoCl3 still bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 184 us vs combined jitter 60 us (live 28 + burst 32). Order "
                            "is correctly live-first. The error is which quantity the REJECT is "
                            "bound to, not the race order.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "kettle PT, 4 kHz, 28 us jitter, 4-20 mA 0-10 bar",
                    "HART burst-mode STATUS word, 32 us jitter",
                    "reflux FT (context)",
                    "reboiler steam (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("live_cap_bar", 5.60),
                        ("live_bar", 2.40),
                        ("live_mA", 8.16),
                        ("burst_shadow_bar", 7.20),
                        ("burst_status_word", "0x80"),
                        ("burst_age_ms", 6200),
                        ("max_legal_burst_age_ms", 250),
                        ("burst_mode_status_as_eu", True),
                        ("burst_is_pv", False),
                        ("proposed_feed_tph", 3.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. ST-8 HoCl3 still latched; distillate 3.6 t/h armed on HK-6.",
                    "2. Live kettle 2.40 bar on valid 8.16 mA; burst STATUS 0x80 scaled to 7.20 bar age 6200 ms (> 250 ms legal).",
                    "3. Cycle encoder precursor at 1.020 ms.",
                    "4. Race window [5.400, 5.760] ms.",
                    "5. pt.live.bar 2.40 bar at 5.510 ms (winner).",
                    "6. hart.burst.eu 7.20 bar at 5.694 ms (loser by 184 us).",
                    "7. Gate at 6.040 ms: REJECT hold 0.00 t/h (incorrect).",
                    "8. Legal distillate cancelled; live kettle still 2.40 bar < 5.60 cap.",
                    "9. 7.20 bar remains a burst-mode STATUS word, not a live PV.",
                    "10. Delayed missed_window_s=1080 (18 min chloride-quality window) while ST-8 waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "feed_36"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 3.6),
                        ("hold", False),
                        ("burst_mode_status_as_eu", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_bar", 2.40),
                        ("live_cap_bar", 5.60),
                        ("live_mA", 8.16),
                        ("burst_shadow_bar", 7.20),
                        ("burst_status_word", "0x80"),
                        ("burst_age_ms", 6200),
                        ("max_legal_burst_age_ms", 250),
                        ("burst_mode_status_as_eu", True),
                        ("burst_is_pv", False),
                        ("proposed_feed_tph", 3.6),
                        ("race_margin_us", 184),
                        ("combined_jitter_us", 60),
                        ("missed_window_s", 1080),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 3.6 t/h HoCl3 distillate because live kettle 2.40 bar on "
                "valid 8.16 mA is under the 5.60 bar cap; 7.20 bar is a HART burst-mode STATUS "
                "word scaled as EU, not the live PV.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Burst-mode STATUS scaled as 7.20 bar looks over the 5.60 bar cap once the "
                "supervisor binds the HART STATUS word as a live PV. Live-first 2.40 bar is "
                "treated as a noisy echo of the same transmitter. Over-caution on a burst flag "
                "is the stated doctrine.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "live_bar",
                            OrderedDict(
                                [
                                    ("cap", 5.60),
                                    ("observed", 2.40),
                                    ("executed_feed_tph", 0.0),
                                    ("live_mA", 8.16),
                                ]
                            ),
                        ),
                        (
                            "stale_burst",
                            OrderedDict(
                                [
                                    ("echo_bar", 7.20),
                                    ("misbound_as", "live_pv"),
                                    ("status_word", "0x80"),
                                    ("age_ms", 6200),
                                    ("max_legal_age_ms", 250),
                                    ("burst_is_pv", False),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 184),
                                    ("combined_jitter_us", 60),
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
            ("name", "hocl3_hold_wrong_burst"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 0.0),
                        ("hold", True),
                        ("burst_mode_status_as_eu", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): feed 3.6 -> 0.00 t/h. Routing relay_hart_burst -> "
                "policy_still_hold; live 2.40 bar left unused as a go signal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT held ST-8 at 0.00 t/h. Live kettle 2.40 bar on valid 8.16 mA was "
                "under the 5.60 bar cap; 7.20 bar was a HART burst-mode STATUS word scaled as "
                "EU, not live. 18 min chloride-quality window missed (missed_window_s=1080). "
                "Correct gate was ACCEPT of the 3.6 t/h distillate.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("column", "held; feed 0.00 t/h; live kettle still 2.40 bar < 5.60"),
                        ("burst", "7.20 bar unused, still STATUS 0x80 not a live PV"),
                        ("deck", "18 min chloride-quality window missed"),
                        ("mission", "distillate deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-first was the correct order and the live number was legal; the REJECT spent that win on a HART burst-mode STATUS word scaled as EU.",
                    "Delayed (missed_window_s=1080): HK-6 loses the 18 min chloride-quality window; next window 6.1 h.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT the 3.6 t/h HoCl3 distillate; leave 7.20 bar HART burst STATUS as a diagnostic, not a PV.",
                        ),
                        ("correct_status", "BURST_MODE_STATUS_not_pv"),
                        ("wrong_status", "BURST_MODE_STATUS_as_eu"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("feed_tph", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "Missed 18 min chloride-quality window (task/efficiency); live kettle never exceeded 2.40 bar (safety near-miss of a false hold).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.live.bar (5.510 ms, 2.40 bar valid 8.16 mA)"),
                        ("loser", "hart.burst.eu (5.694 ms, 7.20 bar burst STATUS as EU)"),
                        ("margin_us", 184),
                        (
                            "counterfactual_if_reversed",
                            "Burst-first by < 184 us would still be a STATUS word, not live 7.20 "
                            "bar; a correct gate binds pt.live.bar to policy_still_go either "
                            "way. The wrong REJECT spent the live win on the burst payload.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6040),
            (
                "reward_inflection_note",
                "Task, efficiency, and coherence drop at the wrong REJECT (6.040 ms, tick 4). "
                "The 18 min missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 1080.0),
            ("missed_window_s", 1080),
        ]
    )
    ras = raster_core(
        28,
        96,
        32,
        86,
        routing(
            "thalamic-relay.ho-pt",
            "spikenaut.policy.still-hold",
            [
                ("relay_hart_burst", "policy_still_hold", 0.74),
                ("relay_live_bar", "policy_still_hold", 0.21),
            ],
            "acetylcholine",
            0.08,
            "hocl3_burst_stdp; ACh tags the (wrong) still_hold bind at the live-PT win",
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
                    pop("still_hold", 42, 0.45, 280.0, 4),
                    pop("still_go", 42, 0.9),
                    pop("burst_veto", 20, 0.8),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r42-702"),
            (
                "title",
                "WRONG-REJECT at Holmia-Knap HK-6 / Still ST-8: live kettle 2.40 bar on valid "
                "8.16 mA < 5.60 bar cap; supervisor treats HART burst-mode STATUS 0x80 as 7.20 bar EU",
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
                    "Wrong-reject / burst-mode-status-as-EU. Sidecar arithmetic 2.40 < 5.60 on "
                    "live valid mA is true; REJECT bound to HART STATUS 0x80 scaled as 7.20 bar. "
                    "total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "holmium-chloride-still",
                    [
                        "reject",
                        "wrong-gate",
                        "burst-mode-status-as-eu",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live-first race can still be a wrong gate "
                    "when routing.table[0].to is policy_still_hold and feed_tph is 0. Convictable "
                    "from live_bar vs cap_bar and burst_is_pv without HoCl3 kinetics.",
                    2,
                    supervisor_error_type="wrong-reject",
                ),
            ),
        ]
    )

