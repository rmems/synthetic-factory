def lif_566_excerpt():
    n = 86
    dt_us = 100
    tau_m_ms = 17.2
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.86
    i_stim_peak = 2.55
    stim = (21400, 25200)
    seed = 110566
    window_us = 46000
    i_clamp_extra = 0.69
    clamp_n = 19
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
    early = [(t, nid) for t, nid in spikes if t < 21400]
    burst = [(t, nid) for t, nid in spikes if 21400 <= t < 25200]
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
            group = [1 for tt, _ in picked if (tt < 21400) == (pool[0][0] < 21400)]
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
    take(burst, 9, label_times=(22800, 23800, 24800))
    clamp = [(t, nid) for t, nid in picked if t < 21400][:7]
    buckle = [(t, nid) for t, nid in picked if t >= 21400][:9]
    picked = sorted(clamp + buckle, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(
            f"LIF excerpt too short {len(picked)} (early={len(early)} burst={len(burst)})"
        )
    channels = ["lif.clamp" if t < 21400 else "lif.buckle" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 86),
            ("dt_us", 100),
            ("tau_m_ms", 17.2),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.86),
            ("i_stim_peak", 2.55),
            ("stim_t_us", [21400, 25200]),
            ("i_clamp_extra", 0.69),
            ("clamp_n", 19),
            ("seed", 110566),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-18 carry +0.69 glycol-clamp bias; stim 21.4-25.2 ms is the packing-support buckle.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 1020),
            ("delayed_surprise_s", 1020),
        ]
    )
    return excerpt_items(picked, channels), extra


