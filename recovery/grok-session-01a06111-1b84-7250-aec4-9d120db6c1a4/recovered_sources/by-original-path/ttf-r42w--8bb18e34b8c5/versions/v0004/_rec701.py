def record_701():
    excerpt, extra = lif_701_excerpt()
    ticks = [
        tick(2380, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6040, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(6228, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6840, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22200, 0.04, -0.45, -0.03, -0.01, -0.01),
        tick(840000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Mother liquor leaving Perchlor-Beck PB-4 / X-2 prints 78.4 C on the "
                "nucleation lance, 6.4 K past the 72.0 C KClO4 seed-out ceiling, with the "
                "mass-flow still at 18.4 t/h. Whoever wins the 400 us slot either trims that "
                "feed to 11.2 t/h or treats condenser DP 6.2 kPa (under a 9.0 kPa flood "
                "look) as permission to keep dumping. The scraper already wedged on the "
                "basket is silent on both T and FT until AE later dumps wet cake.",
            ),
            ("domain", "potassium-perchlorate-crystallizer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep crystallizer X-2 liquor <= 72.0 C and finish the KClO4 pass without "
                "dumping wet cake onto the basket floor.",
            ),
            ("t0_us", 1756850400000701),
            ("gate_latency_us", 800),
            ("race_window_us", 400),
            ("race_window_rel_ms", [6.0, 6.4]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.liquor.C 78.4 over 72.0 KClO4-nucleation cap",
                                "ft.feed.tph 18.4 with condenser DP 6.2 under 9.0 kPa",
                            ],
                        ),
                        (
                            "semantics",
                            "Temperature-first latches liquor clamp 18.4 -> 11.2 t/h; "
                            "vacuum-first keeps 18.4 t/h on a 'still under flood-ceiling' model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one liquor-TC slot versus the feed-mass FT publisher on "
                            "this perchlorate crystallizer skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 188 us vs combined jitter 64 us (TC 30 + FT 34): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 188 us inside the 400 us "
                            "window would have kept 18.4 t/h; predicted next-sample 80.6 C > 72 "
                            "KClO4-nucleation cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "liquor thermocouple lance, 2 kHz, 30 us jitter",
                    "feed mass-flow FT + condenser DP, 1 kHz, 34 us jitter",
                    "basket AE puck (context)",
                    "scraper-blade IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("liquor_cap_C", 72.0),
                        ("observed_liquor_C", 78.4),
                        ("feed_tph", 18.4),
                        ("condenser_dp_kPa", 6.2),
                        ("condenser_cap_kPa", 9.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Crystallizer X-2 in KClO4 pass; feed 18.4 t/h; liquor 78.4 C.",
                    "2. Condenser DP 6.2 kPa under 9.0 flood; scraper jam armed.",
                    "3. Feed-FT precursor at 1.160 ms.",
                    "4. Race window [6.000, 6.400] ms.",
                    "5. tc.liquor.C 78.4 C at 6.040 ms (winner).",
                    "6. ft.feed.tph 18.4 at 6.228 ms (loser by 188 us).",
                    "7. Gate at 6.840 ms: MODIFY clamp 18.4 -> 11.2 t/h.",
                    "8. After clamp liquor 70.8 C <= 72; DP still 6.2 kPa.",
                    "9. At 22.200 ms a scraper-blade jam dumps 0.4 t of wet cake onto the basket.",
                    "10. 14 min basket re-pack (abort_s=840); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_liquor_feed"),
            (
                "parameters",
                OrderedDict(
                    [("feed_tph", 18.4), ("liquor_C", 78.4), ("condenser_dp_kPa", 6.2)]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("liquor_C", 78.4),
                        ("liquor_cap_C", 72.0),
                        ("predicted_unclamped_next_C", 80.6),
                        ("feed_tph", 18.4),
                        ("condenser_dp_kPa", 6.2),
                        ("condenser_cap_kPa", 9.0),
                        ("race_margin_us", 188),
                        ("combined_jitter_us", 64),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.4 t/h because condenser DP 6.2 kPa is under 9.0, treating "
                "the 78.4 C liquor as a still-wet lance rather than a KClO4-nucleation miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Liquor 78.4 C won by 188 us, so the crystallizer is over the 72.0 C "
                "KClO4-nucleation cap, not still a flood-ceiling story. Holding 18.4 t/h "
                "predicts next-sample 80.6 C > 72. MODIFY: feed 18.4 -> 11.2 t/h. Observed "
                "after clamp 70.8 C <= 72. A full REJECT is not indicated: a clean KClO4 "
                "pass accepts 11.2 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "liquor_C",
                            OrderedDict(
                                [
                                    ("cap", 72.0),
                                    ("observed", 78.4),
                                    ("predicted_unclamped_next", 80.6),
                                    ("clamped_feed_tph", 11.2),
                                    ("observed_after_clamp", 70.8),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 188),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 2.94),
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
            ("name", "clamped_liquor_feed"),
            (
                "parameters",
                OrderedDict(
                    [("feed_tph", 11.2), ("liquor_C", 70.8), ("condenser_dp_kPa", 6.2)]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: feed 18.4 -> 11.2 t/h. Process-correct vs the 72.0 C "
                "KClO4-nucleation cap. Scraper-blade jam still dumps at 22.200 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held liquor at 70.8 C. At 22.200 ms a scraper-blade "
                "jam already seated over the basket dumped 0.4 t of wet cake onto the floor. "
                "Clamp reduced dump energy; it did not prevent the dump. Partnered negative: "
                "process heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("liquor", "clamp executed; peak 70.8 C <= 72 cap"),
                        ("basket", "scraper jam dump at 22.200 ms; 0.4 t wet cake"),
                        ("repair", "14 min basket re-pack (abort_s=840)"),
                        ("mission", "PB-4 KClO4 pass incomplete this cycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither liquor T nor feed FT predicted the seated scraper-blade jam; ae.scraper.jam is a new channel at 22.200 ms, 15.360 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=840): 14 min basket re-pack. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "14 min basket re-pack after the scraper-blade jam. Safety head -0.64 prices "
                "the dump; task_progress stays +0.30 because the clamp completed.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.liquor.C (6.040 ms, 78.4 C)"),
                        ("loser", "ft.feed.tph (6.228 ms, 18.4 t/h)"),
                        ("margin_us", 188),
                        (
                            "counterfactual_if_reversed",
                            "Vacuum-first by < 188 us inside the 400 us window would have kept "
                            "18.4 t/h; predicted next-sample 80.6 C would have missed the 72 "
                            "KClO4-nucleation cap even without the jam. The MODIFY is still the "
                            "correct process. The dump is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22200),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.200 ms scraper-blade jam (tick t_us=22200), inside "
                "the 42 ms raster. The correct MODIFY at 6.840 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=840 re-pack tick.",
            ),
            ("delayed_surprise_s", 840),
        ]
    )
    spikes = [
        spike("ft.feed.ctx", 1.16, 0.41),
        spike("tc.liquor.C", 2.38, 0.58),
        spike("ft.feed.tph", 3.91, 0.50),
        spike("tc.liquor.C", 6.04, 1.31),
        spike("ft.feed.tph", 6.228, 1.12),
        spike("ctrl.gate", 6.84, 0.97),
        spike("tc.liquor.C", 8.15, 0.82),
        spike("ft.feed.tph", 10.60, 0.64),
        spike("ctrl.gate", 14.20, 0.86),
        spike("ae.scraper.jam", 22.20, 1.48),
        spike("ae.scraper.jam", 24.05, 0.93),
        spike("ft.feed.ctx", 29.70, 0.40),
        spike("tc.liquor.C", 36.10, 0.55),
    ]
    ras = raster_core(
        42,
        76,
        24,
        77,
        routing(
            "thalamic-relay.pb-liquor",
            "spikenaut.policy.feed-clamp",
            [
                ("relay_liquor_C", "policy_feed_clamp", 0.68),
                ("relay_feed_ft", "policy_feed_hold", 0.29),
                ("relay_ae_jam", "policy_feed_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at liquor win (6.040 ms) opens a 42 ms "
            "eligibility trace that still covers the 22.200 ms scraper-blade jam",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.4),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("feed_clamp", 50, 0.5, 200.0, 4),
                    pop("feed_hold", 40, 0.8, 50.0, 1),
                    pop("jam_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r42-701"),
            (
                "title",
                "Perchlor-Beck PB-4 / Crystallizer X-2: liquor 78.4 C beats feed 18.4 t/h by "
                "188 us; correct MODIFY still eats an in-window scraper-blade jam (partnered "
                "negative total -0.48)",
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
                    "basket re-pack (abort_s=840) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "potassium-perchlorate-crystallizer",
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
                    "14 min basket re-pack.",
                    1,
                ),
            ),
        ]
    )

