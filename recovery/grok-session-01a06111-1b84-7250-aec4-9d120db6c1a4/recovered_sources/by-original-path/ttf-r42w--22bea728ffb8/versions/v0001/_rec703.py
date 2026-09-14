def record_703():
    ticks = [
        tick(2740, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(7010, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7188, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7860, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(8180, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("tc.melt.ctx", 1.38, 0.43),
        spike("ae.crucible.pps", 2.74, 0.61),
        spike("enc.pull.mm", 4.51, 0.49),
        spike("ae.crucible.pps", 7.01, 1.34),
        spike("enc.pull.mm", 7.188, 1.11),
        spike("ctrl.gate", 7.86, 1.02),
        spike("ae.crucible.pps", 10.15, 0.78),
        spike("tc.melt.ctx", 14.70, 0.44),
        spike("enc.pull.mm", 19.20, 0.58),
        spike("ctrl.gate", 24.40, 0.81),
        spike("ae.crucible.pps", 31.00, 0.53),
        spike("enc.pull.mm", 38.60, 0.46),
        spike("tc.melt.ctx", 43.80, 0.37),
    ]
    excerpt = independent_excerpt(42703, 112, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "GGG puller P-3 on the Garnet-Wold GW-HIL pad is armed for a 0.28 mm/min "
                "crystal pull while an iridium-crucible AE packet reads 48 pps against a 12 pps "
                "move cap. A pull encoder, lit by the pad lamp, still reads 2.10 mm/min under a "
                "4.00 mm/min travel look. AE-first latches REJECT hold; encoder-first would "
                "commit a 0.28 mm/min pull into a live crack.",
            ),
            ("domain", "gadolinium-gallium-garnet-puller"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not pull GGG P-3 unless crucible AE <= 12 pps; keep slip 0.0 mm/min until "
                "the injected crack recovers.",
            ),
            ("t0_us", 1756850400000703),
            ("gate_latency_us", 850),
            ("race_window_us", 300),
            ("race_window_rel_ms", [6.9, 7.2]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.crucible.pps 48 pps",
                                "enc.pull.mm 2.10 mm/min under 4.00",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches REJECT hold 0.0 mm/min slip; encoder-first would "
                            "commit a 0.28 mm/min pull on an apparent 2.10 mm/min under-read.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one crucible-AE sample versus encoder integration on this "
                            "GGG HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 178 us vs combined jitter 56 us (AE 24 + ENC 32): 3.2x over "
                            "a 2.0x trust floor. Pad injects the encoder lamp 120-160 us before "
                            "the AE (geometric lag, not a sensor fault); the 2.10 mm/min packet "
                            "is still the loser in this 300 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "iridium-crucible AE puck, 5 kHz burst, 24 us jitter",
                    "crystal-pull encoder, 200 Hz, 32 us jitter",
                    "melt thermocouple (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("crack_cap_pps", 12.0),
                        ("observed_crack_pps", 48.0),
                        ("pull_mm_min", 2.10),
                        ("pull_look_mm_min", 4.00),
                        ("proposed_slip_mm_min", 0.28),
                        ("lamp_inject_lead_us", [120, 160]),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        (
                            "pad",
                            "Garnet-Wold GW-HIL GGG Czochralski mockup with physical pull axis",
                        ),
                        ("injected", "crucible AE burst + encoder lamp spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop GGG puller. Invented plant; not a live crystal shop.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Puller P-3 on the GW-HIL pad; 0.28 mm/min pull armed.",
                    "2. Encoder lamp injected 120-160 us before AE sees 48 pps.",
                    "3. Melt-TC precursor at 1.380 ms.",
                    "4. Race window [6.900, 7.200] ms.",
                    "5. ae.crucible.pps 48 pps at 7.010 ms (winner).",
                    "6. enc.pull.mm 2.10 mm/min at 7.188 ms (loser by 178 us).",
                    "7. Gate at 7.860 ms: REJECT hold 0.0 mm/min; do not pull 0.28.",
                    "8. Crack remains over 12 pps this cycle; slip cap held.",
                    "9. Crucible re-seat queued on the pad.",
                    "10. Delayed (abort_s=480): 8 min melt re-soak and lamp-spectrum retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "lower_ggg_pull"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("slip_mm_min", 0.28),
                        ("hold", False),
                        ("encoder_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("crack_pps", 48.0),
                        ("crack_cap_pps", 12.0),
                        ("pull_mm_min", 2.10),
                        ("pull_look_mm_min", 4.00),
                        ("race_margin_us", 178),
                        ("combined_jitter_us", 56),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 0.28 mm/min crystal pull because encoder 2.10 mm/min looks "
                "under the 4.00 mm/min travel look, treating AE 48 pps as a noisy bus echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Crucible AE 48 pps is over the 12 pps pull-move cap. Encoder 2.10 mm/min is a "
                "HIL lamp under-read, not a clearance. REJECT: hold 0.0 mm/min; do not commit "
                "a 0.28 mm/min pull.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "crack_pps",
                            OrderedDict(
                                [
                                    ("cap", 12.0),
                                    ("observed", 48.0),
                                    ("pull_mm_min", 2.10),
                                ]
                            ),
                        ),
                        (
                            "slip_mm_min",
                            OrderedDict([("proposed", 0.28), ("executed", 0.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 178),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 3.18),
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
            ("name", "hold_for_crack_drop"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("slip_mm_min", 0.0),
                        ("hold", True),
                        ("encoder_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 0.0 mm/min; 0.28 mm/min pull cancelled. AE 48 > 12 pps cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Puller P-3 at 0.0 mm/min slip. Crack over cap this cycle; "
                "slip cap held. Encoder apparent was not treated as an AE clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("slip", "held; 0.0 mm/min"),
                        ("crack", "still over 12 pps this cycle"),
                        ("encoder", "2.10 mm/min unused as clearance"),
                        ("mission", "pull deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: encoder lamp was injected 120-160 us before the AE puck, yet crucible AE still won the 300 us race.",
                    "Delayed (abort_s=480): pad policy update forbids treating pull encoder mm/min as a crucible-AE substitute after an 8 min re-soak.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.crucible.pps (7.010 ms, 48 pps)"),
                        ("loser", "enc.pull.mm (7.188 ms, 2.10 mm/min)"),
                        ("margin_us", 178),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 178 us inside the 300 us window would have "
                            "committed a 0.28 mm/min pull with AE 48 > 12 pps cap. Order, not "
                            "amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7860),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (7.860 ms, tick 4) as the "
                "hold lands. The 8 min re-soak is delayed surprise bound to abort_s=480.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    ras = raster_core(
        46,
        112,
        20,
        103,
        routing(
            "thalamic-relay.ggg-ae",
            "spikenaut.policy.pull-hold",
            [
                ("relay_crack_pps", "policy_pull_hold", 0.70),
                ("relay_enc_pull", "policy_enc_pull", 0.24),
            ],
            "dopamine",
            0.15,
            "crack_hold_stdp; DA tags the pull_hold bind at the crucible-AE win",
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
            ("decision_window_ms", 0.30),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("pull_hold", 70, 0.48, 250.0, 5),
                    pop("enc_pull", 50, 0.85),
                    pop("crack_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r42-703"),
            (
                "title",
                "Garnet-Wold GW-HIL / Puller P-3: crucible AE 48 pps beats pull encoder 2.10 "
                "mm/min by 178 us; correct REJECT holds the GGG pull",
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
                    "Correct REJECT. Crucible AE over cap beats encoder under-read. total 0.80 "
                    "= 0.10 + 0.42 + 0.12 + 0.10 + 0.06. Tick 6 binds abort_s=480.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "gadolinium-gallium-garnet-puller",
                    ["reject", "hil", "crucible-ae", "encoder-underread", "tick6-sidecar-bound"],
                    "Teaches that a HIL pull-encoder under-read losing a 178 us race does not "
                    "clear a crucible-AE over-rate. Hold is distillable from pps vs cap.",
                    3,
                ),
            ),
        ]
    )

