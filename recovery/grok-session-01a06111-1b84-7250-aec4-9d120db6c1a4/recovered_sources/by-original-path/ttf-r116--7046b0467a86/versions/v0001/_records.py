def lif_596_excerpt():
    n = 88
    dt_us = 100
    tau_m_ms = 16.8
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.84
    i_stim_peak = 2.48
    stim = (20400, 24800)
    seed = 116596
    window_us = 44000
    i_clamp_extra = 0.71
    clamp_n = 21
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
    early = [(t, nid) for t, nid in spikes if t < 20400]
    burst = [(t, nid) for t, nid in spikes if 20400 <= t < 24800]
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
            group = [1 for tt, _ in picked if (tt < 20400) == (pool[0][0] < 20400)]
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
    take(burst, 9, label_times=(21600, 22800, 24000))
    clamp = [(t, nid) for t, nid in picked if t < 20400][:7]
    buckle = [(t, nid) for t, nid in picked if t >= 20400][:9]
    picked = sorted(clamp + buckle, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(
            f"LIF excerpt too short {len(picked)} (early={len(early)} burst={len(burst)})"
        )
    channels = ["lif.clamp" if t < 20400 else "lif.buckle" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 88),
            ("dt_us", 100),
            ("tau_m_ms", 16.8),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.84),
            ("i_stim_peak", 2.48),
            ("stim_t_us", [20400, 24800]),
            ("i_clamp_extra", 0.71),
            ("clamp_n", 21),
            ("seed", 116596),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-20 carry +0.71 working-solution-clamp bias; stim 20.4-24.8 ms is the packing-support buckle.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 1080),
            ("delayed_surprise_s", 1080),
        ]
    )
    return excerpt_items(picked, channels), extra


