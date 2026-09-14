def lif_526_excerpt():
    n = 82
    dt_us = 100
    tau_m_ms = 16.5
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.87
    i_stim_peak = 2.62
    stim = (21800, 25600)
    seed = 102526
    window_us = 48000
    i_clamp_extra = 0.68
    clamp_n = 20
    rng = random.Random(seed)
    tau_s = tau_m_ms / 1000.0
    dt_s = dt_us / 1e6
    decay = math.exp(-dt_s / tau_s)
    steps = window_us // dt_us
    voltage = [rng.random() * v_th * 0.97 for _ in range(n)]
    bias = [i_bias * (1.0 + 0.13 * (rng.random() * 2 - 1)) for _ in range(n)]
    for i in range(clamp_n):
        bias[i] += i_clamp_extra
    ref = [0] * n
    spikes = []
    for step in range(steps):
        t_us = step * dt_us
        stim_i = i_stim_peak if stim[0] <= t_us < stim[1] else 0.0
        for i in range(n):
            if ref[i] > 0:
                ref[i] -= dt_us
                voltage[i] = v_reset
                continue
            current = bias[i] + stim_i
            voltage[i] = current + (voltage[i] - current) * decay
            if voltage[i] >= v_th:
                spikes.append((t_us, i))
                voltage[i] = v_reset
                ref[i] = refractory_us
    early = [(t, nid) for t, nid in spikes if t < 21800]
    burst = [(t, nid) for t, nid in spikes if 21800 <= t < 25600]
    used = set()
    last = {}
    picked = []

    def take(pool, want, label_times=None):
        if not pool:
            return
        chosen_idx = set()
        if label_times:
            for target in label_times:
                best = None
                for idx, (t, nid) in enumerate(pool):
                    if idx in chosen_idx or nid in used:
                        continue
                    if nid in last and t - last[nid] < 1000:
                        continue
                    if best is None or abs(t - target) < abs(best[0] - target):
                        best = (t, nid, idx)
                if best is not None:
                    t, nid, idx = best
                    picked.append((t, nid))
                    used.add(nid)
                    last[nid] = t
                    chosen_idx.add(idx)
        stride = max(1, len(pool) // max(want, 1))
        for idx in range(0, len(pool), stride):
            group = [1 for tt, _ in picked if (tt < 21800) == (pool[0][0] < 21800)]
            if len(group) >= want:
                break
            t, nid = pool[idx]
            if nid in used:
                continue
            if nid in last and t - last[nid] < 1000:
                continue
            picked.append((t, nid))
            used.add(nid)
            last[nid] = t

    take(early, 7)
    take(burst, 9, label_times=(23200, 24200, 25200))
    clamp = [(t, nid) for t, nid in picked if t < 21800][:7]
    gas = [(t, nid) for t, nid in picked if t >= 21800][:9]
    picked = sorted(clamp + gas, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(
            f"LIF excerpt too short {len(picked)} (early={len(early)} burst={len(burst)})"
        )
    channels = ["lif.clamp" if t < 21800 else "lif.gassing" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 82),
            ("dt_us", 100),
            ("tau_m_ms", 16.5),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.87),
            ("i_stim_peak", 2.62),
            ("stim_t_us", [21800, 25600]),
            ("i_clamp_extra", 0.68),
            ("clamp_n", 20),
            ("seed", 102526),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-19 carry +0.68 carbonate-clamp bias; stim 21.8-25.6 ms is the basket gassing.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 960),
            ("delayed_surprise_s", 960),
        ]
    )
    return excerpt_items(picked, channels), extra


