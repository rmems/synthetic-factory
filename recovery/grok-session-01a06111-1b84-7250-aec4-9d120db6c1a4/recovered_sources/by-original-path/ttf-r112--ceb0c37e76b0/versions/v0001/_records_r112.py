def lif_576_excerpt():
    n = 82
    dt_us = 100
    tau_m_ms = 16.5
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.87
    i_stim_peak = 2.62
    stim = (21800, 25600)
    seed = 112576
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
    pack = [(t, nid) for t, nid in picked if t >= 21800][:9]
    picked = sorted(clamp + pack, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(
            f"LIF excerpt too short {len(picked)} (early={len(early)} burst={len(burst)})"
        )
    channels = ["lif.clamp" if t < 21800 else "lif.pack" for t, _ in picked]
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
            ("seed", 112576),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-19 carry +0.68 caustic-clamp bias; stim 21.8-25.6 ms is the packing gassing.",
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


def record_576():
    excerpt, extra = lif_576_excerpt()
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
                "Packed-S8 at Ruthetox-Whinfall RW-4 is already metering 5.1 t/h caustic liquor into a 61 C "
                "sump against a 54 C packing-habit cap. A liquor-first latch clamps the caustic; "
                "a feed-first story would keep the 5.1 t/h cruise. Stored Raschig-ring strain is not "
                "yet an observable of either race channel.",
            ),
            ("domain", "ruthenium-tetroxide-scrubber"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the RW-4 packed pass, keep liquor hotspot <= 54 C, and leave the "
                "Raschig packing unmarked.",
            ),
            ("t0_us", 1756850400000576),
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
                                "rtd.liquor.C 61 C pulse",
                                "ft.caustic.tph 5.1 t/h cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Liquor-first latches caustic 5.1 -> 2.8 t/h; feed-first keeps "
                            "cruise on a still-cooling packed-tower model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one 2 kHz liquor-RTD sample minus caustic-orifice group delay "
                            "on this packed-tower bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter ~58 us (liquor 28 + caustic 30): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 380 us window "
                            "would have kept 5.1 t/h cruise; predicted next-sample 57 C > 54 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "liquor multiplex RTD, 2 kHz, 28 us timestamp jitter",
                    "caustic feed FT, 1 kHz, 30 us jitter",
                    "packing AE puck (context until the gassing)",
                    "RuO4 assay (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("liquor_cap_C", 54.0),
                        ("observed_liquor_C", 61.0),
                        ("proposed_caustic_tph", 5.1),
                        ("ruo4_wt_pct", 8.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Packed-S8 indexed on Ruthetox-Whinfall RW-4; caustic armed at 5.1 t/h.",
                    "2. Cruise 5.1 t/h; liquor 61 C against 54 C packing-habit cap.",
                    "3. Caustic precursor at 1.180 ms; liquor warm-start 61 C.",
                    "4. Race window [6.100, 6.480] ms opens on the packed-tower bus.",
                    "5. rtd.liquor.C 61 C at 6.140 ms (winner).",
                    "6. ft.caustic.tph 5.1 t/h at 6.320 ms (loser by 180 us).",
                    "7. Gate at 6.880 ms (winner + 740 us): MODIFY clamp 5.1 -> 2.8 t/h.",
                    "8. Clamp executes; next-sample liquor 50 C < 54 cap.",
                    "9. At 23.200 ms stored strain still gasses 12 mm of Raschig packing; AE burst.",
                    "10. Liquor isolate 16 min (abort_s=960); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_caustic_5p1"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("caustic_tph", 5.1),
                        ("ruo4_wt_pct", 8.4),
                        ("blower_rpm", 22.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("liquor_C", 61.0),
                        ("liquor_cap_C", 54.0),
                        ("predicted_unclamped_next_C", 57.0),
                        ("caustic_tph", 5.1),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 960),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 5.1 t/h cruise: 61 C looks like an RuO4-assay spike, not "
                "packing contact, and S8 volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Liquor 61 C won by 180 us, so the packing is loading heat, not still cooling. "
                "Holding 5.1 t/h predicts next-sample 57 C > 54 cap. MODIFY: caustic 5.1 -> "
                "2.8 t/h. Observed after clamp 50 C < 54. A full REJECT is not indicated: a "
                "sound packed pass accepts 2.8 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "liquor_C",
                            OrderedDict(
                                [
                                    ("cap", 54.0),
                                    ("observed", 61.0),
                                    ("predicted_unclamped_next", 57.0),
                                    ("clamped_caustic_tph", 2.8),
                                    ("observed_after_clamp", 50.0),
                                ]
                            ),
                        ),
                        (
                            "caustic_tph",
                            OrderedDict([("proposed", 5.1), ("clamped", 2.8)]),
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
            ("name", "clamped_caustic_2p8"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("caustic_tph", 2.8),
                        ("ruo4_wt_pct", 8.4),
                        ("blower_rpm", 22.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: caustic 5.1 -> 2.8 t/h. Process-correct vs the 54 C packing-habit "
                "cap. Packing gassing still occurs at 23.200 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held liquor at 50 C. At 23.200 ms stored strain "
                "in the Raschig packing still gassed a 12 mm face. Clamp reduced dump energy; "
                "it did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("caustic", "clamp executed; peak 50 C < 54"),
                        ("packing", "12 mm gassing at 23.200 ms"),
                        ("repair", "16 min liquor isolate (abort_s=960)"),
                        ("mission", "RW-4 packed pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither liquor RTD nor caustic FT predicted the packing charge; ae.pack.collapse is a new channel at 23.200 ms, 16.320 ms after the gate, still inside the 48 ms raster.",
                    "Delayed (abort_s=960): 16 min liquor isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "16 min liquor isolate after a 12 mm Raschig packing gassing collapse. Safety head -0.62 "
                "prices the split; task_progress stays +0.32 because the caustic clamp completed "
                "under the 54 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.liquor.C (6.140 ms, 61 C)"),
                        ("loser", "ft.caustic.tph (6.320 ms, 5.1 t/h)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Feed-first by < 180 us inside the 380 us window would have kept "
                            "5.1 t/h cruise; predicted next-sample 57 C would have exceeded "
                            "the 54 cap even without the packing charge. The MODIFY is still the "
                            "correct process. The collapse is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 23200),
            (
                "reward_inflection_note",
                "Safety collapses at the 23.200 ms packing gassing (tick t_us=23200), inside "
                "the 48 ms raster. The correct MODIFY at 6.880 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=960 isolate tick.",
            ),
            ("delayed_surprise_s", 960.0),
            ("abort_s", 960),
        ]
    )
    spikes = [
        spike("enc.ruo4.ctx", 1.180, 0.43),
        spike("rtd.liquor.C", 2.140, 0.62),
        spike("ft.caustic.tph", 3.520, 0.51),
        spike("rtd.liquor.C", 6.140, 1.34),
        spike("ft.caustic.tph", 6.320, 1.16),
        spike("ctrl.gate", 6.880, 0.99),
        spike("rtd.liquor.C", 8.420, 0.81),
        spike("ft.caustic.tph", 11.200, 0.63),
        spike("ctrl.gate", 15.600, 0.85),
        spike("ae.pack.collapse", 23.200, 1.48),
        spike("ae.pack.collapse", 25.100, 0.92),
        spike("enc.ruo4.ctx", 33.400, 0.42),
        spike("rtd.liquor.C", 42.800, 0.54),
    ]
    ras = raster_core(
        48,
        82,
        24,
        94,
        routing(
            "thalamic-relay.liquor-pack",
            "spikenaut.policy.caustic-clamp",
            [
                ("relay.rtd.liquor", "policy.caustic_clamp", 0.67),
                ("relay.ft.caustic", "policy.caustic_hold", 0.29),
                ("relay.ae.pack", "policy.caustic_clamp", -0.46),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at liquor win (6.140 ms) opens a 50 ms "
            "eligibility trace that still covers the 23.200 ms packing gassing",
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
                    pop("caustic_clamp", 46, 0.50, 229.0, 4),
                    pop("caustic_hold", 46, 0.50, 57.2, 1),
                    pop("ss_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r112-576",
        "Ruthetox-Whinfall RW-4 / Packed-S8: liquor 61 C beats caustic-feed by 180 us; correct "
        "MODIFY still eats an in-window packing gassing (partnered negative total -0.46)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "48 ms raster. total -0.46 = 0.32 + -0.62 + -0.16 + 0.04 + -0.04. Named liquor "
        "isolate (abort_s=960) is not netted into task_progress.",
        ras,
        gate,
        "ruthenium-tetroxide-scrubber",
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
        "16 min liquor isolate.",
        1,
    )


def record_577():
    ticks = [
        tick(1760, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(4400, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(4580, -0.03, -0.01, -0.03, -0.02, 0.01),
        tick(5100, -0.07, -0.06, -0.07, -0.04, 0.02),
        tick(7240, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(1080000000, -0.02, -0.01, -0.04, 0.00, 0.00),
    ]
    spikes = [
        spike("ft.taet.ctx", 0.880, 0.41),
        spike("live.kettle.C", 1.760, 0.59),
        spike("burnout.upscale.eu", 2.520, 0.52),
        spike("live.kettle.C", 4.400, 1.33),
        spike("burnout.upscale.eu", 4.580, 1.16),
        spike("ctrl.gate", 5.100, 1.01),
        spike("live.kettle.C", 7.240, 0.75),
        spike("burnout.upscale.eu", 8.320, 0.62),
        spike("ctrl.gate", 12.400, 0.83),
        spike("ft.taet.ctx", 16.200, 0.43),
        spike("live.kettle.C", 21.600, 0.54),
        spike("burnout.upscale.eu", 26.800, 0.48),
    ]
    excerpt = independent_excerpt(112577, 88, 32000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Kettle-T3 on Tantalox-Grainth TE-6 is holding tantalum-ethoxide at 2.6 t/h with live "
                "kettle-base 74.0 C against a 128.0 C trip. A leftover thermocouple burnout-upscale "
                "still prints 21.2 mA as 248.0 C from an open-circuit detect. Live-RTD-first should "
                "ACCEPT the feed; a weak supervisor that binds the burnout EU will REJECT a legal still.",
            ),
            ("domain", "tantalum-ethoxide-still"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep 2.6 t/h Ta(OEt)5 on Kettle-T3 while live kettle-base stays <= 128.0 C; "
                "do not spend a leftover TC burnout-upscale on the hold.",
            ),
            ("t0_us", 1756850400000577),
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
                                "live.kettle.C 74.0 C LIVE kettle RTD",
                                "burnout.upscale.eu 21.2 mA / 248.0 C leftover TC burnout",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-RTD-first should ACCEPT 2.6 t/h (74.0 C < 128.0 C trip). "
                            "Burnout-first tempts a weak supervisor to treat 248.0 C as live.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one Kettle-T3 RTD sample minus leftover burnout-upscale group delay "
                            "on this ethoxide bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter ~56 us (live 26 + burnout 30): 3.2x over "
                            "a 2.0x trust floor. Order is correctly live-RTD-first. The error is binding "
                            "the leftover burnout-upscale EU, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "Kettle-T3 base RTD, 4 kHz, 26 us jitter, LIVE analog",
                    "leftover TC burnout-upscale shadow, 4 kHz, 30 us jitter, open-circuit UPSCALE STALE",
                    "Ta(OEt)5 feed FT (context)",
                    "ethanol make-up FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("trip_C", 128.0),
                        ("live_C", 74.0),
                        ("shadow_C", 248.0),
                        ("burnout_mA", 21.2),
                        ("burnout_flag", True),
                        ("namur_fail_high", False),
                        ("proposed_taet_tph", 2.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Kettle-T3 latched on Tantalox-Grainth TE-6; Ta(OEt)5 2.6 t/h armed.",
                    "2. Live kettle 74.0 C; leftover TC burnout-upscale still prints 21.2 mA / 248.0 C.",
                    "3. Ta(OEt)5-FT precursor at 0.880 ms.",
                    "4. Race window [4.360, 4.700] ms.",
                    "5. live.kettle.C 74.0 C at 4.400 ms (winner).",
                    "6. burnout.upscale.eu 248.0 C at 4.580 ms (loser by 180 us).",
                    "7. Gate at 5.100 ms: REJECT hold 0.0 t/h (incorrect).",
                    "8. Legal feed cancelled; live kettle-base still 74.0 C < 128.0 C trip.",
                    "9. Burnout-upscale leftover remains the published bind.",
                    "10. Delayed missed_window_s=1080 (18 min assay window) while T3 waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "taet_2p6"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("taet_tph", 2.6),
                        ("hold", False),
                        ("bound_tag", "LIVE_RTD"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 74.0),
                        ("trip_C", 128.0),
                        ("shadow_C", 248.0),
                        ("burnout_mA", 21.2),
                        ("burnout_flag", True),
                        ("burnout_upscale_is_pv", False),
                        ("namur_fail_high", False),
                        ("tc_open_circuit", True),
                        ("pv_live", True),
                        ("proposed_taet_tph", 2.6),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 56),
                        ("missed_window_s", 1080),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.6 t/h Ta(OEt)5 because live kettle 74.0 C is under the "
                "128.0 C trip; 248.0 C is leftover TC burnout-upscale (21.2 mA through URV), "
                "not the live kettle-base.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Leftover TC burnout-upscale still prints 248.0 C, over the 128.0 C trip "
                "once the supervisor treats the burnout EU as live. REJECT: hold Ta(OEt)5 "
                "0.0 t/h until the tag recovers under 128 so the still does not see an over-temp.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "kettle_C",
                            OrderedDict(
                                [
                                    ("published_live_trip", 128.0),
                                    ("observed_live", 74.0),
                                    ("misbound_shadow_C", 248.0),
                                    ("burnout_mA", 21.2),
                                    ("burnout_flag", True),
                                    ("burnout_upscale_is_pv", True),
                                    ("namur_fail_high", False),
                                    ("executed_taet_tph", 0.0),
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
            ("name", "taet_hold_burnout"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("taet_tph", 0.0),
                        ("hold", True),
                        ("bound_tag", "BURNOUT_UPSCALE"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): Ta(OEt)5 2.6 -> 0.0 t/h. Routing relay.burnout.upscale -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live 74.0 C never "
                "violated the 128.0 C trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze Kettle-T3 at 0.0 t/h while live kettle-base stayed 74.0 C under the "
                "128.0 C trip. 18 min assay window missed. Correct gate was ACCEPT of "
                "the already-legal 2.6 t/h feed.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("taet", "held at 0.0 t/h; 2.6 t/h abandoned"),
                        ("live_C", "still 74.0 C, under 128.0 C published trip"),
                        ("still", "18 min assay window missed"),
                        ("tag", "21.2 mA / 248.0 C burnout-upscale false positive, not a live over-trip"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 248.0 C reading is leftover TC burnout-upscale (open-circuit UPSCALE), not a published live over-trip.",
                    "Delayed (missed_window_s=1080): sister Kettle-T4 ran the same 2.6 t/h assay window after QA cleared burnout; T3's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live 74.0 C < published 128.0 C trip; leave 2.6 t/h; bind live kettle RTD; drop burnout-upscale as PV.",
                        ),
                        ("correct_trip_C", 128.0),
                        ("wrong_shadow_C", 248.0),
                        ("bound_tag_should_be", "LIVE_RTD"),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [("taet_tph", 0.0), ("hold", True), ("bound_tag", "BURNOUT_UPSCALE")]
                            ),
                        ),
                        (
                            "cost",
                            "18 min missed assay window (task/efficiency); live T3 never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "live.kettle.C (4.400 ms, 74.0 C LIVE RTD)"),
                        ("loser", "burnout.upscale.eu (4.580 ms, 21.2 mA / 248.0 C STALE BURNOUT)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Burnout-first by < 180 us would still show live 74.0 C < 128.0 C. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the live-RTD "
                            "win on a leftover TC burnout-upscale.",
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
            "relay.burnout.upscale",
            "policy.hold_reject",
            [
                ("relay.burnout.upscale", "policy.hold_reject", 0.76),
                ("relay.live.kettle", "policy.hold_reject", 0.16),
            ],
            "acetylcholine",
            0.06,
            "burnout_upscale_stdp; ACh tags the (wrong) hold_reject bind at the leftover TC burnout shadow",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("missed_window_s", 1080),
                ("delayed_surprise_s", 1080),
                ("burnout_flag", True),
                ("burnout_upscale_is_pv", True),
                ("namur_fail_high", False),
                ("shadow_C", 248.0),
                ("live_C", 74.0),
                ("burnout_mA", 21.2),
                ("bound_tag", "BURNOUT_UPSCALE"),
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
                    pop("burnout_ctx", 26, 0.55, 113.1, 1),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r112-577",
        "WRONG-REJECT at Tantalox-Grainth TE-6 / Kettle-T3: live kettle 74.0 C < 128.0 C trip; "
        "supervisor bound leftover TC burnout-upscale (21.2 mA / 248.0 C) as the live kettle-base",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 74.0 < 128.0 on live T3 is true; clamp bound "
        "to a 248.0 C leftover TC burnout-upscale. total -0.58 = -0.20 + -0.12 + -0.22 + -0.10 + 0.06.",
        ras,
        gate,
        "tantalum-ethoxide-still",
        [
            "reject",
            "wrong-gate",
            "burnout-upscale-as-pv",
            "tc-open-circuit",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed on a leftover TC burnout-upscale.",
        2,
        supervisor_error_type="wrong-reject",
    )


def record_578():
    ticks = [
        tick(2180, 0.01, 0.06, 0.01, 0.01, 0.01),
        tick(5240, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5440, 0.02, 0.07, 0.02, 0.02, 0.01),
        tick(6080, 0.03, 0.12, 0.04, 0.03, 0.02),
        tick(7920, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(510000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("ir.bubbler.ctx", 1.040, 0.44),
        spike("ae.ampoule.pps", 2.180, 0.63),
        spike("ir.bubbler.C", 3.640, 0.50),
        spike("ae.ampoule.pps", 5.240, 1.36),
        spike("ir.bubbler.C", 5.440, 1.13),
        spike("ctrl.gate", 6.080, 1.04),
        spike("ae.ampoule.pps", 7.920, 0.78),
        spike("ir.bubbler.ctx", 12.100, 0.45),
        spike("ir.bubbler.C", 16.200, 0.59),
        spike("ctrl.gate", 20.800, 0.82),
        spike("ae.ampoule.pps", 26.400, 0.51),
        spike("ir.bubbler.C", 31.600, 0.47),
        spike("ae.ampoule.ctx", 34.200, 0.41),
    ]
    excerpt = independent_excerpt(112578, 104, 36000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Bubbler-I7 on Indichl-Sikebeck IS-HIL is armed for 95 sccm InCl3 while "
                "ampoule AE sits at 38 pps against a 10 pps crack floor. A bubbler pyrometer, lit by the "
                "pad lamp spectrum, still reports 390 C under a 460 C bubbler cap. AE-first holds "
                "the bubbler; IR-first would commit 95 sccm into a cracked ampoule.",
            ),
            ("domain", "indium-trichloride-bubbler"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Run I7 only if ampoule AE stays <= 10 pps; otherwise hold so a cracked InCl3 ampoule is "
                "not loaded at 95 sccm.",
            ),
            ("t0_us", 1756850400000578),
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
                                "ae.ampoule.pps 38 pps ampoule crack",
                                "ir.bubbler.C 390 C pad-lamp glint",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches bubbler hold 95 -> 0 sccm; IR-first would commit "
                            "95 sccm on a still-legal 390 C bubbler-cap story.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one ampoule-AE slot versus bubbler-IR decode on this HIL MOVPE bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 200 us vs combined jitter ~62 us (AE 28 + IR 34): 3.2x over "
                            "a 2.0x trust floor. Reversing order by < 200 us inside the 400 us "
                            "window would have committed 95 sccm into a 38 pps ampoule crack.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "ampoule AE puck, 5 kHz, 28 us jitter",
                    "bubbler IR camera, 200 Hz, 34 us jitter",
                    "MFC encoder (context)",
                    "carrier PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_crack_floor_pps", 10.0),
                        ("observed_ae_pps", 38.0),
                        ("bubbler_cap_C", 460.0),
                        ("observed_bubbler_C", 390.0),
                        ("proposed_incl3_sccm", 95.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Bubbler-I7 indexed on Indichl-Sikebeck IS-HIL; InCl3 95 sccm armed.",
                    "2. Bubbler IR 390 C under 460 C cap; AE already 38 pps.",
                    "3. IR-context precursor at 1.040 ms.",
                    "4. Race window [5.200, 5.600] ms.",
                    "5. ae.ampoule.pps 38 pps at 5.240 ms (winner).",
                    "6. ir.bubbler.C 390 C at 5.440 ms (loser by 200 us).",
                    "7. Gate at 6.080 ms: REJECT hold bubbler 0 sccm.",
                    "8. Pass cancelled; ampoule crack not loaded.",
                    "9. HIL pad lamp spectrum remains the bubbler glint source.",
                    "10. Delayed (abort_s=510): 8.5 min ampoule re-seat before the next bubbler.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "incl3_95"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("incl3_sccm", 95.0),
                        ("hold", False),
                        ("ampoule", "I7"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 38.0),
                        ("ae_crack_floor_pps", 10.0),
                        ("bubbler_C", 390.0),
                        ("bubbler_cap_C", 460.0),
                        ("race_margin_us", 200),
                        ("combined_jitter_us", 62),
                        ("abort_s", 510),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 95 sccm because bubbler 390 C is under the 460 C "
                "cap and treats the AE puck as carrier noise.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Ampoule AE 38 pps won by 200 us, so the ampoule is cracking, not still quiet. "
                "38 pps > 10 pps floor. REJECT: hold bubbler 95 -> 0 sccm. Bubbler 390 C < 460 C "
                "does not license the pass once AE is over floor.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ampoule_ae_pps",
                            OrderedDict(
                                [
                                    ("floor", 10.0),
                                    ("observed", 38.0),
                                    ("executed_incl3_sccm", 0.0),
                                ]
                            ),
                        ),
                        (
                            "bubbler_C",
                            OrderedDict(
                                [
                                    ("cap", 460.0),
                                    ("observed", 390.0),
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
            ("name", "ampoule_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("incl3_sccm", 0.0),
                        ("hold", True),
                        ("ampoule", "I7"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (correct): bubbler 95 -> 0 sccm. Routing relay.ae.ampoule -> "
                "policy.ampoule_hold. Ampoule crack is not loaded.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held I7 at 0 sccm. AE 38 pps beat bubbler 390 C; ampoule "
                "was already over the 10 pps crack floor. 8.5 min re-seat follows (abort_s=510).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bubbler", "held at 0 sccm; 95 sccm abandoned"),
                        ("ampoule", "38 pps crack not loaded"),
                        ("ir", "390 C still under 460 C cap"),
                        ("reseat", "8.5 min ampoule re-seat queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Bubbler IR 390 C was a HIL pad-lamp glint, not a bubbler-cap exceedance.",
                    "Delayed (abort_s=510): 8.5 min ampoule re-seat before the next bubbler on IS-HIL.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.ampoule.pps (5.240 ms, 38 pps)"),
                        ("loser", "ir.bubbler.C (5.440 ms, 390 C)"),
                        ("margin_us", 200),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 200 us would have committed 95 sccm into an ampoule "
                            "already at 38 pps. The REJECT is still the correct process; AE is the "
                            "licensing channel, not bubbler IR.",
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
            "thalamic-relay.ampoule-ae",
            "spikenaut.policy.ampoule-hold",
            [
                ("relay.ae.ampoule", "policy.ampoule_hold", 0.69),
                ("relay.ir.bubbler", "policy.ampoule_commit", 0.27),
                ("relay.ae.ampoule", "policy.ampoule_hold", 0.11),
            ],
            "dopamine",
            0.07,
            "ae_floor_stdp; DA at ampoule win (5.240 ms) opens a 70 ms eligibility trace",
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
                    pop("ampoule_hold", 52, 0.50, 240.4, 5),
                    pop("ampoule_commit", 52, 0.50, 48.1, 1),
                    pop("ae_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r112-578",
        "Indichl-Sikebeck IS-HIL / Bubbler-I7: ampoule AE 38 pps beats bubbler 390 C; correct "
        "REJECT holds the InCl3 bubbler",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 38 pps > 10 pps floor beats a legal bubbler IR. "
        "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "indium-trichloride-bubbler",
        ["reject", "hil", "ampoule-ae", "incl3-bubbler", "correct-gate"],
        "Teaches an ampoule-AE vs pad-lamp-glint race on a HIL InCl3 bubbler: the crack floor, "
        "not the bubbler cap, licenses the pass.",
        3,
    )


def record_579():
    ticks = [
        tick(1640, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(3960, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(4120, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(4500, 0.12, 0.09, 0.05, 0.03, 0.02),
        tick(6380, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(390000000, 0.03, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.hearth.ctx", 0.820, 0.42),
        spike("rtd.bed.C", 1.640, 0.59),
        spike("ir.bed.smear", 2.780, 0.48),
        spike("rtd.bed.C", 3.960, 1.29),
        spike("ir.bed.smear", 4.120, 1.11),
        spike("ctrl.gate", 4.500, 0.98),
        spike("rtd.bed.C", 6.380, 0.73),
        spike("enc.hearth.ctx", 10.400, 0.45),
        spike("ir.bed.smear", 14.200, 0.56),
        spike("ctrl.gate", 18.600, 0.81),
        spike("rtd.bed.C", 23.400, 0.50),
    ]
    excerpt = independent_excerpt(112579, 64, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Hearth-L2 of Lanthala-Braefell LA-8 is already at 1510 C bed while a "
                "pyrometer smear still reports as 1740 C against a 1620 C cap the live RTD "
                "has not crossed. Bed-first should ACCEPT 1.6 t/h LaAlO3 sinter; smear-first would "
                "invent a hold on an already-legal hearth pass.",
            ),
            ("domain", "lanthanum-aluminate-sinter"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Run LA-8 at 1.6 t/h while bed stays <= 1620 C; do not spend a pyrometer "
                "smear on the hearth hold.",
            ),
            ("t0_us", 1756850400000579),
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
                                "rtd.bed.C 1510 C live",
                                "ir.bed.smear as 1740 C",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first should ACCEPT 1.6 t/h (1510 C < 1620 C cap). "
                            "Smear-first would hold on a simulated hearth-film.",
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
                            "window would have invented a hold on an already-legal 1510 C bed.",
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
                    "LaAlO3 load cell (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 1620.0),
                        ("observed_bed_C", 1510.0),
                        ("pyro_smear_C", 1740.0),
                        ("proposed_sinter_tph", 1.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Hearth-L2 indexed on Lanthala-Braefell LA-8; sinter 1.6 t/h armed.",
                    "2. Bed 1510 C; pyrometer smear as 1740 C over 1620 C cap.",
                    "3. Hearth-encoder precursor at 0.820 ms.",
                    "4. Race window [3.920, 4.220] ms.",
                    "5. rtd.bed.C 1510 C at 3.960 ms (winner).",
                    "6. ir.bed.smear at 4.120 ms (loser by 160 us).",
                    "7. Gate at 4.500 ms: ACCEPT leave 1.6 t/h.",
                    "8. Bed remains 1510 C < 1620 C; smear unused as a hold.",
                    "9. Simulated hearth film remains the IR source.",
                    "10. Delayed (survey_hold_s=390): 6.5 min density survey after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "sinter_1p6"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("sinter_tph", 1.6),
                        ("hold", False),
                        ("bed_C", 1510.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 1510.0),
                        ("bed_cap_C", 1620.0),
                        ("pyro_smear_C", 1740.0),
                        ("proposed_sinter_tph", 1.6),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 50),
                        ("survey_hold_s", 390),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.6 t/h because bed 1510 C is under the 1620 C cap; "
                "1740 C is a pyrometer smear, not a bed temperature.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 1510 C won by 160 us and sits under the 1620 C cap. Pyrometer smear "
                "1740 C is a simulated film, not a bed reading. ACCEPT: leave 1.6 t/h. "
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
                                    ("cap", 1620.0),
                                    ("observed", 1510.0),
                                    ("executed_sinter_tph", 1.6),
                                ]
                            ),
                        ),
                        (
                            "pyro_smear_C",
                            OrderedDict(
                                [
                                    ("observed", 1740.0),
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
            ("name", "sinter_1p6"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("sinter_tph", 1.6),
                        ("hold", False),
                        ("bed_C", 1510.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 1.6 t/h. Routing relay.rtd.bed -> policy.sinter_go. "
                "Pyrometer unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left LA-8 at 1.6 t/h. Bed 1510 C beat pyrometer smear 1740 C; "
                "the 1620 C cap was never crossed. 6.5 min density survey follows "
                "(survey_hold_s=390).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("sinter", "1.6 t/h held as proposed"),
                        ("bed", "1510 C < 1620 C cap"),
                        ("smear", "1740 C film unused"),
                        ("survey", "6.5 min density survey queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "IR 1740 C was a simulated hearth-film smear, not a bed over-cap.",
                    "Delayed (survey_hold_s=390): 6.5 min density survey after the pass on LA-8.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.C (3.960 ms, 1510 C)"),
                        ("loser", "ir.bed.smear (4.120 ms, smear 1740 C)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Smear-first by < 160 us would still be a hearth film over the "
                            "1620 C cap; a correct gate ACCEPTs either way. Reversing would only "
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
        "ttf-r112-579",
        "Lanthala-Braefell LA-8 / Hearth-L2: bed 1510 C beats pyrometer smear; correct ACCEPT "
        "of an already-legal 1.6 t/h (total +1.10)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Bed 1510 C < 1620 C cap; pyrometer smear unused. "
        "total +1.10 = 0.42 + 0.30 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "lanthanum-aluminate-sinter",
        ["accept", "simulated-smear", "bed-vs-pyro", "laalo3-sinter", "simulated"],
        "Teaches that a pyrometer smear can lose to a legal bed RTD inside a "
        "300 us window; reversing 160 us would have invented a hold on an already-legal hearth.",
        4,
    )


def record_580():
    ticks = [
        tick(1820, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(4840, 0.09, 0.06, 0.04, 0.03, 0.02),
        tick(5020, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(5480, 0.12, 0.09, 0.05, 0.03, 0.02),
        tick(7640, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(450000000, 0.04, 0.04, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.b2h6.ctx", 0.960, 0.43),
        spike("rtd.tray.C", 1.820, 0.60),
        spike("ir.ovhd.smear", 3.080, 0.49),
        spike("rtd.tray.C", 4.840, 1.31),
        spike("ir.ovhd.smear", 5.020, 1.12),
        spike("ctrl.gate", 5.480, 1.00),
        spike("rtd.tray.C", 7.640, 0.75),
        spike("ir.ovhd.smear", 11.000, 0.57),
        spike("ctrl.gate", 14.400, 0.83),
        spike("ft.b2h6.ctx", 17.200, 0.44),
        spike("rtd.tray.C", 21.600, 0.52),
    ]
    excerpt = independent_excerpt(112580, 54, 24000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Tower-B4 at Diboran-Stoupside DB-3 is circulating 2.2 t/h diborane-cracker bottoms at 42 C "
                "against a 58 C tray cap. Overhead IR smear sits at 71 C over that cap while "
                "the live tray RTD has not crossed it. Tray-first should ACCEPT the already-legal "
                "2.2 t/h set; vapor-first would only delay confirmation of the same legal column.",
            ),
            ("domain", "diborane-cracker-column"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 2.2 t/h on B4 while tray stays <= 58 C; do not spend an overhead-IR "
                "smear on the column hold.",
            ),
            ("t0_us", 1756850400000580),
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
                                "rtd.tray.C 42 C live",
                                "ir.ovhd.smear 71 C glint",
                            ],
                        ),
                        (
                            "semantics",
                            "Tray-first should ACCEPT 2.2 t/h (42 C < 58 C cap). "
                            "Vapor-first would only delay confirmation of the same legal column.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one tray-RTD slot versus overhead-IR group delay on this "
                            "diborane-cracker bus.",
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
                    "B2H6 FT (context)",
                    "reflux FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("tray_cap_C", 58.0),
                        ("observed_tray_C", 42.0),
                        ("overhead_smear_C", 71.0),
                        ("proposed_b2h6_tph", 2.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Tower-B4 indexed on Diboran-Stoupside DB-3; B2H6 2.2 t/h armed.",
                    "2. Tray 42 C; overhead IR smear 71 C over 58 C cap.",
                    "3. B2H6-FT precursor at 0.960 ms.",
                    "4. Race window [4.800, 5.160] ms.",
                    "5. rtd.tray.C 42 C at 4.840 ms (winner).",
                    "6. ir.ovhd.smear 71 C at 5.020 ms (loser by 180 us).",
                    "7. Gate at 5.480 ms: ACCEPT leave 2.2 t/h.",
                    "8. Tray remains 42 C < 58 C; vapor unused as a hold.",
                    "9. Diborane cracker bottoms continue.",
                    "10. Delayed (dwell_s=450): 7.5 min assay dwell after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "b2h6_2p2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("b2h6_tph", 2.2),
                        ("hold", False),
                        ("reflux_ratio", 1.8),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("tray_C", 42.0),
                        ("tray_cap_C", 58.0),
                        ("overhead_smear_C", 71.0),
                        ("proposed_b2h6_tph", 2.2),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 56),
                        ("dwell_s", 450),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.2 t/h because tray 42 C is under the 58 C cap "
                "and overhead 71 C is a headspace-IR smear, not a tray temperature.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Tray 42 C won by 180 us and sits under the 58 C cap. Overhead smear "
                "71 C is unused as a hold. ACCEPT: leave 2.2 t/h. A hold would idle a legal column.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tray_C",
                            OrderedDict(
                                [
                                    ("cap", 58.0),
                                    ("observed", 42.0),
                                    ("executed_b2h6_tph", 2.2),
                                ]
                            ),
                        ),
                        (
                            "overhead_smear_C",
                            OrderedDict(
                                [
                                    ("observed", 71.0),
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
            ("name", "b2h6_2p2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("b2h6_tph", 2.2),
                        ("hold", False),
                        ("reflux_ratio", 1.8),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 2.2 t/h. Routing relay.rtd.tray -> policy.col_go. "
                "Overhead unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left B4 at 2.2 t/h. Tray 42 C beat overhead smear 71 C; both "
                "caps held. 7.5 min assay dwell follows (dwell_s=450).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("b2h6", "2.2 t/h held as proposed"),
                        ("tray", "42 C < 58 C cap"),
                        ("overhead", "71 C smear unused"),
                        ("survey", "7.5 min assay dwell queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Overhead IR 71 C was never a cap; it only lost the race to a legal tray RTD.",
                    "Delayed (dwell_s=450): 7.5 min assay dwell after the pass on DB-3.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.tray.C (4.840 ms, 42 C)"),
                        ("loser", "ir.ovhd.smear (5.020 ms, 71 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Vapor-first by < 180 us would still be a smear over the 58 C cap; "
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
        "ttf-r112-580",
        "Diboran-Stoupside DB-3 / Tower-B4: tray 42 C beats overhead smear 71 C; correct ACCEPT "
        "of an already-legal 2.2 t/h (total +1.14)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Tray 42 C < 58 C cap; overhead unused. "
        "total +1.14 = 0.44 + 0.32 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "diborane-cracker-column",
        ["accept", "designed", "tray-vs-vapor", "already-legal", "diborane"],
        "Teaches an already-legal diborane cracker column: live tray sits under cap; "
        "race order only confirms the ACCEPT.",
        5,
    )