def record_566():
    excerpt, extra = lif_566_excerpt()
    ticks = [
        tick(2352, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(5880, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(6100, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6680, 0.09, -0.06, -0.03, 0.02, -0.01),
        tick(22800, 0.04, -0.42, -0.04, 0.00, -0.02),
        tick(1020000000, 0.02, -0.05, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Glyoxal air-oxidizer G-4 at Glyoxal-Wath is already pushing 8.2 t/h ethylene-glycol "
                "into a 214 C bed against a 198 C selectivity cap. A bed-first latch clamps the glycol; "
                "a feed-first story would keep the 8.2 t/h cruise. Stored packing-support strain is not "
                "yet an observable of either race channel.",
            ),
            ("domain", "glyoxal-oxidizer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the G-4 air-oxidation pass, keep bed hotspot <= 198 C, and leave the "
                "packing supports unmarked.",
            ),
            ("t0_us", 1762300000000566),
            ("gate_latency_us", 800),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.88, 6.24]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bed.c 214 C pulse",
                                "ft.eg.tph 8.2 t/h cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first latches ethylene-glycol 8.2 -> 4.6 t/h; feed-first keeps "
                            "cruise on a still-cooling oxidizer model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one 2 kHz bed-RTD sample minus glycol-orifice group delay "
                            "on this air-oxidizer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter ~62 us (bed 28 + glycol 34): 3.5x over "
                            "a 2.0x trust floor. Reversing order by < 220 us inside the 360 us window "
                            "would have kept 8.2 t/h cruise; predicted next-sample 204 C > 198 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed multiplex RTD, 2 kHz, 28 us timestamp jitter",
                    "ethylene-glycol feed FT, 1 kHz, 34 us jitter",
                    "packing AE puck (context until the buckle)",
                    "glyoxal assay (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 198.0),
                        ("observed_bed_C", 214.0),
                        ("proposed_eg_tph", 8.2),
                        ("air_ratio", 1.15),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. G-4 indexed on Glyoxal-Wath; ethylene-glycol armed at 8.2 t/h.",
                    "2. Cruise 8.2 t/h; bed 214 C against 198 C selectivity cap.",
                    "3. Glycol precursor at 1.240 ms; bed warm-start 214 C.",
                    "4. Race window [5.880, 6.240] ms opens on the oxidizer bus.",
                    "5. rtd.bed.c 214 C at 5.880 ms (winner).",
                    "6. ft.eg.tph 8.2 t/h at 6.100 ms (loser by 220 us).",
                    "7. Gate at 6.680 ms (winner + 800 us): MODIFY clamp 8.2 -> 4.6 t/h.",
                    "8. Clamp executes; next-sample bed 186 C < 198 cap.",
                    "9. At 22.800 ms stored strain still buckles 16 mm of packing support; AE burst.",
                    "10. Oxidizer isolate 17 min (abort_s=1020); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_eg_8p2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("eg_tph", 8.2),
                        ("air_ratio", 1.15),
                        ("blower_pct", 62.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 214.0),
                        ("bed_cap_C", 198.0),
                        ("predicted_unclamped_next_C", 204.0),
                        ("eg_tph", 8.2),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 62),
                        ("abort_s", 1020),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 8.2 t/h cruise: 214 C looks like a glyoxal-assay spike, not "
                "packing contact, and G-4 volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 214 C won by 220 us, so the packing is loading heat, not still cooling. "
                "Holding 8.2 t/h predicts next-sample 204 C > 198 cap. MODIFY: ethylene-glycol 8.2 -> "
                "4.6 t/h. Observed after clamp 186 C < 198. A full REJECT is not indicated: a "
                "sound air-oxidation pass accepts 4.6 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 198.0),
                                    ("observed", 214.0),
                                    ("predicted_unclamped_next", 204.0),
                                    ("clamped_eg_tph", 4.6),
                                    ("observed_after_clamp", 186.0),
                                ]
                            ),
                        ),
                        (
                            "eg_tph",
                            OrderedDict([("proposed", 8.2), ("clamped", 4.6)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 3.55),
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
            ("name", "clamped_eg_4p6"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("eg_tph", 4.6),
                        ("air_ratio", 1.15),
                        ("blower_pct", 62.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: ethylene-glycol 8.2 -> 4.6 t/h. Process-correct vs the 198 C "
                "selectivity cap. Packing-support buckle still occurs at 22.800 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held bed at 186 C. At 22.800 ms stored strain "
                "in the packing support still buckled a 16 mm face. Clamp reduced dump energy; "
                "it did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("ethylene_glycol", "clamp executed; peak 186 C < 198"),
                        ("packing", "16 mm buckle at 22.800 ms"),
                        ("repair", "17 min oxidizer isolate (abort_s=1020)"),
                        ("mission", "G-4 air-oxidation pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither bed RTD nor glycol FT predicted the packing charge; ae.pack.buckle is a new channel at 22.800 ms, 16.120 ms after the gate, still inside the 46 ms raster.",
                    "Delayed (abort_s=1020): 17 min oxidizer isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "17 min oxidizer isolate after a 16 mm packing-support buckle. Safety head -0.62 "
                "prices the split; task_progress stays +0.32 because the glycol clamp completed "
                "under the 198 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.c (5.880 ms, 214 C)"),
                        ("loser", "ft.eg.tph (6.100 ms, 8.2 t/h)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Feed-first by < 220 us inside the 360 us window would have kept "
                            "8.2 t/h cruise; predicted next-sample 204 C would have exceeded "
                            "the 198 cap even without the packing charge. The MODIFY is still the "
                            "correct process. The buckle is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22800),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.800 ms packing-support buckle (tick t_us=22800), inside "
                "the 46 ms raster. The correct MODIFY at 6.680 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=1020 isolate tick.",
            ),
            ("delayed_surprise_s", 1020.0),
            ("abort_s", 1020),
        ]
    )
    spikes = [
        spike("enc.eg.ctx", 1.240, 0.43),
        spike("rtd.bed.c", 2.360, 0.62),
        spike("ft.eg.tph", 3.640, 0.51),
        spike("rtd.bed.c", 5.880, 1.34),
        spike("ft.eg.tph", 6.100, 1.16),
        spike("ctrl.gate", 6.680, 0.99),
        spike("rtd.bed.c", 8.520, 0.81),
        spike("ft.eg.tph", 11.400, 0.63),
        spike("ctrl.gate", 15.800, 0.85),
        spike("ae.pack.buckle", 22.800, 1.48),
        spike("ae.pack.buckle", 24.900, 0.92),
        spike("enc.eg.ctx", 33.200, 0.42),
        spike("rtd.bed.c", 41.600, 0.54),
    ]
    ras = raster_core(
        46,
        86,
        24,
        95,
        routing(
            "thalamic-relay.bed-glyoxal",
            "spikenaut.policy.eg-clamp",
            [
                ("relay.rtd.bed", "policy.eg_clamp", 0.66),
                ("relay.ft.eg", "policy.eg_hold", 0.28),
                ("relay.ae.pack", "policy.eg_clamp", -0.45),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at bed win (5.880 ms) opens a 50 ms "
            "eligibility trace that still covers the 22.800 ms packing-support buckle",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("eg_clamp", 46, 0.50, 241.5, 4),
                    pop("eg_hold", 46, 0.50, 60.4, 1),
                    pop("bed_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r110-566",
        "Glyoxal-Wath G-4 / air-oxidizer: bed 214 C beats ethylene-glycol-feed by 220 us; correct "
        "MODIFY still eats an in-window packing-support buckle (partnered negative total -0.46)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "46 ms raster. total -0.46 = 0.32 + -0.62 + -0.16 + 0.04 + -0.04. Named oxidizer "
        "isolate (abort_s=1020) is not netted into task_progress.",
        ras,
        gate,
        "glyoxal-oxidizer",
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
        "17 min oxidizer isolate.",
        1,
    )


def record_567():
    ticks = [
        tick(1888, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(4720, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(4960, -0.03, -0.01, -0.03, -0.02, 0.01),
        tick(5480, -0.07, -0.04, -0.07, -0.04, 0.02),
        tick(5880, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(1140000000, -0.02, -0.01, -0.04, 0.00, 0.00),
    ]
    spikes = [
        spike("ft.maleic.ctx", 0.940, 0.41),
        spike("live.bed.C", 1.880, 0.59),
        spike("bus.burn.up", 2.640, 0.52),
        spike("live.bed.C", 4.720, 1.33),
        spike("bus.burn.up", 4.960, 1.16),
        spike("ctrl.gate", 5.480, 1.01),
        spike("live.bed.C", 7.360, 0.75),
        spike("bus.burn.up", 8.440, 0.62),
        spike("ctrl.gate", 12.600, 0.83),
        spike("ft.maleic.ctx", 16.400, 0.43),
        spike("live.bed.C", 22.200, 0.54),
        spike("bus.burn.up", 26.400, 0.48),
    ]
    excerpt = independent_excerpt(110567, 76, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Maleic dehydrator D-2 at Succiny-Wray is holding maleic acid at 5.6 t/h with live "
                "Type-K bed 168.0 C against a 220.0 C trip. A leftover IEC 60584 burnout-upscale jumper "
                "still prints 1372 C from a 21.6 mA URV failsafe. Live-TC-first should ACCEPT the feed; a weak "
                "supervisor that binds the burnout-upscale EU will REJECT a legal succinic-anhydride still.",
            ),
            ("domain", "succinic-anhydride-dehydrator"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep 5.6 t/h maleic on D-2 while live Type-K bed stays <= 220.0 C; "
                "do not spend a leftover burnout-upscale jumper on the hold.",
            ),
            ("t0_us", 1762300000000567),
            ("gate_latency_us", 760),
            ("race_window_us", 400),
            ("race_window_rel_ms", [4.72, 5.12]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "live.bed.C 168.0 C LIVE Type-K",
                                "bus.burn.up 1372 C leftover burnout-upscale URV",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-TC-first should ACCEPT 5.6 t/h (168.0 C < 220.0 C trip). "
                            "Burnout-first tempts a weak supervisor to treat 1372 C as live.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one D-2 Type-K sample minus leftover burnout-upscale group delay "
                            "on this succinic bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 240 us vs combined jitter ~60 us (live 28 + burnout 32): 4.0x over "
                            "a 2.0x trust floor. Order is correctly live-TC-first. The error is binding "
                            "the leftover burnout-upscale EU, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "D-2 Type-K bed RTD, 4 kHz, 28 us jitter, LIVE analog",
                    "leftover IEC 60584 burnout-upscale jumper, 4 kHz, 32 us jitter, URV failsafe STALE",
                    "maleic feed FT (context)",
                    "acetic make-up FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("trip_C", 220.0),
                        ("live_C", 168.0),
                        ("burnout_C", 1372.0),
                        ("burnout_mA", 21.6),
                        ("burnout_upscale", True),
                        ("burnout_is_pv", False),
                        ("burnout_as_eu", True),
                        ("proposed_maleic_tph", 5.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. D-2 latched on Succiny-Wray; maleic 5.6 t/h armed.",
                    "2. Live Type-K 168.0 C; leftover burnout-upscale still prints 1372 C.",
                    "3. Maleic-FT precursor at 0.940 ms.",
                    "4. Race window [4.720, 5.120] ms.",
                    "5. live.bed.C 168.0 C at 4.720 ms (winner).",
                    "6. bus.burn.up 1372 C at 4.960 ms (loser by 240 us).",
                    "7. Gate at 5.480 ms: REJECT hold 0.0 t/h (incorrect).",
                    "8. Legal feed cancelled; live Type-K still 168.0 C < 220.0 C trip.",
                    "9. Burnout-upscale leftover remains the published bind.",
                    "10. Delayed missed_window_s=1140 (19 min anhydride window) while D-2 waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "maleic_5p6"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("maleic_tph", 5.6),
                        ("hold", False),
                        ("bound_tc", "live_type_k"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 168.0),
                        ("trip_C", 220.0),
                        ("burnout_C", 1372.0),
                        ("burnout_mA", 21.6),
                        ("burnout_upscale", True),
                        ("burnout_is_pv", False),
                        ("burnout_as_eu", True),
                        ("pv_live", True),
                        ("proposed_maleic_tph", 5.6),
                        ("race_margin_us", 240),
                        ("combined_jitter_us", 60),
                        ("missed_window_s", 1140),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 5.6 t/h maleic because live Type-K 168.0 C is under the "
                "220.0 C trip; 1372 C is leftover IEC 60584 burnout-upscale URV on the same "
                "loop, not the live bed.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Leftover burnout-upscale jumper still prints 1372 C, over the 220.0 C trip "
                "once the supervisor treats the URV failsafe as live. REJECT: hold maleic "
                "0.0 t/h until the tag recovers under 220 so the dehydrator does not see an over-temp.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("published_live_trip", 220.0),
                                    ("observed_live", 168.0),
                                    ("misbound_burnout_C", 1372.0),
                                    ("burnout_upscale", True),
                                    ("burnout_is_pv", True),
                                    ("burnout_as_eu", True),
                                    ("executed_maleic_tph", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 240),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 4.00),
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
            ("name", "maleic_hold_burnout"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("maleic_tph", 0.0),
                        ("hold", True),
                        ("bound_tc", "burnout_upscale"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): maleic 5.6 -> 0.0 t/h. Routing relay.burnout.upscale -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live 168.0 C never "
                "violated the 220.0 C trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze D-2 at 0.0 t/h while live Type-K stayed 168.0 C under the "
                "220.0 C trip. 19 min anhydride window missed. Correct gate was ACCEPT of "
                "the already-legal 5.6 t/h feed.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("maleic", "held at 0.0 t/h; 5.6 t/h abandoned"),
                        ("live_C", "still 168.0 C, under 220.0 C published trip"),
                        ("dehydrator", "19 min anhydride window missed"),
                        ("flag", "1372 C burnout-upscale-as-PV false positive, not a live over-trip"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 1372 C reading is leftover IEC 60584 burnout-upscale URV, not a published live over-trip.",
                    "Delayed (missed_window_s=1140): sister D-3 ran the same 5.6 t/h anhydride window after QA cleared the jumper; D-2's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live 168.0 C < published 220.0 C trip; leave 5.6 t/h; ignore burnout-upscale URV.",
                        ),
                        ("correct_trip_C", 220.0),
                        ("wrong_burnout_C", 1372.0),
                        ("bound_tc_should_be", "live_type_k"),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [("maleic_tph", 0.0), ("hold", True), ("bound_tc", "burnout_upscale")]
                            ),
                        ),
                        (
                            "cost",
                            "19 min missed anhydride window (task/efficiency); live D-2 never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "live.bed.C (4.720 ms, 168.0 C LIVE Type-K)"),
                        ("loser", "bus.burn.up (4.960 ms, 1372 C STALE burnout-upscale)"),
                        ("margin_us", 240),
                        (
                            "counterfactual_if_reversed",
                            "Burnout-first by < 240 us would still show live 168.0 C < 220.0 C. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the live-TC "
                            "win on a leftover burnout-upscale jumper.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5480),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (5.480 ms, tick 4). The 19 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 1140.0),
            ("missed_window_s", 1140),
        ]
    )
    ras = raster_core(
        28,
        76,
        32,
        68,
        routing(
            "relay.burnout.upscale",
            "policy.hold_reject",
            [
                ("relay.burnout.upscale", "policy.hold_reject", 0.77),
                ("relay.live.bed", "policy.hold_reject", 0.15),
            ],
            "acetylcholine",
            0.06,
            "burnout_upscale_stdp; ACh tags the (wrong) hold_reject bind at the leftover URV failsafe",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("missed_window_s", 1140),
                ("delayed_surprise_s", 1140),
                ("burnout_upscale", True),
                ("burnout_is_pv", False),
                ("burnout_as_eu", True),
                ("burnout_C", 1372.0),
                ("live_C", 168.0),
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
                    pop("hold_reject", 50, 0.50, 200.0, 4),
                    pop("go_accept", 50, 0.80, 5.0, 0),
                    pop("burnout_ctx", 26, 0.55, 96.2, 1),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r110-567",
        "WRONG-REJECT at Succiny-Wray D-2: live Type-K 168.0 C < 220.0 C trip; "
        "supervisor bound leftover IEC 60584 burnout-upscale URV (1372 C) as the live bed",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 168.0 < 220.0 on live D-2 is true; clamp bound "
        "to a 1372 C leftover burnout-upscale URV. total -0.56 = -0.20 + -0.10 + -0.22 + -0.10 + 0.06.",
        ras,
        gate,
        "succinic-anhydride-dehydrator",
        [
            "reject",
            "wrong-gate",
            "burnout-upscale-as-pv",
            "iec-60584-urv",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed on a leftover burnout-upscale jumper.",
        2,
        supervisor_error_type="wrong-reject",
    )


def record_568():
    ticks = [
        tick(2144, 0.01, 0.06, 0.01, 0.01, 0.01),
        tick(5360, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5580, 0.02, 0.07, 0.02, 0.02, 0.01),
        tick(6180, 0.03, 0.12, 0.04, 0.03, 0.02),
        tick(6560, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(540000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("ir.kettle.ctx", 1.080, 0.44),
        spike("ae.kettle.pps", 2.160, 0.63),
        spike("ir.kettle.C", 3.720, 0.50),
        spike("ae.kettle.pps", 5.360, 1.36),
        spike("ir.kettle.C", 5.580, 1.13),
        spike("ctrl.gate", 6.180, 1.04),
        spike("ae.kettle.pps", 8.040, 0.78),
        spike("ir.kettle.ctx", 12.200, 0.45),
        spike("ir.kettle.C", 16.400, 0.59),
        spike("ctrl.gate", 21.000, 0.82),
        spike("ae.kettle.pps", 26.800, 0.51),
        spike("ir.kettle.C", 32.200, 0.47),
        spike("ae.kettle.ctx", 35.400, 0.41),
    ]
    excerpt = independent_excerpt(110568, 100, 38000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Esterifier E-8 on Butacryl-Holm BA-HIL is armed for 7.1 t/h acrylic acid while "
                "kettle AE sits at 48 pps against a 14 pps foam-collapse floor. A kettle pyrometer, lit by the "
                "pad lamp spectrum, still reports 92 C under a 118 C jacket cap. AE-first holds "
                "the esterifier; IR-first would commit 7.1 t/h into a collapsing foam bed.",
            ),
            ("domain", "butyl-acrylate-esterifier"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Run E-8 only if kettle AE stays <= 14 pps; otherwise hold so a foam-collapse "
                "is not loaded at 7.1 t/h acrylic.",
            ),
            ("t0_us", 1762300000000568),
            ("gate_latency_us", 820),
            ("race_window_us", 380),
            ("race_window_rel_ms", [5.36, 5.74]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.kettle.pps 48 pps foam collapse",
                                "ir.kettle.C 92 C pad-lamp glint",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches esterifier hold 7.1 -> 0 t/h; IR-first would commit "
                            "7.1 t/h on a still-legal 92 C jacket-cap story.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one kettle-AE slot versus jacket-IR decode on this HIL esterifier bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter ~64 us (AE 30 + IR 34): 3.4x over "
                            "a 2.0x trust floor. Reversing order by < 220 us inside the 380 us "
                            "window would have committed 7.1 t/h into a 48 pps foam collapse.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "kettle AE puck, 5 kHz, 30 us jitter",
                    "jacket IR camera, 200 Hz, 34 us jitter",
                    "acrylic encoder (context)",
                    "n-butanol FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_foam_floor_pps", 14.0),
                        ("observed_ae_pps", 48.0),
                        ("jacket_cap_C", 118.0),
                        ("observed_jacket_C", 92.0),
                        ("proposed_acrylic_tph", 7.1),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("bench", "Butacryl-Holm BA-HIL butyl-acrylate esterifier pad, E-8"),
                        (
                            "inject",
                            "AE envelope delayed 80-120 us vs IR; loop lag, not a false AE pickup",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. E-8 indexed on Butacryl-Holm BA-HIL; acrylic 7.1 t/h armed.",
                    "2. Jacket IR 92 C under 118 C cap; AE already 48 pps.",
                    "3. IR-context precursor at 1.080 ms.",
                    "4. Race window [5.360, 5.740] ms.",
                    "5. ae.kettle.pps 48 pps at 5.360 ms (winner).",
                    "6. ir.kettle.C 92 C at 5.580 ms (loser by 220 us).",
                    "7. Gate at 6.180 ms: REJECT hold esterifier 0 t/h.",
                    "8. Pass cancelled; foam collapse not loaded.",
                    "9. HIL pad lamp spectrum remains the jacket glint source.",
                    "10. Delayed (abort_s=540): 9 min kettle re-seat before the next esterification.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "acrylic_7p1"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("acrylic_tph", 7.1),
                        ("hold", False),
                        ("kettle", "E-8"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 48.0),
                        ("ae_foam_floor_pps", 14.0),
                        ("jacket_C", 92.0),
                        ("jacket_cap_C", 118.0),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 64),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 7.1 t/h because jacket 92 C is under the 118 C "
                "cap and treats the AE puck as agitator noise.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Kettle AE 48 pps won by 220 us, so the foam is collapsing, not still quiet. "
                "48 pps > 14 pps floor. REJECT: hold acrylic 7.1 -> 0 t/h. Jacket 92 C < 118 C "
                "does not license the pass once AE is over floor.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "kettle_ae_pps",
                            OrderedDict(
                                [
                                    ("floor", 14.0),
                                    ("observed", 48.0),
                                    ("executed_acrylic_tph", 0.0),
                                ]
                            ),
                        ),
                        (
                            "jacket_C",
                            OrderedDict(
                                [
                                    ("cap", 118.0),
                                    ("observed", 92.0),
                                    ("does_not_license_pass", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 3.44),
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
            ("name", "kettle_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("acrylic_tph", 0.0),
                        ("hold", True),
                        ("kettle", "E-8"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (correct): acrylic 7.1 -> 0 t/h. Routing relay.ae.kettle -> "
                "policy.kettle_hold. Foam collapse is not loaded.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held E-8 at 0 t/h. AE 48 pps beat jacket 92 C; kettle "
                "was already over the 14 pps foam floor. 9 min re-seat follows (abort_s=540).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("esterifier", "held at 0 t/h; 7.1 t/h abandoned"),
                        ("kettle", "48 pps foam collapse not loaded"),
                        ("ir", "92 C still under 118 C cap"),
                        ("reseat", "9 min kettle re-seat queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Jacket IR 92 C was a HIL pad-lamp glint, not a jacket-cap exceedance.",
                    "Delayed (abort_s=540): 9 min kettle re-seat before the next esterification on BA-HIL.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.kettle.pps (5.360 ms, 48 pps)"),
                        ("loser", "ir.kettle.C (5.580 ms, 92 C)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 220 us would have committed 7.1 t/h into a kettle "
                            "already at 48 pps. The REJECT is still the correct process; AE is the "
                            "licensing channel, not jacket IR.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6180),
            (
                "reward_inflection_note",
                "Safety and task credit the correct REJECT at 6.180 ms (tick 4). The 9 min "
                "re-seat is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 540.0),
            ("abort_s", 540),
        ]
    )
    ras = raster_core(
        38,
        100,
        22,
        84,
        routing(
            "thalamic-relay.kettle-ae",
            "spikenaut.policy.kettle-hold",
            [
                ("relay.ae.kettle", "policy.kettle_hold", 0.70),
                ("relay.ir.kettle", "policy.kettle_commit", 0.26),
                ("relay.ae.kettle", "policy.kettle_hold", 0.11),
            ],
            "dopamine",
            0.07,
            "ae_floor_stdp; DA at kettle win (5.360 ms) opens a 70 ms eligibility trace",
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
            ("decision_window_ms", 0.38),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("kettle_hold", 54, 0.50, 194.9, 4),
                    pop("kettle_commit", 54, 0.50, 48.7, 1),
                    pop("ae_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r110-568",
        "Butacryl-Holm BA-HIL / E-8: kettle AE 48 pps beats jacket 92 C; correct "
        "REJECT holds the butyl-acrylate esterifier",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 48 pps > 14 pps floor beats a legal jacket IR. "
        "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "butyl-acrylate-esterifier",
        ["reject", "hil", "kettle-ae", "butyl-acrylate", "correct-gate"],
        "Teaches a kettle-AE vs pad-lamp-glint race on a HIL esterifier: the foam floor, "
        "not the jacket cap, licenses the pass.",
        3,
    )


def record_569():
    ticks = [
        tick(1672, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(4180, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(4360, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(4820, 0.12, 0.09, 0.05, 0.03, 0.02),
        tick(5140, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(360000000, 0.03, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.phos.ctx", 0.860, 0.42),
        spike("rtd.kettle.C", 1.680, 0.59),
        spike("ir.smear.C", 2.820, 0.48),
        spike("rtd.kettle.C", 4.180, 1.29),
        spike("ir.smear.C", 4.360, 1.11),
        spike("ctrl.gate", 4.820, 0.98),
        spike("rtd.kettle.C", 6.640, 0.73),
        spike("enc.phos.ctx", 10.600, 0.45),
        spike("ir.smear.C", 14.400, 0.56),
        spike("ctrl.gate", 18.800, 0.81),
        spike("rtd.kettle.C", 23.800, 0.50),
    ]
    excerpt = independent_excerpt(110569, 60, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Interfacial polycarbonate kettle K-11 at Polycarb-Glen is already at 38 C liquor while a "
                "coil IR smear still reports as 71 C against a 62 C cap the live RTD "
                "has not crossed. Liquor-first should ACCEPT 2.6 t/h phosgene; smear-first would "
                "invent a hold on an already-legal interfacial pass.",
            ),
            ("domain", "polycarbonate-interfacial"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Run K-11 at 2.6 t/h while liquor stays <= 62 C; do not spend a coil IR "
                "smear on the kettle hold.",
            ),
            ("t0_us", 1762300000000569),
            ("gate_latency_us", 640),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.18, 4.50]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.kettle.C 38 C live",
                                "ir.smear.C as 71 C",
                            ],
                        ),
                        (
                            "semantics",
                            "Liquor-first should ACCEPT 2.6 t/h (38 C < 62 C cap). "
                            "Smear-first would hold on a simulated coil-film.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one kettle-RTD sample versus coil-IR decode on this "
                            "interfacial bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter ~54 us (RTD 24 + IR 30): 3.3x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have invented a hold on an already-legal 38 C liquor.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "kettle RTD, 4 kHz, 24 us jitter",
                    "coil IR camera, 200 Hz, 30 us jitter",
                    "phosgene encoder (context)",
                    "BPA load cell (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("liquor_cap_C", 62.0),
                        ("observed_liquor_C", 38.0),
                        ("coil_smear_C", 71.0),
                        ("proposed_phosgene_tph", 2.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. K-11 indexed on Polycarb-Glen; phosgene 2.6 t/h armed.",
                    "2. Liquor 38 C; coil smear as 71 C over 62 C cap.",
                    "3. Phosgene-encoder precursor at 0.860 ms.",
                    "4. Race window [4.180, 4.500] ms.",
                    "5. rtd.kettle.C 38 C at 4.180 ms (winner).",
                    "6. ir.smear.C at 4.360 ms (loser by 180 us).",
                    "7. Gate at 4.820 ms: ACCEPT leave 2.6 t/h.",
                    "8. Liquor remains 38 C < 62 C; smear unused as a hold.",
                    "9. Simulated coil film remains the IR source.",
                    "10. Delayed (survey_hold_s=360): 6 min Mw survey after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "phosgene_2p6"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("phosgene_tph", 2.6),
                        ("hold", False),
                        ("liquor_C", 38.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("liquor_C", 38.0),
                        ("liquor_cap_C", 62.0),
                        ("coil_smear_C", 71.0),
                        ("proposed_phosgene_tph", 2.6),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 54),
                        ("survey_hold_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.6 t/h because liquor 38 C is under the 62 C cap; "
                "71 C is a coil IR smear, not a kettle temperature.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Liquor 38 C won by 180 us and sits under the 62 C cap. Coil smear "
                "71 C is a simulated film, not a kettle reading. ACCEPT: leave 2.6 t/h. "
                "A hold would idle a legal interfacial pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "liquor_C",
                            OrderedDict(
                                [
                                    ("cap", 62.0),
                                    ("observed", 38.0),
                                    ("executed_phosgene_tph", 2.6),
                                ]
                            ),
                        ),
                        (
                            "coil_smear_C",
                            OrderedDict(
                                [
                                    ("observed", 71.0),
                                    ("not_a_kettle_reading", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 54),
                                    ("ratio", 3.33),
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
            ("name", "phosgene_2p6"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("phosgene_tph", 2.6),
                        ("hold", False),
                        ("liquor_C", 38.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 2.6 t/h. Routing relay.rtd.kettle -> policy.pc_go. "
                "Coil smear unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left K-11 at 2.6 t/h. Liquor 38 C beat coil smear 71 C; "
                "the 62 C cap was never crossed. 6 min Mw survey follows "
                "(survey_hold_s=360).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("phosgene", "2.6 t/h held as proposed"),
                        ("liquor", "38 C < 62 C cap"),
                        ("smear", "71 C film unused"),
                        ("survey", "6 min Mw survey queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "IR 71 C was a simulated coil-film smear, not a liquor over-cap.",
                    "Delayed (survey_hold_s=360): 6 min Mw survey after the pass on K-11.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.kettle.C (4.180 ms, 38 C)"),
                        ("loser", "ir.smear.C (4.360 ms, smear 71 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Smear-first by < 180 us would still be a coil film over the "
                            "62 C cap; a correct gate ACCEPTs either way. Reversing would only "
                            "have delayed confirmation of the same legal liquor.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4820),
            (
                "reward_inflection_note",
                "Task credit lands at the correct ACCEPT (4.820 ms, tick 4). The 6 min "
                "Mw survey is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 360.0),
            ("survey_hold_s", 360),
        ]
    )
    ras = raster_core(
        26,
        60,
        36,
        56,
        routing(
            "thalamic-relay.kettle-rtd",
            "spikenaut.policy.pc-go",
            [
                ("relay.rtd.kettle", "policy.pc_go", 0.72),
                ("relay.ir.smear", "policy.pc_hold", 0.18),
            ],
            "serotonin",
            0.08,
            "liquor_under_cap_stdp; 5-HT tags the go bind at the kettle RTD win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_hold_s", 360),
                ("delayed_surprise_s", 360),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("pc_go", 36, 0.50, 260.4, 3),
                    pop("pc_hold", 36, 0.80, 8.7, 0),
                    pop("rtd_veto", 16, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r110-569",
        "Polycarb-Glen K-11 / interfacial: liquor 38 C beats coil smear 71 C; correct ACCEPT "
        "of an already-legal 2.6 t/h (total +1.10)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Liquor 38 C < 62 C cap; smear unused. "
        "total +1.10 = 0.42 + 0.30 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "polycarbonate-interfacial",
        ["accept", "simulated", "liquor-vs-smear", "already-legal", "polycarbonate"],
        "Teaches an already-legal interfacial polycarbonate kettle: live liquor sits under cap; "
        "race order only confirms the ACCEPT.",
        4,
    )


def record_570():
    ticks = [
        tick(1936, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(4840, 0.09, 0.06, 0.04, 0.03, 0.02),
        tick(5040, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(5560, 0.13, 0.10, 0.05, 0.03, 0.02),
        tick(5920, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(420000000, 0.03, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.nb.ctx", 0.980, 0.41),
        spike("rtd.nb.C", 1.940, 0.58),
        spike("ir.vapor.C", 3.120, 0.47),
        spike("rtd.nb.C", 4.840, 1.28),
        spike("ir.vapor.C", 5.040, 1.10),
        spike("ctrl.gate", 5.560, 0.97),
        spike("rtd.nb.C", 7.420, 0.74),
        spike("enc.nb.ctx", 11.100, 0.44),
        spike("ir.vapor.C", 15.200, 0.55),
        spike("ctrl.gate", 19.400, 0.80),
        spike("rtd.nb.C", 22.800, 0.49),
    ]
    excerpt = independent_excerpt(110570, 52, 24000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Norbornene polymerizer P-5 at Norborn-Mire already holds kettle 64 C against an 88 C "
                "cap while overhead vapor IR still smears as 97 C. Kettle-first should ACCEPT 4.4 t/h "
                "norbornene; vapor-first would invent a hold on an already-legal ROMP pass.",
            ),
            ("domain", "norbornene-polymerizer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run P-5 at 4.4 t/h while kettle stays <= 88 C; do not spend overhead vapor "
                "smear on the polymerizer hold.",
            ),
            ("t0_us", 1762300000000570),
            ("gate_latency_us", 720),
            ("race_window_us", 360),
            ("race_window_rel_ms", [4.84, 5.20]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.nb.C 64 C live kettle",
                                "ir.vapor.C as 97 C smear",
                            ],
                        ),
                        (
                            "semantics",
                            "Kettle-first should ACCEPT 4.4 t/h (64 C < 88 C cap). "
                            "Vapor-first would hold on an unused overhead smear.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one kettle-RTD sample versus overhead-IR decode on this "
                            "ROMP bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 200 us vs combined jitter ~58 us (RTD 26 + IR 32): 3.4x over "
                            "a 2.0x trust floor. Reversing order by < 200 us inside the 360 us "
                            "window would have invented a hold on an already-legal 64 C kettle.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "kettle RTD, 4 kHz, 26 us jitter",
                    "overhead IR, 200 Hz, 32 us jitter",
                    "norbornene encoder (context)",
                    "Grubbs-catalyst FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("kettle_cap_C", 88.0),
                        ("observed_kettle_C", 64.0),
                        ("vapor_smear_C", 97.0),
                        ("proposed_nb_tph", 4.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. P-5 indexed on Norborn-Mire; norbornene 4.4 t/h armed.",
                    "2. Kettle 64 C; vapor smear as 97 C over 88 C cap.",
                    "3. Encoder precursor at 0.980 ms.",
                    "4. Race window [4.840, 5.200] ms.",
                    "5. rtd.nb.C 64 C at 4.840 ms (winner).",
                    "6. ir.vapor.C at 5.040 ms (loser by 200 us).",
                    "7. Gate at 5.560 ms: ACCEPT leave 4.4 t/h.",
                    "8. Kettle remains 64 C < 88 C; smear unused as a hold.",
                    "9. Overhead unused as a process PV.",
                    "10. Delayed (dwell_s=420): 7 min Mw dwell after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "nb_4p4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("nb_tph", 4.4),
                        ("hold", False),
                        ("kettle_C", 64.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("kettle_C", 64.0),
                        ("kettle_cap_C", 88.0),
                        ("vapor_smear_C", 97.0),
                        ("proposed_nb_tph", 4.4),
                        ("race_margin_us", 200),
                        ("combined_jitter_us", 58),
                        ("dwell_s", 420),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.4 t/h because kettle 64 C is under the 88 C cap; "
                "97 C is overhead vapor smear, not kettle temperature.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Kettle 64 C won by 200 us and sits under the 88 C cap. Overhead smear "
                "97 C is unused vapor IR, not a kettle reading. ACCEPT: leave 4.4 t/h. "
                "A hold would idle a legal ROMP pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "kettle_C",
                            OrderedDict(
                                [
                                    ("cap", 88.0),
                                    ("observed", 64.0),
                                    ("executed_nb_tph", 4.4),
                                ]
                            ),
                        ),
                        (
                            "vapor_smear_C",
                            OrderedDict(
                                [
                                    ("observed", 97.0),
                                    ("not_a_kettle_reading", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 200),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 3.45),
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
            ("name", "nb_4p4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("nb_tph", 4.4),
                        ("hold", False),
                        ("kettle_C", 64.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 4.4 t/h. Routing relay.rtd.nb -> policy.nb_go. "
                "Overhead unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left P-5 at 4.4 t/h. Kettle 64 C beat vapor smear 97 C; "
                "the 88 C cap was never crossed. 7 min Mw dwell follows (dwell_s=420).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("norbornene", "4.4 t/h held as proposed"),
                        ("kettle", "64 C < 88 C cap"),
                        ("smear", "97 C vapor unused"),
                        ("dwell", "7 min Mw dwell queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "IR 97 C was overhead vapor smear, not a kettle over-cap.",
                    "Delayed (dwell_s=420): 7 min Mw dwell after the pass on P-5.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.nb.C (4.840 ms, 64 C)"),
                        ("loser", "ir.vapor.C (5.040 ms, smear 97 C)"),
                        ("margin_us", 200),
                        (
                            "counterfactual_if_reversed",
                            "Vapor-first by < 200 us would still be unused overhead smear; "
                            "a correct gate ACCEPTs either way. Reversing would only have delayed "
                            "confirmation of the same legal kettle.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5560),
            (
                "reward_inflection_note",
                "Task credit lands at the correct ACCEPT (5.560 ms, tick 4). The 7 min "
                "Mw dwell is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 420.0),
            ("dwell_s", 420),
        ]
    )
    ras = raster_core(
        24,
        52,
        40,
        50,
        routing(
            "thalamic-relay.nb-rtd",
            "spikenaut.policy.nb-go",
            [
                ("relay.rtd.nb", "policy.nb_go", 0.73),
                ("relay.ir.vapor", "policy.nb_hold", 0.16),
            ],
            "adenosine",
            0.09,
            "kettle_under_cap_stdp; adenosine tags the go bind at the kettle RTD win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("dwell_s", 420),
                ("delayed_surprise_s", 420),
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
                    pop("nb_go", 34, 0.50, 245.1, 3),
                    pop("nb_hold", 34, 0.80, 8.2, 0),
                    pop("rtd_veto", 16, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r110-570",
        "Norborn-Mire P-5 / polymerizer: kettle 64 C beats vapor smear 97 C; correct ACCEPT "
        "of an already-legal 4.4 t/h (total +1.14)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Kettle 64 C < 88 C cap; vapor unused. "
        "total +1.14 = 0.44 + 0.32 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "norbornene-polymerizer",
        ["accept", "designed", "kettle-vs-vapor", "already-legal", "norbornene"],
        "Teaches an already-legal norbornene ROMP kettle: live liquor sits under cap; "
        "race order only confirms the ACCEPT.",
        5,
    )