def record_596():
    excerpt, extra = lif_596_excerpt()
    ticks = [
        tick(2180, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(5720, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(5960, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6560, 0.09, -0.06, -0.03, 0.02, -0.01),
        tick(21600, 0.04, -0.42, -0.04, 0.00, -0.02),
        tick(1080000000, 0.02, -0.05, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Anthrahydroquinone oxidizer X-3 at Peroxaq-Moss is already pushing 6.8 t/h working-solution "
                "into a 176 C tower against a 162 C peroxide-selectivity cap. A tower-first latch clamps the "
                "working solution; a feed-first story would keep the 6.8 t/h cruise. Stored packing-support "
                "strain is not yet an observable of either race channel.",
            ),
            ("domain", "anthrahydroquinone-oxidizer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the X-3 air-oxidation pass, keep tower hotspot <= 162 C, and leave the "
                "packing supports unmarked.",
            ),
            ("t0_us", 1762300000000596),
            ("gate_latency_us", 840),
            ("race_window_us", 400),
            ("race_window_rel_ms", [5.72, 6.12]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.ox.c 176 C pulse",
                                "ft.ws.tph 6.8 t/h cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Tower-first latches working-solution 6.8 -> 3.8 t/h; feed-first keeps "
                            "cruise on a still-cooling oxidizer model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one 2 kHz tower-RTD sample minus working-solution orifice group delay "
                            "on this AO-oxidizer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 240 us vs combined jitter ~66 us (tower 30 + working-solution 36): 3.6x over "
                            "a 2.0x trust floor. Reversing order by < 240 us inside the 400 us window "
                            "would have kept 6.8 t/h cruise; predicted next-sample 168 C > 162 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "tower multiplex RTD, 2 kHz, 30 us timestamp jitter",
                    "working-solution feed FT, 1 kHz, 36 us jitter",
                    "packing AE puck (context until the buckle)",
                    "H2O2 assay (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("tower_cap_C", 162.0),
                        ("observed_tower_C", 176.0),
                        ("proposed_ws_tph", 6.8),
                        ("air_ratio", 1.22),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. X-3 indexed on Peroxaq-Moss; working-solution armed at 6.8 t/h.",
                    "2. Cruise 6.8 t/h; tower 176 C against 162 C peroxide-selectivity cap.",
                    "3. Working-solution precursor at 1.180 ms; tower warm-start 176 C.",
                    "4. Race window [5.720, 6.120] ms opens on the AO-oxidizer bus.",
                    "5. rtd.ox.c 176 C at 5.720 ms (winner).",
                    "6. ft.ws.tph 6.8 t/h at 5.960 ms (loser by 240 us).",
                    "7. Gate at 6.560 ms (winner + 840 us): MODIFY clamp 6.8 -> 3.8 t/h.",
                    "8. Clamp executes; next-sample tower 154 C < 162 cap.",
                    "9. At 21.600 ms stored strain still buckles 14 mm of packing support; AE burst.",
                    "10. Oxidizer isolate 18 min (abort_s=1080); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_ws_6p8"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ws_tph", 6.8),
                        ("air_ratio", 1.22),
                        ("blower_pct", 58.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("tower_C", 176.0),
                        ("tower_cap_C", 162.0),
                        ("predicted_unclamped_next_C", 168.0),
                        ("ws_tph", 6.8),
                        ("race_margin_us", 240),
                        ("combined_jitter_us", 66),
                        ("abort_s", 1080),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 6.8 t/h cruise: 176 C looks like an H2O2-assay spike, not "
                "packing contact, and X-3 volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Tower 176 C won by 240 us, so the packing is loading heat, not still cooling. "
                "Holding 6.8 t/h predicts next-sample 168 C > 162 cap. MODIFY: working-solution 6.8 -> "
                "3.8 t/h. Observed after clamp 154 C < 162. A full REJECT is not indicated: a "
                "sound AO oxidation pass accepts 3.8 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tower_C",
                            OrderedDict(
                                [
                                    ("cap", 162.0),
                                    ("observed", 176.0),
                                    ("predicted_unclamped_next", 168.0),
                                    ("clamped_ws_tph", 3.8),
                                    ("observed_after_clamp", 154.0),
                                ]
                            ),
                        ),
                        (
                            "ws_tph",
                            OrderedDict([("proposed", 6.8), ("clamped", 3.8)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 240),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 3.64),
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
            ("name", "clamped_ws_3p8"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ws_tph", 3.8),
                        ("air_ratio", 1.22),
                        ("blower_pct", 58.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: working-solution 6.8 -> 3.8 t/h. Process-correct vs the 162 C "
                "selectivity cap. Packing-support buckle still occurs at 21.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held tower at 154 C. At 21.600 ms stored strain "
                "in the packing support still buckled a 14 mm face. Clamp reduced dump energy; "
                "it did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("working_solution", "clamp executed; peak 154 C < 162"),
                        ("packing", "14 mm buckle at 21.600 ms"),
                        ("repair", "18 min oxidizer isolate (abort_s=1080)"),
                        ("mission", "X-3 air-oxidation pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither tower RTD nor working-solution FT predicted the packing charge; ae.pack.buckle is a new channel at 21.600 ms, 15.040 ms after the gate, still inside the 44 ms raster.",
                    "Delayed (abort_s=1080): 18 min oxidizer isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "18 min oxidizer isolate after a 14 mm packing-support buckle. Safety head -0.62 "
                "prices the split; task_progress stays +0.32 because the working-solution clamp completed "
                "under the 162 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.ox.c (5.720 ms, 176 C)"),
                        ("loser", "ft.ws.tph (5.960 ms, 6.8 t/h)"),
                        ("margin_us", 240),
                        (
                            "counterfactual_if_reversed",
                            "Feed-first by < 240 us inside the 400 us window would have kept "
                            "6.8 t/h cruise; predicted next-sample 168 C would have exceeded "
                            "the 162 cap even without the packing charge. The MODIFY is still the "
                            "correct process. The buckle is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 21600),
            (
                "reward_inflection_note",
                "Safety collapses at the 21.600 ms packing-support buckle (tick t_us=21600), inside "
                "the 44 ms raster. The correct MODIFY at 6.560 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=1080 isolate tick.",
            ),
            ("delayed_surprise_s", 1080.0),
            ("abort_s", 1080),
        ]
    )
    spikes = [
        spike("enc.ws.ctx", 1.180, 0.43),
        spike("rtd.ox.c", 2.180, 0.62),
        spike("ft.ws.tph", 3.440, 0.51),
        spike("rtd.ox.c", 5.720, 1.34),
        spike("ft.ws.tph", 5.960, 1.16),
        spike("ctrl.gate", 6.560, 0.99),
        spike("rtd.ox.c", 8.400, 0.81),
        spike("ft.ws.tph", 11.200, 0.63),
        spike("ctrl.gate", 15.400, 0.85),
        spike("ae.pack.buckle", 21.600, 1.48),
        spike("ae.pack.buckle", 23.800, 0.92),
        spike("enc.ws.ctx", 32.400, 0.42),
        spike("rtd.ox.c", 40.200, 0.54),
    ]
    ras = raster_core(
        44,
        88,
        25,
        97,
        routing(
            "thalamic-relay.tower-ahq",
            "spikenaut.policy.ws-clamp",
            [
                ("relay.rtd.ox", "policy.ws_clamp", 0.67),
                ("relay.ft.ws", "policy.ws_hold", 0.27),
                ("relay.ae.pack", "policy.ws_clamp", -0.44),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at tower win (5.720 ms) opens a 50 ms "
            "eligibility trace that still covers the 21.600 ms packing-support buckle",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("ws_clamp", 48, 0.50, 208.3, 4),
                    pop("ws_hold", 48, 0.50, 52.1, 1),
                    pop("tower_veto", 22, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r116-596",
        "Peroxaq-Moss X-3 / AHQ oxidizer: tower 176 C beats working-solution-feed by 240 us; correct "
        "MODIFY still eats an in-window packing-support buckle (partnered negative total -0.46)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "44 ms raster. total -0.46 = 0.32 + -0.62 + -0.16 + 0.04 + -0.04. Named oxidizer "
        "isolate (abort_s=1080) is not netted into task_progress.",
        ras,
        gate,
        "anthrahydroquinone-oxidizer",
        [
            "modify",
            "partnered-negative-total",
            "independent-lif-raster",
            "sidecar-sim-only",
            "in-window-world-charge",
            "designed",
        ],
        "A critic can see the world-charge as a LIF burst inside the raster while "
        "process heads stay honest. Credit assignment is spikes, not prose across an "
        "18 min oxidizer isolate.",
        1,
    )


def record_597():
    ticks = [
        tick(1760, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(4880, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(5140, -0.03, -0.01, -0.03, -0.02, 0.01),
        tick(5720, -0.07, -0.04, -0.07, -0.04, 0.02),
        tick(6140, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(1200000000, -0.02, -0.01, -0.04, 0.00, 0.00),
    ]
    spikes = [
        spike("ft.adn.ctx", 0.880, 0.41),
        spike("live.bed.C", 1.760, 0.59),
        spike("bus.ne107.m", 2.480, 0.52),
        spike("live.bed.C", 4.880, 1.33),
        spike("bus.ne107.m", 5.140, 1.16),
        spike("ctrl.gate", 5.720, 1.01),
        spike("live.bed.C", 7.240, 0.75),
        spike("bus.ne107.m", 8.320, 0.62),
        spike("ctrl.gate", 12.400, 0.83),
        spike("ft.adn.ctx", 16.200, 0.43),
        spike("live.bed.C", 21.800, 0.54),
        spike("bus.ne107.m", 26.200, 0.48),
    ]
    excerpt = independent_excerpt(116597, 72, 30000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Hexanedinitrile membrane cell M-4 at Adipon-Nab is holding acrylonitrile at 4.8 t/h with live "
                "Type-K cathode 154.0 C against a 198.0 C trip. A leftover NAMUR NE107 Maintenance-Required "
                "status nibble still prints 248 C from diagnostic code 32 scaled as EU. Live-TC-first should "
                "ACCEPT the feed; a weak supervisor that binds the NE107 M-bit as PV will REJECT a legal EHD cell.",
            ),
            ("domain", "hexanedinitrile-membrane-cell"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep 4.8 t/h acrylonitrile on M-4 while live Type-K cathode stays <= 198.0 C; "
                "do not spend a leftover NE107 maintenance nibble on the hold.",
            ),
            ("t0_us", 1762300000000597),
            ("gate_latency_us", 840),
            ("race_window_us", 420),
            ("race_window_rel_ms", [4.88, 5.30]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "live.bed.C 154.0 C LIVE Type-K",
                                "bus.ne107.m 248 C leftover NE107 Maintenance-Required EU",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-TC-first should ACCEPT 4.8 t/h (154.0 C < 198.0 C trip). "
                            "NE107-first tempts a weak supervisor to treat 248 C as live.",
                        ),
                        (
                            "window_derivation",
                            "420 us = one M-4 Type-K sample minus leftover NE107-status group delay "
                            "on this EHD bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 260 us vs combined jitter ~62 us (live 28 + NE107 34): 4.2x over "
                            "a 2.0x trust floor. Order is correctly live-TC-first. The error is binding "
                            "the leftover NE107 M-bit as EU, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "M-4 Type-K cathode RTD, 4 kHz, 28 us jitter, LIVE analog",
                    "leftover NAMUR NE107 Maintenance-Required nibble, 4 kHz, 34 us jitter, status STALE",
                    "acrylonitrile feed FT (context)",
                    "membrane DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("trip_C", 198.0),
                        ("live_C", 154.0),
                        ("ne107_C", 248.0),
                        ("ne107_status", 32),
                        ("ne107_maintenance", True),
                        ("ne107_is_pv", False),
                        ("ne107_as_eu", True),
                        ("proposed_adn_tph", 4.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. M-4 latched on Adipon-Nab; acrylonitrile 4.8 t/h armed.",
                    "2. Live Type-K 154.0 C; leftover NE107 M-bit still prints 248 C.",
                    "3. ADN-FT precursor at 0.880 ms.",
                    "4. Race window [4.880, 5.300] ms.",
                    "5. live.bed.C 154.0 C at 4.880 ms (winner).",
                    "6. bus.ne107.m 248 C at 5.140 ms (loser by 260 us).",
                    "7. Gate at 5.720 ms: REJECT hold 0.0 t/h (incorrect).",
                    "8. Legal feed cancelled; live Type-K still 154.0 C < 198.0 C trip.",
                    "9. NE107 maintenance leftover remains the published bind.",
                    "10. Delayed missed_window_s=1200 (20 min hydrodimer window) while M-4 waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "adn_4p8"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("adn_tph", 4.8),
                        ("hold", False),
                        ("bound_tc", "live_type_k"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 154.0),
                        ("trip_C", 198.0),
                        ("ne107_C", 248.0),
                        ("ne107_status", 32),
                        ("ne107_maintenance", True),
                        ("ne107_is_pv", False),
                        ("ne107_as_eu", True),
                        ("pv_live", True),
                        ("proposed_adn_tph", 4.8),
                        ("race_margin_us", 260),
                        ("combined_jitter_us", 62),
                        ("missed_window_s", 1200),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.8 t/h acrylonitrile because live Type-K 154.0 C is under the "
                "198.0 C trip; 248 C is leftover NAMUR NE107 Maintenance-Required status 32 on the same "
                "loop, not the live cathode.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Leftover NE107 Maintenance-Required nibble still prints 248 C, over the 198.0 C trip "
                "once the supervisor treats the status code as live EU. REJECT: hold acrylonitrile "
                "0.0 t/h until the tag recovers under 198 so the EHD cell does not see an over-temp.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("published_live_trip", 198.0),
                                    ("observed_live", 154.0),
                                    ("misbound_ne107_C", 248.0),
                                    ("ne107_maintenance", True),
                                    ("ne107_is_pv", True),
                                    ("ne107_as_eu", True),
                                    ("executed_adn_tph", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 260),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 4.19),
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
            ("name", "adn_hold_ne107"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("adn_tph", 0.0),
                        ("hold", True),
                        ("bound_tc", "ne107_maintenance"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): acrylonitrile 4.8 -> 0.0 t/h. Routing relay.ne107.maint -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live 154.0 C never "
                "violated the 198.0 C trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze M-4 at 0.0 t/h while live Type-K stayed 154.0 C under the "
                "198.0 C trip. 20 min hydrodimer window missed. Correct gate was ACCEPT of "
                "the already-legal 4.8 t/h feed.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("acrylonitrile", "held at 0.0 t/h; 4.8 t/h abandoned"),
                        ("live_C", "still 154.0 C, under 198.0 C published trip"),
                        ("ehd_cell", "20 min hydrodimer window missed"),
                        ("flag", "248 C NE107-maintenance-as-PV false positive, not a live over-trip"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 248 C reading is leftover NAMUR NE107 Maintenance-Required status 32 scaled as EU, not a published live over-trip.",
                    "Delayed (missed_window_s=1200): sister M-5 ran the same 4.8 t/h hydrodimer window after QA cleared the nibble; M-4's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live 154.0 C < published 198.0 C trip; leave 4.8 t/h; ignore NE107 M-bit EU.",
                        ),
                        ("correct_trip_C", 198.0),
                        ("wrong_ne107_C", 248.0),
                        ("bound_tc_should_be", "live_type_k"),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [("adn_tph", 0.0), ("hold", True), ("bound_tc", "ne107_maintenance")]
                            ),
                        ),
                        (
                            "cost",
                            "20 min missed hydrodimer window (task/efficiency); live M-4 never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "live.bed.C (4.880 ms, 154.0 C LIVE Type-K)"),
                        ("loser", "bus.ne107.m (5.140 ms, 248 C STALE NE107 Maintenance-Required)"),
                        ("margin_us", 260),
                        (
                            "counterfactual_if_reversed",
                            "NE107-first by < 260 us would still show live 154.0 C < 198.0 C. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the live-TC "
                            "win on a leftover NE107 Maintenance-Required nibble.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5720),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (5.720 ms, tick 4). The 20 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 1200.0),
            ("missed_window_s", 1200),
        ]
    )
    ras = raster_core(
        30,
        72,
        34,
        73,
        routing(
            "relay.ne107.maint",
            "policy.hold_reject",
            [
                ("relay.ne107.maint", "policy.hold_reject", 0.78),
                ("relay.live.bed", "policy.hold_reject", 0.14),
            ],
            "acetylcholine",
            0.06,
            "ne107_maint_stdp; ACh tags the (wrong) hold_reject bind at the leftover Maintenance-Required nibble",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("missed_window_s", 1200),
                ("delayed_surprise_s", 1200),
                ("ne107_maintenance", True),
                ("ne107_is_pv", False),
                ("ne107_as_eu", True),
                ("ne107_status", 32),
                ("ne107_C", 248.0),
                ("live_C", 154.0),
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
                    pop("hold_reject", 52, 0.50, 183.2, 4),
                    pop("go_accept", 52, 0.80, 4.6, 0),
                    pop("ne107_ctx", 28, 0.55, 85.0, 1),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r116-597",
        "WRONG-REJECT at Adipon-Nab M-4: live Type-K 154.0 C < 198.0 C trip; "
        "supervisor bound leftover NAMUR NE107 Maintenance-Required status 32 (248 C) as the live cathode",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 154.0 < 198.0 on live M-4 is true; clamp bound "
        "to a 248 C leftover NE107 M-bit EU. total -0.56 = -0.20 + -0.10 + -0.22 + -0.10 + 0.06.",
        ras,
        gate,
        "hexanedinitrile-membrane-cell",
        [
            "reject",
            "wrong-gate",
            "ne107-maintenance-as-pv",
            "namur-ne107-m-bit",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed on a leftover NE107 M-bit.",
        2,
        supervisor_error_type="wrong-reject",
    )


def record_598():
    ticks = [
        tick(2040, 0.01, 0.06, 0.01, 0.01, 0.01),
        tick(5200, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5420, 0.02, 0.07, 0.02, 0.02, 0.01),
        tick(6040, 0.03, 0.12, 0.04, 0.03, 0.02),
        tick(6420, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(600000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("ir.kettle.ctx", 1.020, 0.44),
        spike("ae.kettle.pps", 2.040, 0.63),
        spike("ir.kettle.C", 3.580, 0.50),
        spike("ae.kettle.pps", 5.200, 1.36),
        spike("ir.kettle.C", 5.420, 1.13),
        spike("ctrl.gate", 6.040, 1.04),
        spike("ae.kettle.pps", 7.880, 0.78),
        spike("ir.kettle.ctx", 12.000, 0.45),
        spike("ir.kettle.C", 16.200, 0.59),
        spike("ctrl.gate", 20.800, 0.82),
        spike("ae.kettle.pps", 26.400, 0.51),
        spike("ir.kettle.C", 31.800, 0.47),
        spike("ae.kettle.ctx", 34.800, 0.41),
    ]
    excerpt = independent_excerpt(116598, 96, 36000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Vinylacetylene dimer kettle C-3 on Chloropr-Whin CW-HIL is armed for 6.4 t/h MVA while "
                "kettle AE sits at 52 pps against a 16 pps foam-collapse floor. A kettle pyrometer, lit by the "
                "pad lamp spectrum, still reports 88 C under a 124 C jacket cap. AE-first holds "
                "the dimerizer; IR-first would commit 6.4 t/h into a collapsing foam bed.",
            ),
            ("domain", "vinylacetylene-chloroprene-kettle"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Run C-3 only if kettle AE stays <= 16 pps; otherwise hold so a foam-collapse "
                "is not loaded at 6.4 t/h MVA.",
            ),
            ("t0_us", 1762300000000598),
            ("gate_latency_us", 840),
            ("race_window_us", 380),
            ("race_window_rel_ms", [5.20, 5.58]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.kettle.pps 52 pps foam collapse",
                                "ir.kettle.C 88 C pad-lamp glint",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches dimerizer hold 6.4 -> 0 t/h; IR-first would commit "
                            "6.4 t/h on a still-legal 88 C jacket-cap story.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one kettle-AE slot versus jacket-IR decode on this HIL dimerizer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter ~64 us (AE 30 + IR 34): 3.4x over "
                            "a 2.0x trust floor. Reversing order by < 220 us inside the 380 us "
                            "window would have committed 6.4 t/h into a 52 pps foam collapse.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "kettle AE puck, 5 kHz, 30 us jitter",
                    "jacket IR camera, 200 Hz, 34 us jitter",
                    "MVA encoder (context)",
                    "HCl make-up FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_foam_floor_pps", 16.0),
                        ("observed_ae_pps", 52.0),
                        ("jacket_cap_C", 124.0),
                        ("observed_jacket_C", 88.0),
                        ("proposed_mva_tph", 6.4),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("bench", "Chloropr-Whin CW-HIL vinylacetylene-chloroprene dimer pad, C-3"),
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
                    "1. C-3 indexed on Chloropr-Whin CW-HIL; MVA 6.4 t/h armed.",
                    "2. Jacket IR 88 C under 124 C cap; AE already 52 pps.",
                    "3. IR-context precursor at 1.020 ms.",
                    "4. Race window [5.200, 5.580] ms.",
                    "5. ae.kettle.pps 52 pps at 5.200 ms (winner).",
                    "6. ir.kettle.C 88 C at 5.420 ms (loser by 220 us).",
                    "7. Gate at 6.040 ms: REJECT hold dimerizer 0 t/h.",
                    "8. Pass cancelled; foam collapse not loaded.",
                    "9. HIL pad lamp spectrum remains the jacket glint source.",
                    "10. Delayed (abort_s=600): 10 min kettle re-seat before the next dimerization.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "mva_6p4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("mva_tph", 6.4),
                        ("hold", False),
                        ("kettle", "C-3"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 52.0),
                        ("ae_foam_floor_pps", 16.0),
                        ("jacket_C", 88.0),
                        ("jacket_cap_C", 124.0),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 64),
                        ("abort_s", 600),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 6.4 t/h because jacket 88 C is under the 124 C "
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
                "Kettle AE 52 pps won by 220 us, so the foam is collapsing, not still quiet. "
                "52 pps > 16 pps floor. REJECT: hold MVA 6.4 -> 0 t/h. Jacket 88 C < 124 C "
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
                                    ("floor", 16.0),
                                    ("observed", 52.0),
                                    ("executed_mva_tph", 0.0),
                                ]
                            ),
                        ),
                        (
                            "jacket_C",
                            OrderedDict(
                                [
                                    ("cap", 124.0),
                                    ("observed", 88.0),
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
                        ("mva_tph", 0.0),
                        ("hold", True),
                        ("kettle", "C-3"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (correct): MVA 6.4 -> 0 t/h. Routing relay.ae.kettle -> "
                "policy.kettle_hold. Foam collapse is not loaded.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held C-3 at 0 t/h. AE 52 pps beat jacket 88 C; kettle "
                "was already over the 16 pps foam floor. 10 min re-seat follows (abort_s=600).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("dimerizer", "held at 0 t/h; 6.4 t/h abandoned"),
                        ("kettle", "52 pps foam collapse not loaded"),
                        ("ir", "88 C still under 124 C cap"),
                        ("reseat", "10 min kettle re-seat queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Jacket IR 88 C was a HIL pad-lamp glint, not a jacket-cap exceedance.",
                    "Delayed (abort_s=600): 10 min kettle re-seat before the next dimerization on CW-HIL.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.kettle.pps (5.200 ms, 52 pps)"),
                        ("loser", "ir.kettle.C (5.420 ms, 88 C)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 220 us would have committed 6.4 t/h into a kettle "
                            "already at 52 pps. The REJECT is still the correct process; AE is the "
                            "licensing channel, not jacket IR.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6040),
            (
                "reward_inflection_note",
                "Safety and task credit the correct REJECT at 6.040 ms (tick 4). The 10 min "
                "re-seat is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 600.0),
            ("abort_s", 600),
        ]
    )
    ras = raster_core(
        36,
        96,
        24,
        83,
        routing(
            "thalamic-relay.kettle-ae",
            "spikenaut.policy.kettle-hold",
            [
                ("relay.ae.kettle", "policy.kettle_hold", 0.71),
                ("relay.ir.kettle", "policy.kettle_commit", 0.25),
                ("relay.ae.kettle", "policy.kettle_hold", 0.12),
            ],
            "dopamine",
            0.07,
            "ae_floor_stdp; DA at kettle win (5.200 ms) opens a 70 ms eligibility trace",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 600),
                ("delayed_surprise_s", 600),
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
                    pop("kettle_hold", 50, 0.50, 210.5, 4),
                    pop("kettle_commit", 50, 0.50, 52.6, 1),
                    pop("ae_veto", 26, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r116-598",
        "Chloropr-Whin CW-HIL / C-3: kettle AE 52 pps beats jacket 88 C; correct "
        "REJECT holds the vinylacetylene-chloroprene dimerizer",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 52 pps > 16 pps floor beats a legal jacket IR. "
        "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "vinylacetylene-chloroprene-kettle",
        ["reject", "hil", "kettle-ae", "vinylacetylene", "correct-gate"],
        "Teaches a kettle-AE vs pad-lamp-glint race on a HIL dimerizer: the foam floor, "
        "not the jacket cap, licenses the pass.",
        3,
    )


def record_599():
    ticks = [
        tick(1540, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(4020, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(4200, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(4660, 0.12, 0.09, 0.05, 0.03, 0.02),
        tick(4980, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(390000000, 0.03, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.meoh.ctx", 0.780, 0.42),
        spike("rtd.liq.C", 1.540, 0.59),
        spike("ir.smear.C", 2.680, 0.48),
        spike("rtd.liq.C", 4.020, 1.29),
        spike("ir.smear.C", 4.200, 1.11),
        spike("ctrl.gate", 4.660, 0.98),
        spike("rtd.liq.C", 6.480, 0.73),
        spike("enc.meoh.ctx", 10.400, 0.45),
        spike("ir.smear.C", 14.200, 0.56),
        spike("ctrl.gate", 18.400, 0.81),
        spike("rtd.liq.C", 23.200, 0.50),
    ]
    excerpt = independent_excerpt(116599, 64, 28000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Oxidative-carbonylation kettle D-7 at Dimethc-Cover is already at 42 C liquor while a "
                "coil IR smear still reports as 79 C against a 68 C cap the live RTD "
                "has not crossed. Liquor-first should ACCEPT 3.2 t/h methanol; smear-first would "
                "invent a hold on an already-legal DMC pass.",
            ),
            ("domain", "dmc-oxy-carbonylation"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Run D-7 at 3.2 t/h while liquor stays <= 68 C; do not spend a coil IR "
                "smear on the kettle hold.",
            ),
            ("t0_us", 1762300000000599),
            ("gate_latency_us", 640),
            ("race_window_us", 340),
            ("race_window_rel_ms", [4.02, 4.36]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.liq.C 42 C live",
                                "ir.smear.C as 79 C",
                            ],
                        ),
                        (
                            "semantics",
                            "Liquor-first should ACCEPT 3.2 t/h (42 C < 68 C cap). "
                            "Smear-first would hold on a simulated coil-film.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one liquor-RTD sample versus coil-IR decode on this "
                            "DMC carbonylation bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter ~54 us (RTD 24 + IR 30): 3.3x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 340 us "
                            "window would have invented a hold on an already-legal 42 C liquor.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "liquor RTD, 4 kHz, 24 us jitter",
                    "coil IR camera, 200 Hz, 30 us jitter",
                    "methanol encoder (context)",
                    "CO feed FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("liquor_cap_C", 68.0),
                        ("observed_liquor_C", 42.0),
                        ("coil_smear_C", 79.0),
                        ("proposed_meoh_tph", 3.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. D-7 indexed on Dimethc-Cover; methanol 3.2 t/h armed.",
                    "2. Liquor 42 C; coil smear as 79 C over 68 C cap.",
                    "3. Methanol-encoder precursor at 0.780 ms.",
                    "4. Race window [4.020, 4.360] ms.",
                    "5. rtd.liq.C 42 C at 4.020 ms (winner).",
                    "6. ir.smear.C at 4.200 ms (loser by 180 us).",
                    "7. Gate at 4.660 ms: ACCEPT leave 3.2 t/h.",
                    "8. Liquor remains 42 C < 68 C; smear unused as a hold.",
                    "9. Simulated coil film remains the IR source.",
                    "10. Delayed (survey_hold_s=390): 6.5 min DMC assay after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "meoh_3p2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("meoh_tph", 3.2),
                        ("hold", False),
                        ("liquor_C", 42.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("liquor_C", 42.0),
                        ("liquor_cap_C", 68.0),
                        ("coil_smear_C", 79.0),
                        ("proposed_meoh_tph", 3.2),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 54),
                        ("survey_hold_s", 390),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 3.2 t/h because liquor 42 C is under the 68 C cap; "
                "79 C is a coil IR smear, not a kettle temperature.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Liquor 42 C won by 180 us and sits under the 68 C cap. Coil smear "
                "79 C is a simulated film, not a kettle reading. ACCEPT: leave 3.2 t/h. "
                "A hold would idle a legal DMC carbonylation pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "liquor_C",
                            OrderedDict(
                                [
                                    ("cap", 68.0),
                                    ("observed", 42.0),
                                    ("executed_meoh_tph", 3.2),
                                ]
                            ),
                        ),
                        (
                            "coil_smear_C",
                            OrderedDict(
                                [
                                    ("observed", 79.0),
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
            ("name", "meoh_3p2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("meoh_tph", 3.2),
                        ("hold", False),
                        ("liquor_C", 42.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 3.2 t/h. Routing relay.rtd.liq -> policy.dmc_go. "
                "Coil smear unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left D-7 at 3.2 t/h. Liquor 42 C beat coil smear 79 C; "
                "the 68 C cap was never crossed. 6.5 min DMC assay follows "
                "(survey_hold_s=390).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("methanol", "3.2 t/h held as proposed"),
                        ("liquor", "42 C < 68 C cap"),
                        ("smear", "79 C film unused"),
                        ("survey", "6.5 min DMC assay queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "IR 79 C was a simulated coil-film smear, not a liquor over-cap.",
                    "Delayed (survey_hold_s=390): 6.5 min DMC assay after the pass on D-7.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.liq.C (4.020 ms, 42 C)"),
                        ("loser", "ir.smear.C (4.200 ms, smear 79 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Smear-first by < 180 us would still be a coil film over the "
                            "68 C cap; a correct gate ACCEPTs either way. Reversing would only "
                            "have delayed confirmation of the same legal liquor.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4660),
            (
                "reward_inflection_note",
                "Task credit lands at the correct ACCEPT (4.660 ms, tick 4). The 6.5 min "
                "DMC assay is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 390.0),
            ("survey_hold_s", 390),
        ]
    )
    ras = raster_core(
        28,
        64,
        32,
        57,
        routing(
            "thalamic-relay.liq-rtd",
            "spikenaut.policy.dmc-go",
            [
                ("relay.rtd.liq", "policy.dmc_go", 0.72),
                ("relay.ir.smear", "policy.dmc_hold", 0.18),
            ],
            "serotonin",
            0.08,
            "liquor_under_cap_stdp; 5-HT tags the go bind at the liquor RTD win",
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
            ("decision_window_ms", 0.34),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("dmc_go", 40, 0.50, 220.6, 3),
                    pop("dmc_hold", 40, 0.80, 7.4, 0),
                    pop("rtd_veto", 16, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r116-599",
        "Dimethc-Cover D-7 / DMC oxy-carbonylation: liquor 42 C beats coil smear 79 C; correct ACCEPT "
        "of an already-legal 3.2 t/h (total +1.10)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Liquor 42 C < 68 C cap; smear unused. "
        "total +1.10 = 0.42 + 0.30 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "dmc-oxy-carbonylation",
        ["accept", "simulated", "liquor-vs-smear", "already-legal", "dimethyl-carbonate"],
        "Teaches an already-legal DMC oxidative-carbonylation kettle: live liquor sits under cap; "
        "race order only confirms the ACCEPT.",
        4,
    )


def record_600():
    ticks = [
        tick(1840, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(4640, 0.09, 0.06, 0.04, 0.03, 0.02),
        tick(4840, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(5360, 0.13, 0.10, 0.05, 0.03, 0.02),
        tick(5720, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(480000000, 0.03, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.iba.ctx", 0.920, 0.41),
        spike("rtd.bed.C", 1.840, 0.58),
        spike("ir.vapor.C", 3.000, 0.47),
        spike("rtd.bed.C", 4.640, 1.28),
        spike("ir.vapor.C", 4.840, 1.10),
        spike("ctrl.gate", 5.360, 0.97),
        spike("rtd.bed.C", 7.220, 0.74),
        spike("enc.iba.ctx", 10.800, 0.44),
        spike("ir.vapor.C", 14.800, 0.55),
        spike("ctrl.gate", 18.800, 0.80),
        spike("rtd.bed.C", 21.400, 0.49),
    ]
    excerpt = independent_excerpt(116600, 48, 22000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Oleflex isobutane bed B-2 at Prodehy-Hawes already holds catalyst 512 C against a 548 C "
                "cap while overhead vapor IR still smears as 571 C. Bed-first should ACCEPT 8.6 t/h "
                "isobutane; vapor-first would invent a hold on an already-legal PDH pass.",
            ),
            ("domain", "isobutane-oleflex-bed"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run B-2 at 8.6 t/h while bed stays <= 548 C; do not spend overhead vapor "
                "smear on the dehydrogenator hold.",
            ),
            ("t0_us", 1762300000000600),
            ("gate_latency_us", 720),
            ("race_window_us", 360),
            ("race_window_rel_ms", [4.64, 5.00]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bed.C 512 C live catalyst",
                                "ir.vapor.C as 571 C smear",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first should ACCEPT 8.6 t/h (512 C < 548 C cap). "
                            "Vapor-first would hold on an unused overhead smear.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one bed-RTD sample versus overhead-IR decode on this "
                            "Oleflex PDH bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 200 us vs combined jitter ~58 us (RTD 26 + IR 32): 3.4x over "
                            "a 2.0x trust floor. Reversing order by < 200 us inside the 360 us "
                            "window would have invented a hold on an already-legal 512 C bed.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed RTD, 4 kHz, 26 us jitter",
                    "overhead IR, 200 Hz, 32 us jitter",
                    "isobutane encoder (context)",
                    "hydrogen FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 548.0),
                        ("observed_bed_C", 512.0),
                        ("vapor_smear_C", 571.0),
                        ("proposed_iba_tph", 8.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. B-2 indexed on Prodehy-Hawes; isobutane 8.6 t/h armed.",
                    "2. Bed 512 C; vapor smear as 571 C over 548 C cap.",
                    "3. Encoder precursor at 0.920 ms.",
                    "4. Race window [4.640, 5.000] ms.",
                    "5. rtd.bed.C 512 C at 4.640 ms (winner).",
                    "6. ir.vapor.C at 4.840 ms (loser by 200 us).",
                    "7. Gate at 5.360 ms: ACCEPT leave 8.6 t/h.",
                    "8. Bed remains 512 C < 548 C; smear unused as a hold.",
                    "9. Overhead unused as a process PV.",
                    "10. Delayed (dwell_s=480): 8 min conversion dwell after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "iba_8p6"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("iba_tph", 8.6),
                        ("hold", False),
                        ("bed_C", 512.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 512.0),
                        ("bed_cap_C", 548.0),
                        ("vapor_smear_C", 571.0),
                        ("proposed_iba_tph", 8.6),
                        ("race_margin_us", 200),
                        ("combined_jitter_us", 58),
                        ("dwell_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 8.6 t/h because bed 512 C is under the 548 C cap; "
                "571 C is overhead vapor smear, not bed temperature.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 512 C won by 200 us and sits under the 548 C cap. Overhead smear "
                "571 C is unused vapor IR, not a bed reading. ACCEPT: leave 8.6 t/h. "
                "A hold would idle a legal Oleflex PDH pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 548.0),
                                    ("observed", 512.0),
                                    ("executed_iba_tph", 8.6),
                                ]
                            ),
                        ),
                        (
                            "vapor_smear_C",
                            OrderedDict(
                                [
                                    ("observed", 571.0),
                                    ("not_a_bed_reading", True),
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
            ("name", "iba_8p6"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("iba_tph", 8.6),
                        ("hold", False),
                        ("bed_C", 512.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 8.6 t/h. Routing relay.rtd.bed -> policy.pdh_go. "
                "Overhead unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left B-2 at 8.6 t/h. Bed 512 C beat vapor smear 571 C; "
                "the 548 C cap was never crossed. 8 min conversion dwell follows (dwell_s=480).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("isobutane", "8.6 t/h held as proposed"),
                        ("bed", "512 C < 548 C cap"),
                        ("smear", "571 C vapor unused"),
                        ("dwell", "8 min conversion dwell queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "IR 571 C was overhead vapor smear, not a bed over-cap.",
                    "Delayed (dwell_s=480): 8 min conversion dwell after the pass on B-2.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.C (4.640 ms, 512 C)"),
                        ("loser", "ir.vapor.C (4.840 ms, smear 571 C)"),
                        ("margin_us", 200),
                        (
                            "counterfactual_if_reversed",
                            "Vapor-first by < 200 us would still be unused overhead smear; "
                            "a correct gate ACCEPTs either way. Reversing would only have delayed "
                            "confirmation of the same legal bed.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5360),
            (
                "reward_inflection_note",
                "Task credit lands at the correct ACCEPT (5.360 ms, tick 4). The 8 min "
                "conversion dwell is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480.0),
            ("dwell_s", 480),
        ]
    )
    ras = raster_core(
        22,
        48,
        42,
        44,
        routing(
            "thalamic-relay.bed-rtd",
            "spikenaut.policy.pdh-go",
            [
                ("relay.rtd.bed", "policy.pdh_go", 0.73),
                ("relay.ir.vapor", "policy.pdh_hold", 0.16),
            ],
            "adenosine",
            0.09,
            "bed_under_cap_stdp; adenosine tags the go bind at the bed RTD win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("dwell_s", 480),
                ("delayed_surprise_s", 480),
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
                    pop("pdh_go", 36, 0.50, 231.5, 3),
                    pop("pdh_hold", 36, 0.80, 7.7, 0),
                    pop("rtd_veto", 16, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r116-600",
        "Prodehy-Hawes B-2 / Oleflex: bed 512 C beats vapor smear 571 C; correct ACCEPT "
        "of an already-legal 8.6 t/h (total +1.14)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Bed 512 C < 548 C cap; vapor unused. "
        "total +1.14 = 0.44 + 0.32 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "isobutane-oleflex-bed",
        ["accept", "designed", "bed-vs-vapor", "already-legal", "oleflex-pdh"],
        "Teaches an already-legal Oleflex isobutane bed: live catalyst sits under cap; "
        "race order only confirms the ACCEPT.",
        5,
    )