def record_526():
    excerpt, extra = lif_526_excerpt()
    ticks = [
        tick(2140, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6140, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(6320, 0.05, -0.03, -0.02, 0.00, 0.00),
        tick(6880, 0.09, -0.06, -0.03, 0.02, -0.01),
        tick(23200, 0.04, -0.42, -0.04, -0.01, -0.02),
        tick(960000000, 0.02, -0.05, -0.02, 0.01, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "DTB-C3 at Cesform-Wath CF-3 is already pushing 6.8 t/h cesium-carbonate liquor into a 58 C "
                "magma against a 52 C crystal-habit cap. A magma-first latch clamps the carbonate; "
                "a feed-first story would keep the 6.8 t/h cruise. Stored basket-screen strain is not "
                "yet an observable of either race channel.",
            ),
            ("domain", "cesium-formate-crystallizer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the CF-3 DTB pass, keep magma hotspot <= 52 C, and leave the "
                "basket screens unmarked.",
            ),
            ("t0_us", 1756850400000526),
            ("gate_latency_us", 740),
            ("race_window_us", 380),
            ("race_window_rel_ms", [6.10, 6.48]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.magma.C 58 C pulse",
                                "ft.cs.tph 6.8 t/h cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Magma-first latches cesium-carbonate 6.8 -> 3.9 t/h; feed-first keeps "
                            "cruise on a still-cooling DTB model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one 2 kHz magma-RTD sample minus carbonate-orifice group delay "
                            "on this DTB bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter ~58 us (magma 28 + carbonate 30): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 380 us window "
                            "would have kept 6.8 t/h cruise; predicted next-sample 55 C > 52 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "magma multiplex RTD, 2 kHz, 28 us timestamp jitter",
                    "cesium-carbonate feed FT, 1 kHz, 30 us jitter",
                    "basket AE puck (context until the gassing)",
                    "formate assay (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("magma_cap_C", 52.0),
                        ("observed_magma_C", 58.0),
                        ("proposed_cs_tph", 6.8),
                        ("formate_wt_pct", 82.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. DTB-C3 indexed on Cesform-Wath CF-3; cesium-carbonate armed at 6.8 t/h.",
                    "2. Cruise 6.8 t/h; magma 58 C against 52 C habit cap.",
                    "3. Carbonate precursor at 1.180 ms; magma warm-start 58 C.",
                    "4. Race window [6.100, 6.480] ms opens on the DTB bus.",
                    "5. rtd.magma.C 58 C at 6.140 ms (winner).",
                    "6. ft.cs.tph 6.8 t/h at 6.320 ms (loser by 180 us).",
                    "7. Gate at 6.880 ms (winner + 740 us): MODIFY clamp 6.8 -> 3.9 t/h.",
                    "8. Clamp executes; next-sample magma 49 C < 52 cap.",
                    "9. At 23.200 ms stored strain still gasses 14 mm of basket screen; AE burst.",
                    "10. Magma isolate 16 min (abort_s=960); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_cs_6p8"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cs_tph", 6.8),
                        ("formate_wt_pct", 82.0),
                        ("dtb_rpm", 18.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("magma_C", 58.0),
                        ("magma_cap_C", 52.0),
                        ("predicted_unclamped_next_C", 55.0),
                        ("cs_tph", 6.8),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 960),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 6.8 t/h cruise: 58 C looks like a formate-assay spike, not "
                "basket contact, and C3 volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Magma 58 C won by 180 us, so the basket is loading heat, not still cooling. "
                "Holding 6.8 t/h predicts next-sample 55 C > 52 cap. MODIFY: cesium-carbonate 6.8 -> "
                "3.9 t/h. Observed after clamp 49 C < 52. A full REJECT is not indicated: a "
                "sound DTB pass accepts 3.9 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "magma_C",
                            OrderedDict(
                                [
                                    ("cap", 52.0),
                                    ("observed", 58.0),
                                    ("predicted_unclamped_next", 55.0),
                                    ("clamped_cs_tph", 3.9),
                                    ("observed_after_clamp", 49.0),
                                ]
                            ),
                        ),
                        (
                            "cs_tph",
                            OrderedDict([("proposed", 6.8), ("clamped", 3.9)]),
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
            ("name", "clamped_cs_3p9"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cs_tph", 3.9),
                        ("formate_wt_pct", 82.0),
                        ("dtb_rpm", 18.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: cesium-carbonate 6.8 -> 3.9 t/h. Process-correct vs the 52 C habit "
                "cap. Basket gassing still occurs at 23.200 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held magma at 49 C. At 23.200 ms stored strain "
                "in the basket screen still gassed a 14 mm face. Clamp reduced dump energy; "
                "it did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("cesium_carbonate", "clamp executed; peak 49 C < 52"),
                        ("basket", "14 mm gassing at 23.200 ms"),
                        ("repair", "16 min magma isolate (abort_s=960)"),
                        ("mission", "CF-3 DTB pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither magma RTD nor carbonate FT predicted the basket charge; ae.bsk.collapse is a new channel at 23.200 ms, 16.320 ms after the gate, still inside the 48 ms raster.",
                    "Delayed (abort_s=960): 16 min magma isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "16 min magma isolate after a 14 mm basket-screen gassing collapse. Safety head -0.62 "
                "prices the split; task_progress stays +0.32 because the carbonate clamp completed "
                "under the 52 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.magma.C (6.140 ms, 58 C)"),
                        ("loser", "ft.cs.tph (6.320 ms, 6.8 t/h)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Feed-first by < 180 us inside the 380 us window would have kept "
                            "6.8 t/h cruise; predicted next-sample 55 C would have exceeded "
                            "the 52 cap even without the basket charge. The MODIFY is still the "
                            "correct process. The collapse is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 23200),
            (
                "reward_inflection_note",
                "Safety collapses at the 23.200 ms basket gassing (tick t_us=23200), inside "
                "the 48 ms raster. The correct MODIFY at 6.880 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=960 isolate tick.",
            ),
            ("delayed_surprise_s", 960.0),
            ("abort_s", 960),
        ]
    )
    spikes = [
        spike("enc.cs.ctx", 1.180, 0.43),
        spike("rtd.magma.C", 2.140, 0.62),
        spike("ft.cs.tph", 3.520, 0.51),
        spike("rtd.magma.C", 6.140, 1.34),
        spike("ft.cs.tph", 6.320, 1.16),
        spike("ctrl.gate", 6.880, 0.99),
        spike("rtd.magma.C", 8.420, 0.81),
        spike("ft.cs.tph", 11.200, 0.63),
        spike("ctrl.gate", 15.600, 0.85),
        spike("ae.bsk.collapse", 23.200, 1.48),
        spike("ae.bsk.collapse", 25.100, 0.92),
        spike("enc.cs.ctx", 33.400, 0.42),
        spike("rtd.magma.C", 42.800, 0.54),
    ]
    ras = raster_core(
        48,
        82,
        24,
        94,
        routing(
            "thalamic-relay.magma-dtb",
            "spikenaut.policy.cs-clamp",
            [
                ("relay.rtd.magma", "policy.cs_clamp", 0.67),
                ("relay.ft.cs", "policy.cs_hold", 0.29),
                ("relay.ae.bsk", "policy.cs_clamp", -0.46),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at magma win (6.140 ms) opens a 50 ms "
            "eligibility trace that still covers the 23.200 ms basket gassing",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.38),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("cs_clamp", 46, 0.50, 229.0, 4),
                    pop("cs_hold", 46, 0.50, 57.2, 1),
                    pop("ss_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r102-526",
        "Cesform-Wath CF-3 / DTB-C3: magma 58 C beats cesium-carbonate-feed by 180 us; correct "
        "MODIFY still eats an in-window basket gassing (partnered negative total -0.46)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "48 ms raster. total -0.46 = 0.32 + -0.62 + -0.16 + 0.04 + -0.04. Named magma "
        "isolate (abort_s=960) is not netted into task_progress.",
        ras,
        gate,
        "cesium-formate-crystallizer",
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
        "16 min magma isolate.",
        1,
    )


def record_527():
    ticks = [
        tick(1760, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(4400, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(4580, -0.03, -0.01, -0.03, -0.02, 0.01),
        tick(5100, -0.07, -0.06, -0.07, -0.04, 0.02),
        tick(7240, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(1080000000, -0.02, -0.01, -0.04, 0.00, 0.00),
    ]
    spikes = [
        spike("ft.lipf.ctx", 0.880, 0.41),
        spike("live.still.C", 1.760, 0.59),
        spike("stale.sim.eu", 2.520, 0.52),
        spike("live.still.C", 4.400, 1.33),
        spike("stale.sim.eu", 4.580, 1.16),
        spike("ctrl.gate", 5.100, 1.01),
        spike("live.still.C", 7.240, 0.75),
        spike("stale.sim.eu", 8.320, 0.62),
        spike("ctrl.gate", 12.400, 0.83),
        spike("ft.lipf.ctx", 16.200, 0.43),
        spike("live.still.C", 21.600, 0.54),
        spike("stale.sim.eu", 26.800, 0.48),
    ]
    excerpt = independent_excerpt(102527, 88, 32000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Still-S7 on Hexaflu-Rigg HF-7 is holding phosphorus-pentafluoride at 3.4 t/h with live "
                "still-base 86.0 C against a 118.0 C trip. A leftover DCS MODE_SIMULATE tag still "
                "prints 142.0 C from an engineering inject. Live-mode-first should ACCEPT the feed; a weak "
                "supervisor that binds the simulation-mode EU will REJECT a legal LiPF6 still.",
            ),
            ("domain", "lithium-hexafluorophosphate-still"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep 3.4 t/h PF5 on Still-S7 while live still-base stays <= 118.0 C; "
                "do not spend a leftover MODE_SIMULATE inject on the hold.",
            ),
            ("t0_us", 1756850400000527),
            ("gate_latency_us", 700),
            ("race_window_us", 340),
            ("race_window_rel_ms", [4.36, 4.70]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "live.still.C 86.0 C LIVE MODE_PROCESS",
                                "stale.sim.eu 142.0 C leftover MODE_SIMULATE inject",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-mode-first should ACCEPT 3.4 t/h (86.0 C < 118.0 C trip). "
                            "Sim-tag-first tempts a weak supervisor to treat 142.0 C as live.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one Still-S7 RTD sample minus leftover MODE_SIMULATE group delay "
                            "on this LiPF6 bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter ~56 us (live 26 + sim 30): 3.2x over "
                            "a 2.0x trust floor. Order is correctly live-mode-first. The error is binding "
                            "the leftover MODE_SIMULATE EU, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "Still-S7 base RTD, 4 kHz, 26 us jitter, MODE_PROCESS LIVE",
                    "leftover MODE_SIMULATE tag shadow, 4 kHz, 30 us jitter, engineering inject STALE",
                    "PF5 feed FT (context)",
                    "HF make-up FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("trip_C", 118.0),
                        ("live_C", 86.0),
                        ("shadow_C", 142.0),
                        ("mode_live", "PROCESS"),
                        ("mode_shadow", "SIMULATE"),
                        ("proposed_pf5_tph", 3.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Still-S7 latched on Hexaflu-Rigg HF-7; PF5 3.4 t/h armed.",
                    "2. Live MODE_PROCESS 86.0 C; leftover MODE_SIMULATE still prints 142.0 C.",
                    "3. PF5-FT precursor at 0.880 ms.",
                    "4. Race window [4.360, 4.700] ms.",
                    "5. live.still.C 86.0 C at 4.400 ms (winner).",
                    "6. stale.sim.eu 142.0 C at 4.580 ms (loser by 180 us).",
                    "7. Gate at 5.100 ms: REJECT hold 0.0 t/h (incorrect).",
                    "8. Legal feed cancelled; live still-base still 86.0 C < 118.0 C trip.",
                    "9. MODE_SIMULATE leftover remains the published bind.",
                    "10. Delayed missed_window_s=1080 (18 min assay window) while S7 waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "pf5_3p4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pf5_tph", 3.4),
                        ("hold", False),
                        ("bound_tag_mode", "PROCESS"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 86.0),
                        ("trip_C", 118.0),
                        ("shadow_C", 142.0),
                        ("mode_live", "PROCESS"),
                        ("mode_bound", "PROCESS"),
                        ("mode_simulate", False),
                        ("sim_tag_is_pv", False),
                        ("pv_live", True),
                        ("proposed_pf5_tph", 3.4),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 56),
                        ("missed_window_s", 1080),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 3.4 t/h PF5 because live MODE_PROCESS 86.0 C is under the "
                "118.0 C trip; 142.0 C is leftover MODE_SIMULATE engineering inject on the same "
                "tag, not the live still-base.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Leftover MODE_SIMULATE inject still prints 142.0 C, over the 118.0 C trip "
                "once the supervisor treats the simulation-mode EU as live. REJECT: hold PF5 "
                "0.0 t/h until the tag recovers under 118 so the still does not see an over-temp.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "still_C",
                            OrderedDict(
                                [
                                    ("published_live_trip", 118.0),
                                    ("observed_live", 86.0),
                                    ("misbound_shadow_C", 142.0),
                                    ("mode_live", "PROCESS"),
                                    ("mode_bound", "SIMULATE"),
                                    ("mode_simulate", True),
                                    ("sim_tag_is_pv", True),
                                    ("executed_pf5_tph", 0.0),
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
            ("name", "pf5_hold_sim_tag"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pf5_tph", 0.0),
                        ("hold", True),
                        ("bound_tag_mode", "SIMULATE"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): PF5 3.4 -> 0.0 t/h. Routing relay.sim.tag -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live 86.0 C never "
                "violated the 118.0 C trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze Still-S7 at 0.0 t/h while live still-base stayed 86.0 C under the "
                "118.0 C trip. 18 min assay window missed. Correct gate was ACCEPT of "
                "the already-legal 3.4 t/h feed.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("pf5", "held at 0.0 t/h; 3.4 t/h abandoned"),
                        ("live_C", "still 86.0 C, under 118.0 C published trip"),
                        ("still", "18 min assay window missed"),
                        ("tag", "142.0 C MODE_SIMULATE false positive, not a live over-trip"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 142.0 C reading is leftover MODE_SIMULATE engineering inject, not a published live over-trip.",
                    "Delayed (missed_window_s=1080): sister Still-S8 ran the same 3.4 t/h assay window after QA cleared MODE_SIMULATE; S7's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live 86.0 C < published 118.0 C trip; leave 3.4 t/h; bind live MODE_PROCESS.",
                        ),
                        ("correct_trip_C", 118.0),
                        ("wrong_shadow_C", 142.0),
                        ("bound_mode_should_be", "PROCESS"),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [("pf5_tph", 0.0), ("hold", True), ("bound_tag_mode", "SIMULATE")]
                            ),
                        ),
                        (
                            "cost",
                            "18 min missed assay window (task/efficiency); live S7 never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "live.still.C (4.400 ms, 86.0 C LIVE MODE_PROCESS)"),
                        ("loser", "stale.sim.eu (4.580 ms, 142.0 C STALE MODE_SIMULATE)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Sim-tag-first by < 180 us would still show live 86.0 C < 118.0 C. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the live-mode "
                            "win on a leftover MODE_SIMULATE inject.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5100),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (5.100 ms, tick 4). The 18 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 1080.0),
            ("missed_window_s", 1080),
        ]
    )
    ras = raster_core(
        32,
        88,
        28,
        79,
        routing(
            "relay.sim.tag",
            "policy.hold_reject",
            [
                ("relay.sim.tag", "policy.hold_reject", 0.76),
                ("relay.live.still", "policy.hold_reject", 0.16),
            ],
            "acetylcholine",
            0.06,
            "sim_tag_stdp; ACh tags the (wrong) hold_reject bind at the leftover MODE_SIMULATE shadow",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("missed_window_s", 1080),
                ("delayed_surprise_s", 1080),
                ("mode_simulate", True),
                ("sim_tag_is_pv", True),
                ("shadow_C", 142.0),
                ("live_C", 86.0),
                ("mode_bound", "SIMULATE"),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.34),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 48, 0.50, 245.1, 4),
                    pop("go_accept", 48, 0.80, 6.1, 0),
                    pop("sim_ctx", 26, 0.55, 113.1, 1),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r102-527",
        "WRONG-REJECT at Hexaflu-Rigg HF-7 / Still-S7: live MODE_PROCESS 86.0 C < 118.0 C trip; "
        "supervisor bound leftover MODE_SIMULATE inject (142.0 C) as the live still-base",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 86.0 < 118.0 on live S7 is true; clamp bound "
        "to a 142.0 C leftover MODE_SIMULATE shadow. total -0.58 = -0.20 + -0.12 + -0.22 + -0.10 + 0.06.",
        ras,
        gate,
        "lithium-hexafluorophosphate-still",
        [
            "reject",
            "wrong-gate",
            "simulation-tag-as-live",
            "mode-simulate-as-pv",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed on a leftover MODE_SIMULATE tag.",
        2,
        supervisor_error_type="wrong-reject",
    )


def record_528():
    ticks = [
        tick(2180, 0.01, 0.06, 0.01, 0.01, 0.01),
        tick(5240, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5440, 0.02, 0.07, 0.02, 0.02, 0.01),
        tick(6080, 0.03, 0.12, 0.04, 0.03, 0.02),
        tick(7920, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(510000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("ir.shower.ctx", 1.040, 0.44),
        spike("ae.wafer.pps", 2.180, 0.63),
        spike("ir.shower.C", 3.640, 0.50),
        spike("ae.wafer.pps", 5.240, 1.36),
        spike("ir.shower.C", 5.440, 1.13),
        spike("ctrl.gate", 6.080, 1.04),
        spike("ae.wafer.pps", 7.920, 0.78),
        spike("ir.shower.ctx", 12.100, 0.45),
        spike("ir.shower.C", 16.200, 0.59),
        spike("ctrl.gate", 20.800, 0.82),
        spike("ae.wafer.pps", 26.400, 0.51),
        spike("ir.shower.C", 31.600, 0.47),
        spike("ae.wafer.ctx", 34.200, 0.41),
    ]
    excerpt = independent_excerpt(102528, 104, 36000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Showerhead-W4 on Tunghex-Swale TW-HIL is armed for 180 sccm WF6 while "
                "wafer AE sits at 44 pps against a 12 pps crack floor. A shower pyrometer, lit by the "
                "pad lamp spectrum, still reports 410 C under a 480 C shower cap. AE-first holds "
                "the showerhead; IR-first would commit 180 sccm into a cracked wafer.",
            ),
            ("domain", "tungsten-hexafluoride-cvd"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Run W4 only if wafer AE stays <= 12 pps; otherwise hold so a cracked WF6 wafer is "
                "not loaded at 180 sccm.",
            ),
            ("t0_us", 1756850400000528),
            ("gate_latency_us", 840),
            ("race_window_us", 400),
            ("race_window_rel_ms", [5.20, 5.60]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.wafer.pps 44 pps wafer crack",
                                "ir.shower.C 410 C pad-lamp glint",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches shower hold 180 -> 0 sccm; IR-first would commit "
                            "180 sccm on a still-legal 410 C shower-cap story.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one wafer-AE slot versus shower-IR decode on this HIL CVD bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 200 us vs combined jitter ~62 us (AE 28 + IR 34): 3.2x over "
                            "a 2.0x trust floor. Reversing order by < 200 us inside the 400 us "
                            "window would have committed 180 sccm into a 44 pps wafer crack.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "wafer AE puck, 5 kHz, 28 us jitter",
                    "shower IR camera, 200 Hz, 34 us jitter",
                    "MFC encoder (context)",
                    "chamber PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_crack_floor_pps", 12.0),
                        ("observed_ae_pps", 44.0),
                        ("shower_cap_C", 480.0),
                        ("observed_shower_C", 410.0),
                        ("proposed_wf6_sccm", 180.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Showerhead-W4 indexed on Tunghex-Swale TW-HIL; WF6 180 sccm armed.",
                    "2. Shower IR 410 C under 480 C cap; AE already 44 pps.",
                    "3. IR-context precursor at 1.040 ms.",
                    "4. Race window [5.200, 5.600] ms.",
                    "5. ae.wafer.pps 44 pps at 5.240 ms (winner).",
                    "6. ir.shower.C 410 C at 5.440 ms (loser by 200 us).",
                    "7. Gate at 6.080 ms: REJECT hold shower 0 sccm.",
                    "8. Pass cancelled; wafer crack not loaded.",
                    "9. HIL pad lamp spectrum remains the shower glint source.",
                    "10. Delayed (abort_s=510): 8.5 min wafer re-seat before the next shower.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "wf6_180"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("wf6_sccm", 180.0),
                        ("hold", False),
                        ("wafer", "W4"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 44.0),
                        ("ae_crack_floor_pps", 12.0),
                        ("shower_C", 410.0),
                        ("shower_cap_C", 480.0),
                        ("race_margin_us", 200),
                        ("combined_jitter_us", 62),
                        ("abort_s", 510),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 180 sccm because shower 410 C is under the 480 C "
                "cap and treats the AE puck as chamber noise.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Wafer AE 44 pps won by 200 us, so the wafer is cracking, not still quiet. "
                "44 pps > 12 pps floor. REJECT: hold shower 180 -> 0 sccm. Shower 410 C < 480 C "
                "does not license the pass once AE is over floor.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "wafer_ae_pps",
                            OrderedDict(
                                [
                                    ("floor", 12.0),
                                    ("observed", 44.0),
                                    ("executed_wf6_sccm", 0.0),
                                ]
                            ),
                        ),
                        (
                            "shower_C",
                            OrderedDict(
                                [
                                    ("cap", 480.0),
                                    ("observed", 410.0),
                                    ("does_not_license_pass", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 200),
                                    ("combined_jitter_us", 62),
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
            ("name", "wafer_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("wf6_sccm", 0.0),
                        ("hold", True),
                        ("wafer", "W4"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (correct): shower 180 -> 0 sccm. Routing relay.ae.wafer -> "
                "policy.wafer_hold. Wafer crack is not loaded.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held W4 at 0 sccm. AE 44 pps beat shower 410 C; wafer "
                "was already over the 12 pps crack floor. 8.5 min re-seat follows (abort_s=510).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("shower", "held at 0 sccm; 180 sccm abandoned"),
                        ("wafer", "44 pps crack not loaded"),
                        ("ir", "410 C still under 480 C cap"),
                        ("reseat", "8.5 min wafer re-seat queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Shower IR 410 C was a HIL pad-lamp glint, not a shower-cap exceedance.",
                    "Delayed (abort_s=510): 8.5 min wafer re-seat before the next shower on TW-HIL.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.wafer.pps (5.240 ms, 44 pps)"),
                        ("loser", "ir.shower.C (5.440 ms, 410 C)"),
                        ("margin_us", 200),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 200 us would have committed 180 sccm into a wafer "
                            "already at 44 pps. The REJECT is still the correct process; AE is the "
                            "licensing channel, not shower IR.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6080),
            (
                "reward_inflection_note",
                "Safety and task credit the correct REJECT at 6.080 ms (tick 4). The 8.5 min "
                "re-seat is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 510.0),
            ("abort_s", 510),
        ]
    )
    ras = raster_core(
        36,
        104,
        22,
        82,
        routing(
            "thalamic-relay.wafer-ae",
            "spikenaut.policy.wafer-hold",
            [
                ("relay.ae.wafer", "policy.wafer_hold", 0.69),
                ("relay.ir.shower", "policy.wafer_commit", 0.27),
                ("relay.ae.wafer", "policy.wafer_hold", 0.11),
            ],
            "dopamine",
            0.07,
            "ae_floor_stdp; DA at wafer win (5.240 ms) opens a 70 ms eligibility trace",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 510),
                ("delayed_surprise_s", 510),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("wafer_hold", 52, 0.50, 240.4, 5),
                    pop("wafer_commit", 52, 0.50, 48.1, 1),
                    pop("ae_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r102-528",
        "Tunghex-Swale TW-HIL / Showerhead-W4: wafer AE 44 pps beats shower 410 C; correct "
        "REJECT holds the WF6 shower",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 44 pps > 12 pps floor beats a legal shower IR. "
        "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "tungsten-hexafluoride-cvd",
        ["reject", "hil", "wafer-ae", "wf6-cvd", "correct-gate"],
        "Teaches a wafer-AE vs pad-lamp-glint race on a HIL WF6 shower: the crack floor, "
        "not the shower cap, licenses the pass.",
        3,
    )


def record_529():
    ticks = [
        tick(1640, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(3960, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(4120, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(4500, 0.12, 0.09, 0.05, 0.03, 0.02),
        tick(6380, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(390000000, 0.03, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.kiln.ctx", 0.820, 0.42),
        spike("rtd.bed.C", 1.640, 0.59),
        spike("ir.bed.smear", 2.780, 0.48),
        spike("rtd.bed.C", 3.960, 1.29),
        spike("ir.bed.smear", 4.120, 1.11),
        spike("ctrl.gate", 4.500, 0.98),
        spike("rtd.bed.C", 6.380, 0.73),
        spike("enc.kiln.ctx", 10.400, 0.45),
        spike("ir.bed.smear", 14.200, 0.56),
        spike("ctrl.gate", 18.600, 0.81),
        spike("rtd.bed.C", 23.400, 0.50),
    ]
    excerpt = independent_excerpt(102529, 64, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Tunnel-K9 of Strontia-Keld SK-4 is already at 1180 C bed while a "
                "pyrometer smear still reports as 1410 C against a 1280 C cap the live RTD "
                "has not crossed. Bed-first should ACCEPT 2.4 t/h SrTiO3 sinter; smear-first would "
                "invent a hold on an already-legal tunnel pass.",
            ),
            ("domain", "strontium-titanate-sinter"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Run SK-4 at 2.4 t/h while bed stays <= 1280 C; do not spend a pyrometer "
                "smear on the kiln hold.",
            ),
            ("t0_us", 1756850400000529),
            ("gate_latency_us", 540),
            ("race_window_us", 300),
            ("race_window_rel_ms", [3.92, 4.22]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bed.C 1180 C live",
                                "ir.bed.smear as 1410 C",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first should ACCEPT 2.4 t/h (1180 C < 1280 C cap). "
                            "Smear-first would hold on a simulated kiln-film.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one bed-RTD sample versus pyrometer decode on this "
                            "sinter bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter ~50 us (RTD 22 + IR 28): 3.2x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 300 us "
                            "window would have invented a hold on an already-legal 1180 C bed.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed RTD, 4 kHz, 22 us jitter",
                    "pyrometer, 200 Hz, 28 us jitter",
                    "hearth encoder (context)",
                    "SrTiO3 load cell (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 1280.0),
                        ("observed_bed_C", 1180.0),
                        ("pyro_smear_C", 1410.0),
                        ("proposed_sinter_tph", 2.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Tunnel-K9 indexed on Strontia-Keld SK-4; sinter 2.4 t/h armed.",
                    "2. Bed 1180 C; pyrometer smear as 1410 C over 1280 C cap.",
                    "3. Kiln-encoder precursor at 0.820 ms.",
                    "4. Race window [3.920, 4.220] ms.",
                    "5. rtd.bed.C 1180 C at 3.960 ms (winner).",
                    "6. ir.bed.smear at 4.120 ms (loser by 160 us).",
                    "7. Gate at 4.500 ms: ACCEPT leave 2.4 t/h.",
                    "8. Bed remains 1180 C < 1280 C; smear unused as a hold.",
                    "9. Simulated kiln film remains the IR source.",
                    "10. Delayed (survey_hold_s=390): 6.5 min density survey after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "sinter_2p4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("sinter_tph", 2.4),
                        ("hold", False),
                        ("bed_C", 1180.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 1180.0),
                        ("bed_cap_C", 1280.0),
                        ("pyro_smear_C", 1410.0),
                        ("proposed_sinter_tph", 2.4),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 50),
                        ("survey_hold_s", 390),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.4 t/h because bed 1180 C is under the 1280 C cap; "
                "1410 C is a pyrometer smear, not a bed temperature.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 1180 C won by 160 us and sits under the 1280 C cap. Pyrometer smear "
                "1410 C is a simulated film, not a bed reading. ACCEPT: leave 2.4 t/h. "
                "A hold would idle a legal sinter pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 1280.0),
                                    ("observed", 1180.0),
                                    ("executed_sinter_tph", 2.4),
                                ]
                            ),
                        ),
                        (
                            "pyro_smear_C",
                            OrderedDict(
                                [
                                    ("observed", 1410.0),
                                    ("not_a_bed_reading", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 160),
                                    ("combined_jitter_us", 50),
                                    ("ratio", 3.20),
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
            ("name", "sinter_2p4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("sinter_tph", 2.4),
                        ("hold", False),
                        ("bed_C", 1180.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 2.4 t/h. Routing relay.rtd.bed -> policy.sinter_go. "
                "Pyrometer unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left SK-4 at 2.4 t/h. Bed 1180 C beat pyrometer smear 1410 C; "
                "the 1280 C cap was never crossed. 6.5 min density survey follows "
                "(survey_hold_s=390).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("sinter", "2.4 t/h held as proposed"),
                        ("bed", "1180 C < 1280 C cap"),
                        ("smear", "1410 C film unused"),
                        ("survey", "6.5 min density survey queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "IR 1410 C was a simulated kiln-film smear, not a bed over-cap.",
                    "Delayed (survey_hold_s=390): 6.5 min density survey after the pass on SK-4.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.C (3.960 ms, 1180 C)"),
                        ("loser", "ir.bed.smear (4.120 ms, smear 1410 C)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Smear-first by < 160 us would still be a kiln film over the "
                            "1280 C cap; a correct gate ACCEPTs either way. Reversing would only "
                            "have delayed confirmation of the same legal bed.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4500),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 4.500 ms (tick 4). The 6.5 min "
                "survey is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 390.0),
            ("survey_hold_s", 390),
        ]
    )
    ras = raster_core(
        26,
        64,
        36,
        60,
        routing(
            "thalamic-relay.bed-rtd",
            "spikenaut.policy.sinter-go",
            [
                ("relay.rtd.bed", "policy.sinter_go", 0.71),
                ("relay.ir.bed", "policy.smear_hold", 0.21),
                ("relay.rtd.bed", "policy.sinter_go", 0.10),
            ],
            "serotonin",
            0.04,
            "already_legal_stdp; 5-HT at bed win (3.960 ms) tags the go bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_hold_s", 390),
                ("delayed_surprise_s", 390),
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
                    pop("sinter_go", 38, 0.50, 263.2, 3),
                    pop("smear_hold", 38, 0.80, 8.8, 0),
                    pop("rtd_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r102-529",
        "Strontia-Keld SK-4 / Tunnel-K9: bed 1180 C beats pyrometer smear; correct ACCEPT "
        "of an already-legal 2.4 t/h (total +1.10)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Bed 1180 C < 1280 C cap; pyrometer smear unused. "
        "total +1.10 = 0.42 + 0.30 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "strontium-titanate-sinter",
        ["accept", "simulated-smear", "bed-vs-pyro", "srtio3-sinter", "simulated"],
        "Teaches that a pyrometer smear can lose to a legal bed RTD inside a "
        "300 us window; reversing 160 us would have invented a hold on an already-legal kiln.",
        4,
    )


def record_530():
    ticks = [
        tick(1820, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(4840, 0.09, 0.06, 0.04, 0.03, 0.02),
        tick(5020, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(5480, 0.12, 0.09, 0.05, 0.03, 0.02),
        tick(7640, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(450000000, 0.04, 0.04, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.n2h4.ctx", 0.960, 0.43),
        spike("rtd.tray.C", 1.820, 0.60),
        spike("ir.ovhd.smear", 3.080, 0.49),
        spike("rtd.tray.C", 4.840, 1.31),
        spike("ir.ovhd.smear", 5.020, 1.12),
        spike("ctrl.gate", 5.480, 1.00),
        spike("rtd.tray.C", 7.640, 0.75),
        spike("ir.ovhd.smear", 11.000, 0.57),
        spike("ctrl.gate", 14.400, 0.83),
        spike("ft.n2h4.ctx", 17.200, 0.44),
        spike("rtd.tray.C", 21.600, 0.52),
    ]
    excerpt = independent_excerpt(102530, 54, 24000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Column-H2 at Hydraz-Sike HS-2 is circulating 1.8 t/h hydrazine hydrate at 78 C "
                "against a 92 C tray cap. Overhead IR smear sits at 104 C over that cap while "
                "the live tray RTD has not crossed it. Tray-first should ACCEPT the already-legal "
                "1.8 t/h set; vapor-first would only delay confirmation of the same legal column.",
            ),
            ("domain", "hydrazine-hydrate-column"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 1.8 t/h on H2 while tray stays <= 92 C; do not spend an overhead-IR "
                "smear on the column hold.",
            ),
            ("t0_us", 1756850400000530),
            ("gate_latency_us", 640),
            ("race_window_us", 360),
            ("race_window_rel_ms", [4.80, 5.16]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.tray.C 78 C live",
                                "ir.ovhd.smear 104 C glint",
                            ],
                        ),
                        (
                            "semantics",
                            "Tray-first should ACCEPT 1.8 t/h (78 C < 92 C cap). "
                            "Vapor-first would only delay confirmation of the same legal column.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one tray-RTD slot versus overhead-IR group delay on this "
                            "hydrazine bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter ~56 us (RTD 24 + IR 32): 3.2x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would still show live tray under cap; ACCEPT either way.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "tray RTD, 2 kHz, 24 us jitter",
                    "overhead IR camera, 1 kHz, 32 us jitter",
                    "N2H4 FT (context)",
                    "reflux FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("tray_cap_C", 92.0),
                        ("observed_tray_C", 78.0),
                        ("overhead_smear_C", 104.0),
                        ("proposed_n2h4_tph", 1.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Column-H2 indexed on Hydraz-Sike HS-2; N2H4 1.8 t/h armed.",
                    "2. Tray 78 C; overhead IR smear 104 C over 92 C cap.",
                    "3. N2H4-FT precursor at 0.960 ms.",
                    "4. Race window [4.800, 5.160] ms.",
                    "5. rtd.tray.C 78 C at 4.840 ms (winner).",
                    "6. ir.ovhd.smear 104 C at 5.020 ms (loser by 180 us).",
                    "7. Gate at 5.480 ms: ACCEPT leave 1.8 t/h.",
                    "8. Tray remains 78 C < 92 C; vapor unused as a hold.",
                    "9. Hydrazine hydrate continues.",
                    "10. Delayed (dwell_s=450): 7.5 min assay dwell after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "n2h4_1p8"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("n2h4_tph", 1.8),
                        ("hold", False),
                        ("reflux_ratio", 2.4),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("tray_C", 78.0),
                        ("tray_cap_C", 92.0),
                        ("overhead_smear_C", 104.0),
                        ("proposed_n2h4_tph", 1.8),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 56),
                        ("dwell_s", 450),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.8 t/h because tray 78 C is under the 92 C cap "
                "and overhead 104 C is a headspace-IR smear, not a tray temperature.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Tray 78 C won by 180 us and sits under the 92 C cap. Overhead smear "
                "104 C is unused as a hold. ACCEPT: leave 1.8 t/h. A hold would idle a legal column.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tray_C",
                            OrderedDict(
                                [
                                    ("cap", 92.0),
                                    ("observed", 78.0),
                                    ("executed_n2h4_tph", 1.8),
                                ]
                            ),
                        ),
                        (
                            "overhead_smear_C",
                            OrderedDict(
                                [
                                    ("observed", 104.0),
                                    ("under_cap_unused", True),
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
            ("name", "n2h4_1p8"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("n2h4_tph", 1.8),
                        ("hold", False),
                        ("reflux_ratio", 2.4),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 1.8 t/h. Routing relay.rtd.tray -> policy.col_go. "
                "Overhead unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left H2 at 1.8 t/h. Tray 78 C beat overhead smear 104 C; both "
                "caps held. 7.5 min assay dwell follows (dwell_s=450).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("n2h4", "1.8 t/h held as proposed"),
                        ("tray", "78 C < 92 C cap"),
                        ("overhead", "104 C smear unused"),
                        ("survey", "7.5 min assay dwell queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Overhead IR 104 C was never a cap; it only lost the race to a legal tray RTD.",
                    "Delayed (dwell_s=450): 7.5 min assay dwell after the pass on HS-2.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.tray.C (4.840 ms, 78 C)"),
                        ("loser", "ir.ovhd.smear (5.020 ms, 104 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Vapor-first by < 180 us would still be a smear over the 92 C cap; "
                            "a correct gate ACCEPTs either way. Reversing would only have delayed "
                            "confirmation of the same legal column.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5480),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 5.480 ms (tick 4). The 7.5 min "
                "dwell is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 450.0),
            ("dwell_s", 450),
        ]
    )
    ras = raster_core(
        24,
        54,
        40,
        52,
        routing(
            "thalamic-relay.tray-rtd",
            "spikenaut.policy.col-go",
            [
                ("relay.rtd.tray", "policy.col_go", 0.70),
                ("relay.ir.ovhd", "policy.vapor_hold", 0.23),
                ("relay.rtd.tray", "policy.col_go", 0.10),
            ],
            "adenosine",
            0.08,
            "already_legal_stdp; adenosine at tray win (4.840 ms) tags the go bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("dwell_s", 450),
                ("delayed_surprise_s", 450),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("col_go", 34, 0.50, 245.1, 3),
                    pop("vapor_hold", 34, 0.80, 8.2, 0),
                    pop("rtd_veto", 16, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r102-530",
        "Hydraz-Sike HS-2 / Column-H2: tray 78 C beats overhead smear 104 C; correct ACCEPT "
        "of an already-legal 1.8 t/h (total +1.14)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Tray 78 C < 92 C cap; overhead unused. "
        "total +1.14 = 0.44 + 0.32 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "hydrazine-hydrate-column",
        ["accept", "designed", "tray-vs-vapor", "already-legal", "hydrazine"],
        "Teaches an already-legal hydrazine hydrate column: live tray sits under cap; "
        "race order only confirms the ACCEPT.",
        5,
    )
