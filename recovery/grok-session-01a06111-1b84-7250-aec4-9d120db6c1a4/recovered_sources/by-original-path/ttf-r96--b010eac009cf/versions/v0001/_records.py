def lif_496_excerpt():
    n = 82
    dt_us = 100
    tau_m_ms = 16.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.88
    i_stim_peak = 2.48
    stim = (21400, 25000)
    seed = 96496
    window_us = 44000
    i_clamp_extra = 0.66
    clamp_n = 18
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
    burst = [(t, nid) for t, nid in spikes if 21400 <= t < 25000]
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
    take(burst, 9, label_times=(22600, 23600, 24600))
    clamp = [(t, nid) for t, nid in picked if t < 21400][:7]
    pack = [(t, nid) for t, nid in picked if t >= 21400][:9]
    picked = sorted(clamp + pack, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(
            f"LIF excerpt too short {len(picked)} (early={len(early)} burst={len(burst)})"
        )
    channels = ["lif.clamp" if t < 21400 else "lif.disk" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 82),
            ("dt_us", 100),
            ("tau_m_ms", 16.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.88),
            ("i_stim_peak", 2.48),
            ("stim_t_us", [21400, 25000]),
            ("i_clamp_extra", 0.66),
            ("clamp_n", 18),
            ("seed", 96496),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-17 carry +0.66 ethylene-clamp bias; stim 21.4-25.0 ms is the rupture-disk blow.",
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


def record_496():
    excerpt, extra = lif_496_excerpt()
    ticks = [
        tick(2480, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6240, 0.07, -0.04, -0.03, 0.01, -0.01),
        tick(6424, 0.05, -0.03, -0.02, 0.00, 0.00),
        tick(7000, 0.08, -0.06, -0.03, 0.02, -0.01),
        tick(22600, 0.04, -0.38, -0.04, -0.01, -0.02),
        tick(960000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Autoclave-A4 at Ldpe-Grain LG-2 is already pushing 12.0 t/h ethylene into a 268 C "
                "wall against a 255 C metal-temperature cap. A wall-first latch clamps the ethylene; "
                "a feed-first story would keep the 12.0 t/h cruise. Stored rupture-disk strain is not "
                "yet an observable of either race channel.",
            ),
            ("domain", "ldpe-autoclave"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the LG-2 high-pressure pass, keep autoclave wall <= 255 C, and leave the "
                "rupture disk unmarked.",
            ),
            ("t0_us", 1756850400000496),
            ("gate_latency_us", 760),
            ("race_window_us", 400),
            ("race_window_rel_ms", [6.20, 6.60]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.wall.C 268 C pulse",
                                "ft.ethene.tph 12.0 t/h cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Wall-first latches ethylene 12.0 -> 6.8 t/h; feed-first keeps "
                            "cruise on a still-cooling disk model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one 2 kHz wall-RTD sample minus ethylene-orifice group "
                            "delay on this autoclave bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 184 us vs combined jitter ~62 us (wall 28 + ethylene 34): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 184 us inside the 400 us window "
                            "would have kept 12.0 t/h cruise; predicted next-sample 261 C > 255 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "wall multiplex RTD, 2 kHz, 28 us timestamp jitter",
                    "ethylene feed FT, 1 kHz, 34 us jitter",
                    "rupture-disk AE puck (context until the blow)",
                    "initiator analyzer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("wall_cap_C", 255.0),
                        ("observed_wall_C", 268.0),
                        ("proposed_ethene_tph", 12.0),
                        ("initiator_kgh", 18.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Autoclave-A4 indexed on Ldpe-Grain LG-2; ethylene armed at 12.0 t/h.",
                    "2. Cruise 12.0 t/h; wall 268 C against 255 C metal-temperature cap.",
                    "3. Ethylene precursor at 1.180 ms; wall warm-start 268 C.",
                    "4. Race window [6.200, 6.600] ms opens on the autoclave bus.",
                    "5. rtd.wall.C 268 C at 6.240 ms (winner).",
                    "6. ft.ethene.tph 12.0 t/h at 6.424 ms (loser by 184 us).",
                    "7. Gate at 7.000 ms (winner + 760 us): MODIFY clamp 12.0 -> 6.8 t/h.",
                    "8. Clamp executes; next-sample wall 248 C < 255 cap.",
                    "9. At 22.600 ms stored strain still blows 12 mm of rupture disk; AE burst.",
                    "10. Autoclave isolate 16 min (abort_s=960); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_ethene_12"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ethene_tph", 12.0),
                        ("initiator_kgh", 18.4),
                        ("agitator_rpm", 0.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("wall_C", 268.0),
                        ("wall_cap_C", 255.0),
                        ("predicted_unclamped_next_C", 261.0),
                        ("ethene_tph", 12.0),
                        ("race_margin_us", 184),
                        ("combined_jitter_us", 62),
                        ("abort_s", 960),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 12.0 t/h cruise: 268 C looks like an initiator-analyzer spike, not "
                "lid contact, and A4 volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Wall 268 C won by 184 us, so the lid is loading heat, not still cooling. "
                "Holding 12.0 t/h predicts next-sample 261 C > 255 cap. MODIFY: ethylene 12.0 -> "
                "6.8 t/h. Observed after clamp 248 C < 255. A full REJECT is not indicated: a "
                "sound LDPE pass accepts 6.8 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "wall_C",
                            OrderedDict(
                                [
                                    ("cap", 255.0),
                                    ("observed", 268.0),
                                    ("predicted_unclamped_next", 261.0),
                                    ("clamped_ethene_tph", 6.8),
                                    ("observed_after_clamp", 248.0),
                                ]
                            ),
                        ),
                        (
                            "ethene_tph",
                            OrderedDict([("proposed", 12.0), ("clamped", 6.8)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 184),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 2.97),
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
            ("name", "clamped_ethene_6p8"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ethene_tph", 6.8),
                        ("initiator_kgh", 18.4),
                        ("agitator_rpm", 0.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: ethylene 12.0 -> 6.8 t/h. Process-correct vs the 255 C wall "
                "cap. Disk blow still occurs at 22.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held wall at 248 C. At 22.600 ms stored strain "
                "in the rupture disk still blew a 12 mm face. Clamp reduced dump energy; "
                "it did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("ethene", "clamp executed; peak 248 C < 255"),
                        ("disk", "12 mm blow at 22.600 ms"),
                        ("repair", "16 min autoclave isolate (abort_s=960)"),
                        ("mission", "LG-2 high-pressure pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither wall RTD nor ethylene FT predicted the disk charge; ae.disk.blow is a new channel at 22.600 ms, 15.600 ms after the gate, still inside the 44 ms raster.",
                    "Delayed (abort_s=960): 16 min autoclave isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "16 min autoclave isolate after a 12 mm rupture-disk blow. Safety head -0.58 "
                "prices the split; task_progress stays +0.30 because the ethylene clamp completed "
                "under the 255 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.wall.C (6.240 ms, 268 C)"),
                        ("loser", "ft.ethene.tph (6.424 ms, 12.0 t/h)"),
                        ("margin_us", 184),
                        (
                            "counterfactual_if_reversed",
                            "Feed-first by < 184 us inside the 400 us window would have kept "
                            "12.0 t/h cruise; predicted next-sample 261 C would have exceeded "
                            "the 255 cap even without the disk charge. The MODIFY is still the "
                            "correct process. The blow is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22600),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.600 ms rupture-disk blow (tick t_us=22600), inside "
                "the 44 ms raster. The correct MODIFY at 7.000 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=960 isolate tick.",
            ),
            ("delayed_surprise_s", 960.0),
            ("abort_s", 960),
        ]
    )
    spikes = [
        spike("enc.ldpe.ctx", 1.180, 0.42),
        spike("rtd.wall.C", 2.480, 0.61),
        spike("ft.ethene.tph", 3.740, 0.50),
        spike("rtd.wall.C", 6.240, 1.32),
        spike("ft.ethene.tph", 6.424, 1.14),
        spike("ctrl.gate", 7.000, 0.98),
        spike("rtd.wall.C", 8.720, 0.80),
        spike("ft.ethene.tph", 11.400, 0.62),
        spike("ctrl.gate", 16.200, 0.84),
        spike("ae.disk.blow", 22.600, 1.46),
        spike("ae.disk.blow", 24.400, 0.91),
        spike("enc.ldpe.ctx", 32.100, 0.41),
        spike("rtd.wall.C", 41.200, 0.53),
    ]
    ras = raster_core(
        44,
        82,
        24,
        87,
        routing(
            "thalamic-relay.wall-disk",
            "spikenaut.policy.ethene-clamp",
            [
                ("relay.rtd.wall", "policy.ethene_clamp", 0.67),
                ("relay.ft.ethene", "policy.ethene_hold", 0.29),
                ("relay.ae.disk", "policy.ethene_clamp", -0.44),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at wall win (6.240 ms) opens a 50 ms "
            "eligibility trace that still covers the 22.600 ms rupture-disk blow",
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
                    pop("ethene_clamp", 44, 0.50, 227.3, 4),
                    pop("ethene_hold", 44, 0.50, 56.8, 1),
                    pop("wall_veto", 22, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r96-496",
        "Ldpe-Grain LG-2 / Autoclave-A4: wall 268 C beats ethylene feed by 184 us; correct "
        "MODIFY still eats an in-window rupture-disk blow (partnered negative total -0.45)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "44 ms raster. total -0.45 = 0.30 + -0.58 + -0.16 + 0.04 + -0.05. Named autoclave "
        "isolate (abort_s=960) is not netted into task_progress.",
        ras,
        gate,
        "ldpe-autoclave",
        [
            "modify",
            "partnered-negative",
            "independent-lif-raster",
            "sidecar-sim-only",
            "designed",
        ],
        "Teaches an in-window world charge after a process-correct clamp: LIF excerpt is "
        "membrane crossings, not a remap of spike_events; safety prices the disk, task stays honest.",
        1,
    )


def record_497():
    ticks = [
        tick(1880, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(4540, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(4700, -0.03, -0.01, -0.03, -0.02, 0.01),
        tick(5140, -0.07, -0.05, -0.08, -0.05, 0.02),
        tick(7320, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(1140000000, -0.02, -0.01, -0.04, -0.01, 0.00),
    ]
    spikes = [
        spike("ft.ethene.ctx", 0.880, 0.40),
        spike("live.tc.eu", 1.880, 0.58),
        spike("tc.stale.eu", 2.640, 0.51),
        spike("live.tc.eu", 4.540, 1.32),
        spike("tc.stale.eu", 4.700, 1.15),
        spike("ctrl.gate", 5.140, 1.00),
        spike("live.tc.eu", 7.320, 0.74),
        spike("tc.stale.eu", 8.480, 0.61),
        spike("ctrl.gate", 12.400, 0.82),
        spike("ft.ethene.ctx", 16.800, 0.42),
        spike("live.tc.eu", 21.600, 0.53),
        spike("tc.stale.eu", 25.900, 0.47),
    ]
    excerpt = independent_excerpt(96497, 94, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "EO-tube ET-6 on Oxirane-Clough OC-5 is holding ethylene at 9.6 t/h with live "
                "Type-K hotspot 218 C against a 280 C trip. A leftover Type-S millivolt table plus "
                "a leftover 32 C ice-point card from last catalyst change still sit on the "
                "transmitter. Live-K-first should ACCEPT the feed; a weak supervisor that binds "
                "the Type-S table and reapplies the ice-point will REJECT a legal tubular.",
            ),
            ("domain", "ethylene-oxide-tubular"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep 9.6 t/h ethylene on ET-6 while live Type-K stays <= 280 C; "
                "do not spend a leftover Type-S table or a 32 C ice-point card on the hold.",
            ),
            ("t0_us", 1756850400000497),
            ("gate_latency_us", 600),
            ("race_window_us", 280),
            ("race_window_rel_ms", [4.48, 4.76]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "live.tc.eu 218 C Type K already compensated",
                                "tc.stale.eu 312 C Type-S table plus leftover 32 C ice-point",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-K-first should ACCEPT 9.6 t/h (218 C < 280 C trip). "
                            "Stale-S-first tempts a weak supervisor to treat 312 C as live.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one ET-6 Type-K sample minus leftover Type-S transmitter "
                            "group delay on this EO bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter ~54 us (live 24 + stale 30): 3.0x over "
                            "a 2.0x trust floor. Order is correctly live-K-first. The error is binding "
                            "the leftover Type-S table plus ice-point, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "ET-6 hotspot Type K, 4 kHz, 24 us jitter, ITS-90 LIVE",
                    "leftover Type-S millivolt card, 4 kHz, 30 us jitter, STALE",
                    "ethylene FT (context)",
                    "oxygen analyzer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("trip_C", 280.0),
                        ("live_C", 218.0),
                        ("published_tc_type", "K"),
                        ("bound_tc_type", "S"),
                        ("scaled_wrong_C", 312.0),
                        ("cj_offset_C", 32.0),
                        ("live_mV", 8.90),
                        ("proposed_feed_tph", 9.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. ET-6 latched on Oxirane-Clough OC-5; ethylene 9.6 t/h armed.",
                    "2. Live Type-K 8.90 mV = 218 C compensated; leftover Type-S table plus 32 C ice-point scales 312 C.",
                    "3. Ethylene-FT precursor at 0.880 ms.",
                    "4. Race window [4.480, 4.760] ms.",
                    "5. live.tc.eu 218 C at 4.540 ms (winner).",
                    "6. tc.stale.eu 312 C at 4.700 ms (loser by 160 us).",
                    "7. Gate at 5.140 ms: REJECT hold 0.0 t/h (incorrect).",
                    "8. Legal ethylene cancelled; live 218 C still < 280 C trip.",
                    "9. Type-S bind remains; leftover ice-point unused as a live sensor.",
                    "10. Delayed missed_window_s=1140 (19 min selectivity window) while ET-6 waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "feed_9p6"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 9.6),
                        ("hold", False),
                        ("bound_tc_type", "K"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 218.0),
                        ("trip_C", 280.0),
                        ("published_tc_type", "K"),
                        ("bound_tc_type", "K"),
                        ("scaled_wrong_C", 312.0),
                        ("cj_offset_C", 32.0),
                        ("live_mV", 8.90),
                        ("tc_type_swap", False),
                        ("cj_offset_applied_twice", False),
                        ("pv_live", True),
                        ("proposed_feed_tph", 9.6),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 54),
                        ("missed_window_s", 1140),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 9.6 t/h feed because live Type-K 8.90 mV is 218 C under the "
                "280 C trip; 312 C is a leftover Type-S table plus a leftover 32 C ice-point, "
                "not the live EU.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Leftover Type-S millivolt table plus leftover 32 C ice-point card scales 8.90 mV "
                "to 312 C, over the 280 C trip once the supervisor treats that card as live. "
                "REJECT: hold ethylene 0.0 t/h until the tag recovers under 280 so the tubular "
                "does not see a hotspot event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "eo_hotspot_C",
                            OrderedDict(
                                [
                                    ("published_live_trip", 280.0),
                                    ("observed_live", 218.0),
                                    ("misbound_tc_type", "S"),
                                    ("scaled_wrong_C", 312.0),
                                    ("cj_offset_C", 32.0),
                                    ("live_mV", 8.90),
                                    ("tc_type_swap", True),
                                    ("cj_offset_applied_twice", True),
                                    ("executed_feed_tph", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 160),
                                    ("combined_jitter_us", 54),
                                    ("ratio", 2.96),
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
            ("name", "feed_hold_stale_tc"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 0.0),
                        ("hold", True),
                        ("bound_tc_type", "S"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): feed 9.6 -> 0.0 t/h. Routing relay.tc.stale -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live 218 C never "
                "violated the 280 C trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze ET-6 at 0.0 t/h while live Type-K stayed 218 C under the "
                "280 C trip. 19 min selectivity window missed. Correct gate was ACCEPT of "
                "the already-legal 9.6 t/h feed.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held at 0.0 t/h; 9.6 t/h abandoned"),
                        ("live_C", "still 218 C, under 280 C published trip"),
                        ("loop", "19 min selectivity window missed"),
                        ("tc", "312 C leftover Type-S plus ice-point false positive, not a live over-trip"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 312 C reading is a leftover Type-S millivolt table plus a leftover 32 C ice-point applied to an already-compensated Type-K PV, not a published live over-trip.",
                    "Delayed (missed_window_s=1140): sister ET-7 ran the same 9.6 t/h selectivity window after QA rebound the Type-K map; ET-6's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live 218 C < published 280 C trip; leave 9.6 t/h; bind Type K; drop leftover ice-point.",
                        ),
                        ("correct_trip_C", 280.0),
                        ("wrong_scaled_C", 312.0),
                        ("bound_tc_should_be", "K"),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [("feed_tph", 0.0), ("hold", True), ("bound_tc_type", "S")]
                            ),
                        ),
                        (
                            "cost",
                            "19 min missed selectivity window (task/efficiency); live tubular never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "live.tc.eu (4.540 ms, 218 C Type K)"),
                        ("loser", "tc.stale.eu (4.700 ms, 312 C leftover Type-S plus ice-point)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Stale-S-first by < 160 us would still show live 218 C < 280 C. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the live-K "
                            "win on a leftover Type-S table plus a leftover 32 C ice-point.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5140),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (5.140 ms, tick 4). The 19 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 1140.0),
            ("missed_window_s", 1140),
        ]
    )
    ras = raster_core(
        28,
        94,
        32,
        84,
        routing(
            "relay.tc.stale",
            "policy.hold_reject",
            [
                ("relay.tc.stale", "policy.hold_reject", 0.75),
                ("relay.live.tc", "policy.hold_reject", 0.18),
            ],
            "acetylcholine",
            0.06,
            "tc_type_swap_stdp; ACh tags the (wrong) hold_reject bind at the leftover Type-S shadow",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("missed_window_s", 1140),
                ("delayed_surprise_s", 1140),
                ("tc_type_swap", True),
                ("cj_offset_applied_twice", True),
                ("live_C", 218.0),
                ("bound_tc_type", "S"),
                ("scaled_wrong_C", 312.0),
                ("cj_offset_C", 32.0),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.28),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 50, 0.50, 285.7, 4),
                    pop("go_accept", 50, 0.80, 7.1, 0),
                    pop("tc_ctx", 28, 0.55, 71.4, 1),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r96-497",
        "WRONG-REJECT at Oxirane-Clough OC-5 / ET-6: live Type-K 218 C < 280 C trip; "
        "supervisor bound leftover Type-S table (312 C) plus leftover 32 C ice-point",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 218 < 280 on live Type K is true; clamp bound "
        "to a 312 C leftover Type-S plus ice-point. total -0.60 = -0.20 + -0.11 + -0.23 + -0.12 + 0.06.",
        ras,
        gate,
        "ethylene-oxide-tubular",
        [
            "reject",
            "wrong-gate",
            "tc-type-swap",
            "cold-junction-offset",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live<trip Type-K read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed on a leftover Type-S table.",
        2,
        supervisor_error_type="wrong-reject",
    )


def record_498():
    ticks = [
        tick(2280, 0.01, 0.06, 0.01, 0.01, 0.01),
        tick(5480, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5672, 0.02, 0.07, 0.02, 0.02, 0.01),
        tick(6280, 0.03, 0.12, 0.04, 0.03, 0.02),
        tick(8160, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("ir.bath.ctx", 1.140, 0.43),
        spike("ae.tin.pps", 2.280, 0.62),
        spike("ir.bath.C", 3.780, 0.49),
        spike("ae.tin.pps", 5.480, 1.35),
        spike("ir.bath.C", 5.672, 1.12),
        spike("ctrl.gate", 6.280, 1.03),
        spike("ae.tin.pps", 8.160, 0.77),
        spike("ir.bath.ctx", 12.400, 0.44),
        spike("ir.bath.C", 16.800, 0.58),
        spike("ctrl.gate", 21.600, 0.81),
        spike("ae.tin.pps", 28.200, 0.50),
        spike("ir.bath.C", 33.400, 0.46),
        spike("ae.tin.ctx", 38.100, 0.40),
    ]
    excerpt = independent_excerpt(96498, 110, 40000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Ribbon-R2 on Tinbath-Howe TH-HIL is armed for a 420 t/d float-glass pull while "
                "tin-wetting AE sits at 52 pps against a 16 pps leak floor. A bath pyrometer, lit "
                "by the pad lamp spectrum, still reports 718 C under an 850 C bath cap. AE-first "
                "holds the pull; IR-first would commit 420 t/d into a wetting leak.",
            ),
            ("domain", "float-glass-tin-bath"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Run R2 only if tin AE stays <= 16 pps; otherwise hold so a wetting leak is "
                "not loaded at 420 t/d.",
            ),
            ("t0_us", 1756850400000498),
            ("gate_latency_us", 800),
            ("race_window_us", 420),
            ("race_window_rel_ms", [5.44, 5.86]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.tin.pps 52 pps tin-wetting leak",
                                "ir.bath.C 718 C pad-lamp glint",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches ribbon hold 420 -> 0 t/d; IR-first would commit "
                            "420 t/d on a still-legal 718 C bath-cap story.",
                        ),
                        (
                            "window_derivation",
                            "420 us = one tin-AE slot versus bath-IR decode on this HIL float-glass bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 192 us vs combined jitter ~68 us (AE 32 + IR 36): 2.8x over "
                            "a 2.0x trust floor. Reversing order by < 192 us inside the 420 us "
                            "window would have committed 420 t/d into a 52 pps wetting leak.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "tin-bath AE puck, 5 kHz, 32 us jitter",
                    "bath IR camera, 200 Hz, 36 us jitter",
                    "ribbon encoder (context)",
                    "N2/H2 atmosphere PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_leak_floor_pps", 16.0),
                        ("observed_ae_pps", 52.0),
                        ("bath_cap_C", 850.0),
                        ("observed_bath_C", 718.0),
                        ("proposed_pull_td", 420.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Ribbon-R2 indexed on Tinbath-Howe TH-HIL; pull 420 t/d armed.",
                    "2. Bath IR 718 C under 850 C cap; AE already 52 pps.",
                    "3. IR-context precursor at 1.140 ms.",
                    "4. Race window [5.440, 5.860] ms.",
                    "5. ae.tin.pps 52 pps at 5.480 ms (winner).",
                    "6. ir.bath.C 718 C at 5.672 ms (loser by 192 us).",
                    "7. Gate at 6.280 ms: REJECT hold ribbon 0 t/d.",
                    "8. Pass cancelled; wetting leak not loaded.",
                    "9. HIL pad lamp spectrum remains the bath glint source.",
                    "10. Delayed (abort_s=480): 8 min tin re-wet before the next pull.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "pull_420"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pull_td", 420.0),
                        ("hold", False),
                        ("train", "R2"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 52.0),
                        ("ae_leak_floor_pps", 16.0),
                        ("bath_C", 718.0),
                        ("bath_cap_C", 850.0),
                        ("race_margin_us", 192),
                        ("combined_jitter_us", 68),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 420 t/d because bath 718 C is under the 850 C "
                "cap and treats the AE puck as atmosphere-PT noise.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Tin AE 52 pps won by 192 us, so the bath is wetting-leaking, not still quiet. "
                "52 pps > 16 pps floor. REJECT: hold pull 420 -> 0 t/d. Bath 718 C < 850 C "
                "does not license the pass once AE is over floor.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tin_ae_pps",
                            OrderedDict(
                                [
                                    ("floor", 16.0),
                                    ("observed", 52.0),
                                    ("executed_pull_td", 0.0),
                                ]
                            ),
                        ),
                        (
                            "bath_C",
                            OrderedDict(
                                [
                                    ("cap", 850.0),
                                    ("observed", 718.0),
                                    ("does_not_license_pass", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 192),
                                    ("combined_jitter_us", 68),
                                    ("ratio", 2.82),
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
            ("name", "tin_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pull_td", 0.0),
                        ("hold", True),
                        ("train", "R2"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (correct): pull 420 -> 0 t/d. Routing relay.ae.tin -> "
                "policy.tin_hold. Wetting leak is not loaded.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held R2 at 0 t/d. AE 52 pps beat bath 718 C; tin "
                "was already over the 16 pps leak floor. 8 min re-wet follows (abort_s=480).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("ribbon", "held at 0 t/d; 420 t/d abandoned"),
                        ("tin", "52 pps leak not loaded"),
                        ("bath", "718 C still under 850 C cap"),
                        ("rewet", "8 min tin re-wet queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Bath IR 718 C was a HIL pad-lamp glint, not a bath-cap exceedance.",
                    "Delayed (abort_s=480): 8 min tin re-wet before the next pull on TH-HIL.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.tin.pps (5.480 ms, 52 pps)"),
                        ("loser", "ir.bath.C (5.672 ms, 718 C)"),
                        ("margin_us", 192),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 192 us would have committed 420 t/d into a bath "
                            "already at 52 pps. The REJECT is still the correct process; AE is the "
                            "licensing channel, not bath IR.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6280),
            (
                "reward_inflection_note",
                "Safety and task credit the correct REJECT at 6.280 ms (tick 4). The 8 min "
                "re-wet is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480.0),
            ("abort_s", 480),
        ]
    )
    ras = raster_core(
        40,
        110,
        22,
        97,
        routing(
            "thalamic-relay.tin-ae",
            "spikenaut.policy.tin-hold",
            [
                ("relay.ae.tin", "policy.tin_hold", 0.69),
                ("relay.ir.bath", "policy.tin_commit", 0.26),
                ("relay.ae.tin", "policy.tin_hold", 0.11),
            ],
            "dopamine",
            0.07,
            "ae_floor_stdp; DA at tin win (5.480 ms) opens a 70 ms eligibility trace",
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
            ("decision_window_ms", 0.42),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("tin_hold", 56, 0.50, 212.6, 5),
                    pop("tin_commit", 56, 0.50, 42.5, 1),
                    pop("ae_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r96-498",
        "Tinbath-Howe TH-HIL / Ribbon-R2: tin AE 52 pps beats bath 718 C; correct "
        "REJECT holds the float-glass pull",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 52 pps > 16 pps floor beats a legal bath IR. "
        "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "float-glass-tin-bath",
        ["reject", "hil", "tin-ae", "float-glass", "correct-gate"],
        "Teaches a tin-AE vs pad-lamp-glint race on a HIL float-glass bath: the leak floor, "
        "not the bath cap, licenses the pull.",
        3,
    )


def record_499():
    ticks = [
        tick(1720, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(4280, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(4424, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(4820, 0.12, 0.09, 0.05, 0.03, 0.02),
        tick(6640, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(270000000, 0.03, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.pbd.ctx", 0.760, 0.41),
        spike("rtd.kettle.C", 1.720, 0.58),
        spike("ir.jacket.C", 2.960, 0.47),
        spike("rtd.kettle.C", 4.280, 1.28),
        spike("ir.jacket.C", 4.424, 1.10),
        spike("ctrl.gate", 4.820, 0.97),
        spike("rtd.kettle.C", 6.640, 0.72),
        spike("enc.pbd.ctx", 10.200, 0.44),
        spike("ir.jacket.C", 14.400, 0.55),
        spike("ctrl.gate", 18.600, 0.80),
        spike("rtd.kettle.C", 22.400, 0.49),
        spike("enc.pbd.ctx", 25.200, 0.38),
    ]
    excerpt = independent_excerpt(96499, 58, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Kettle-K3 of Diene-Riggs DR-6 is already at 64.0 C solution temperature while a "
                "jacket-coil IR smear still reports 89 C against an 82 C trip the live RTD has "
                "not crossed. Kettle-first should ACCEPT 7.6 t/h butadiene; glint-first would "
                "invent a hold on an already-legal solution pass.",
            ),
            ("domain", "polybutadiene-solution-kettle"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Run K3 at 7.6 t/h while kettle stays <= 82 C; do not spend a jacket-coil "
                "IR smear on the solution hold.",
            ),
            ("t0_us", 1756850400000499),
            ("gate_latency_us", 540),
            ("race_window_us", 300),
            ("race_window_rel_ms", [4.24, 4.54]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.kettle.C 64.0 C live",
                                "ir.jacket.C smear 89 C",
                            ],
                        ),
                        (
                            "semantics",
                            "Kettle-first should ACCEPT 7.6 t/h (64.0 C < 82 C trip). "
                            "Glint-first would hold on a simulated jacket smear.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one kettle RTD sample versus jacket-IR decode on this "
                            "solution-polymer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 144 us vs combined jitter ~50 us (RTD 22 + IR 28): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 144 us inside the 300 us "
                            "window would have invented a hold on an already-legal 64.0 C kettle.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "kettle RTD, 4 kHz, 22 us jitter",
                    "jacket IR camera, 200 Hz, 28 us jitter",
                    "butadiene FT (context)",
                    "alkyl-lithium analyzer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("kettle_trip_C", 82.0),
                        ("observed_kettle_C", 64.0),
                        ("jacket_shadow_C", 89.0),
                        ("proposed_bd_tph", 7.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Kettle-K3 indexed on Diene-Riggs DR-6; butadiene 7.6 t/h armed.",
                    "2. Kettle 64.0 C; jacket-IR smear 89 C over 82 C trip.",
                    "3. PBD-encoder precursor at 0.760 ms.",
                    "4. Race window [4.240, 4.540] ms.",
                    "5. rtd.kettle.C 64.0 C at 4.280 ms (winner).",
                    "6. ir.jacket.C smear at 4.424 ms (loser by 144 us).",
                    "7. Gate at 4.820 ms: ACCEPT leave 7.6 t/h.",
                    "8. Kettle remains 64.0 C < 82 C; glint unused as a hold.",
                    "9. Simulated jacket scale remains the IR source.",
                    "10. Delayed (survey_hold_s=270): 4.5 min Mooney survey after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "bd_7p6"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("bd_tph", 7.6),
                        ("hold", False),
                        ("jacket_C", 58.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("kettle_C", 64.0),
                        ("kettle_trip_C", 82.0),
                        ("jacket_shadow_C", 89.0),
                        ("proposed_bd_tph", 7.6),
                        ("race_margin_us", 144),
                        ("combined_jitter_us", 50),
                        ("survey_hold_s", 270),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 7.6 t/h because kettle 64.0 C is under the 82 C trip; "
                "89 C is a jacket-coil IR smear, not a kettle temperature.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Kettle 64.0 C won by 144 us and sits under the 82 C trip. Jacket smear "
                "89 C is a simulated coil scale, not a kettle reading. ACCEPT: leave 7.6 t/h. "
                "A hold would idle a legal solution-polymer pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "kettle_C",
                            OrderedDict(
                                [
                                    ("trip", 82.0),
                                    ("observed", 64.0),
                                    ("executed_bd_tph", 7.6),
                                ]
                            ),
                        ),
                        (
                            "jacket_shadow_C",
                            OrderedDict(
                                [
                                    ("observed", 89.0),
                                    ("not_a_kettle_reading", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 144),
                                    ("combined_jitter_us", 50),
                                    ("ratio", 2.88),
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
            ("name", "bd_7p6"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("bd_tph", 7.6),
                        ("hold", False),
                        ("jacket_C", 58.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 7.6 t/h. Routing relay.rtd.kettle -> policy.pbd_go. "
                "Jacket-IR unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left K3 at 7.6 t/h. Kettle 64.0 C beat jacket smear 89 C; "
                "the 82 C trip was never crossed. 4.5 min Mooney survey follows "
                "(survey_hold_s=270).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bd", "7.6 t/h held as proposed"),
                        ("kettle", "64.0 C < 82 C trip"),
                        ("glint", "89 C smear unused"),
                        ("survey", "4.5 min Mooney survey queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "IR 89 C was a simulated jacket-coil smear, not a kettle over-trip.",
                    "Delayed (survey_hold_s=270): 4.5 min Mooney survey after the pass on DR-6.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.kettle.C (4.280 ms, 64.0 C)"),
                        ("loser", "ir.jacket.C (4.424 ms, smear 89 C)"),
                        ("margin_us", 144),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 144 us would still be a jacket smear over the "
                            "82 C trip; a correct gate ACCEPTs either way. Reversing would only "
                            "have delayed confirmation of the same legal kettle.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4820),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 4.820 ms (tick 4). The 4.5 min "
                "survey is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 270.0),
            ("survey_hold_s", 270),
        ]
    )
    ras = raster_core(
        26,
        58,
        36,
        54,
        routing(
            "thalamic-relay.kettle-rtd",
            "spikenaut.policy.pbd-go",
            [
                ("relay.rtd.kettle", "policy.pbd_go", 0.71),
                ("relay.ir.jacket", "policy.glint_hold", 0.21),
                ("relay.rtd.kettle", "policy.pbd_go", 0.10),
            ],
            "serotonin",
            0.04,
            "already_legal_stdp; 5-HT at kettle win (4.280 ms) tags the go bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_hold_s", 270),
                ("delayed_surprise_s", 270),
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
                    pop("pbd_go", 36, 0.50, 277.8, 3),
                    pop("ir_hold", 36, 0.80, 9.3, 0),
                    pop("rtd_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r96-499",
        "Diene-Riggs DR-6 / Kettle-K3: kettle 64.0 C beats jacket smear; correct ACCEPT "
        "of an already-legal 7.6 t/h (total +1.10)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Kettle 64.0 C < 82 C trip; jacket smear unused. "
        "total +1.10 = 0.42 + 0.30 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "polybutadiene-solution-kettle",
        ["accept", "simulated-smear", "kettle-vs-glint", "pbd", "simulated"],
        "Teaches that a jacket-coil IR smear can lose to a legal kettle RTD inside a "
        "300 us window; reversing 144 us would have invented a hold on an already-legal PBD kettle.",
        4,
    )


def record_500():
    ticks = [
        tick(1840, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(4920, 0.09, 0.06, 0.04, 0.03, 0.02),
        tick(5092, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(5540, 0.12, 0.09, 0.06, 0.03, 0.02),
        tick(7860, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(420000000, 0.04, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.anolyte.ctx", 0.880, 0.42),
        spike("cell.v", 1.840, 0.59),
        spike("bus.ir.V", 3.260, 0.48),
        spike("cell.v", 4.920, 1.30),
        spike("bus.ir.V", 5.092, 1.11),
        spike("ctrl.gate", 5.540, 0.99),
        spike("cell.v", 7.860, 0.74),
        spike("bus.ir.V", 11.200, 0.56),
        spike("ctrl.gate", 15.000, 0.82),
        spike("ft.anolyte.ctx", 17.400, 0.43),
        spike("cell.v", 20.200, 0.51),
    ]
    excerpt = independent_excerpt(96500, 50, 22000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Cell-C12 at Cobalt-Wyke CW-3 is electrowinning at 16.8 kA with cell 3.38 V "
                "against a 3.90 V anode-effect cap. Bus-bar IR smear sits at 4.22 V over that "
                "cap. Voltage-first should ACCEPT the already-legal 16.8 kA set; smear-first "
                "would only delay confirmation of the same legal sulfate cell.",
            ),
            ("domain", "cobalt-electrowin-cell"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 16.8 kA on C12 while cell stays <= 3.90 V; do not spend a bus-bar IR "
                "smear on the cell hold.",
            ),
            ("t0_us", 1756850400000500),
            ("gate_latency_us", 620),
            ("race_window_us", 340),
            ("race_window_rel_ms", [4.88, 5.22]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "cell.v 3.38 V live",
                                "bus.ir.V 4.22 V smear",
                            ],
                        ),
                        (
                            "semantics",
                            "Voltage-first should ACCEPT 16.8 kA (3.38 V < 3.90 V cap). "
                            "Smear-first would only delay confirmation of the same legal cell.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one cell-voltage slot versus bus-IR group delay on this "
                            "cobalt-EW bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 172 us vs combined jitter ~56 us (cell 24 + bus 32): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 172 us inside the 340 us "
                            "window would still show the live cell under cap; ACCEPT either way.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "cell voltmeter, 2 kHz, 24 us jitter",
                    "bus-bar IR camera, 200 Hz, 32 us jitter",
                    "anolyte FT (context)",
                    "cobalt analyzer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cell_cap_V", 3.90),
                        ("observed_cell_V", 3.38),
                        ("bus_shadow_V", 4.22),
                        ("proposed_kA", 16.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Cell-C12 indexed on Cobalt-Wyke CW-3; sulfate EW 16.8 kA armed.",
                    "2. Cell 3.38 V; bus IR smear 4.22 V over 3.90 V cap.",
                    "3. Anolyte-FT precursor at 0.880 ms.",
                    "4. Race window [4.880, 5.220] ms.",
                    "5. cell.v 3.38 V at 4.920 ms (winner).",
                    "6. bus.ir.V smear at 5.092 ms (loser by 172 us).",
                    "7. Gate at 5.540 ms: ACCEPT leave 16.8 kA.",
                    "8. Cell remains 3.38 V < 3.90 V; smear unused as a hold.",
                    "9. Cobalt sendout continues.",
                    "10. Delayed (dwell_s=420): 7 min cathode-quality dwell after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "ew_16p8"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("current_kA", 16.8),
                        ("hold", False),
                        ("feed_m3h", 4.4),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("cell_V", 3.38),
                        ("cell_cap_V", 3.90),
                        ("bus_shadow_V", 4.22),
                        ("proposed_kA", 16.8),
                        ("race_margin_us", 172),
                        ("combined_jitter_us", 56),
                        ("dwell_s", 420),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 16.8 kA because cell 3.38 V is under the 3.90 V cap "
                "and 4.22 V is a bus-bar IR smear, not a cell voltage.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Cell 3.38 V won by 172 us and sits under the 3.90 V cap. Bus smear "
                "4.22 V is not a cell reading. ACCEPT: leave 16.8 kA. A hold would idle a "
                "legal cobalt electrowin cell.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "cell_V",
                            OrderedDict(
                                [
                                    ("cap", 3.90),
                                    ("observed", 3.38),
                                    ("executed_kA", 16.8),
                                ]
                            ),
                        ),
                        (
                            "bus_shadow_V",
                            OrderedDict(
                                [
                                    ("observed", 4.22),
                                    ("not_a_cell_reading", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 172),
                                    ("combined_jitter_us", 56),
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
            ("name", "ew_16p8"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("current_kA", 16.8),
                        ("hold", False),
                        ("feed_m3h", 4.4),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 16.8 kA. Routing relay.cell.v -> policy.cell_go. "
                "Bus-IR unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left C12 at 16.8 kA. Cell 3.38 V beat bus smear 4.22 V; the "
                "3.90 V cap held. 7 min cathode-quality dwell follows (dwell_s=420).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("cell", "16.8 kA held as proposed"),
                        ("voltage", "3.38 V < 3.90 V cap"),
                        ("smear", "4.22 V unused"),
                        ("survey", "7 min cathode-quality dwell queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Bus IR 4.22 V was never a trip; it only lost the race to a legal cell voltmeter.",
                    "Delayed (dwell_s=420): 7 min cathode-quality dwell after the pass on CW-3.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "cell.v (4.920 ms, 3.38 V)"),
                        ("loser", "bus.ir.V (5.092 ms, smear 4.22 V)"),
                        ("margin_us", 172),
                        (
                            "counterfactual_if_reversed",
                            "Smear-first by < 172 us would still be a bus-bar glint over the "
                            "3.90 V cap; a correct gate ACCEPTs either way. Reversing would only "
                            "have delayed confirmation of the same legal cell.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5540),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 5.540 ms (tick 4). The 7 min "
                "dwell is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 420.0),
            ("dwell_s", 420),
        ]
    )
    ras = raster_core(
        22,
        50,
        42,
        46,
        routing(
            "thalamic-relay.cell-v",
            "spikenaut.policy.cell-go",
            [
                ("relay.cell.v", "policy.cell_go", 0.70),
                ("relay.bus.ir", "policy.bus_hold", 0.23),
                ("relay.cell.v", "policy.cell_go", 0.10),
            ],
            "adenosine",
            0.08,
            "already_legal_stdp; adenosine at cell win (4.920 ms) tags the go bind",
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
            ("decision_window_ms", 0.34),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("cell_go", 32, 0.50, 275.7, 3),
                    pop("bus_hold", 32, 0.80, 9.2, 0),
                    pop("cell_veto", 16, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r96-500",
        "Cobalt-Wyke CW-3 / Cell-C12: 3.38 V beats bus smear 4.22 V; correct ACCEPT "
        "of an already-legal 16.8 kA (total +1.14)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Cell 3.38 V < 3.90 V cap; bus smear unused. "
        "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
        ras,
        gate,
        "cobalt-electrowin-cell",
        ["accept", "designed", "cell-vs-bus", "already-legal", "cobalt-ew"],
        "Teaches an already-legal cobalt electrowin cell: live voltage sits under cap; "
        "bus-bar IR smear only confirms the ACCEPT.",
        5,
    )
