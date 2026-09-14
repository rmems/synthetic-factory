def lif_486_excerpt():
    n = 80
    dt_us = 100
    tau_m_ms = 17.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.89
    i_stim_peak = 2.56
    stim = (21400, 25000)
    seed = 94486
    window_us = 44000
    i_clamp_extra = 0.68
    clamp_n = 16
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
    take(burst, 9, label_times=(22400, 23400, 24400))
    clamp = [(t, nid) for t, nid in picked if t < 21400][:7]
    pack = [(t, nid) for t, nid in picked if t >= 21400][:9]
    picked = sorted(clamp + pack, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(
            f"LIF excerpt too short {len(picked)} (early={len(early)} burst={len(burst)})"
        )
    channels = ["lif.clamp" if t < 21400 else "lif.basket" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 80),
            ("dt_us", 100),
            ("tau_m_ms", 17.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.89),
            ("i_stim_peak", 2.56),
            ("stim_t_us", [21400, 25000]),
            ("i_clamp_extra", 0.68),
            ("clamp_n", 16),
            ("seed", 94486),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-15 carry +0.68 ADN-clamp bias; stim 21.4-25.0 ms is the basket blow.",
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


def record_486():
    excerpt, extra = lif_486_excerpt()
    ticks = [
        tick(2340, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6140, 0.07, -0.04, -0.03, 0.01, -0.01),
        tick(6320, 0.05, -0.03, -0.02, 0.00, 0.00),
        tick(6920, 0.08, -0.06, -0.03, 0.02, -0.01),
        tick(22400, 0.04, -0.38, -0.04, -0.01, -0.02),
        tick(960000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Adiponitrile hydrogenator ADN-H6 at Adnamine-Wray AW-4 is already pushing 12.0 t/h "
                "nitrile into a 178 C wall against a 165 C metal-temperature cap. A wall-first latch "
                "clamps the nitrile; a feed-first story would keep the 12.0 t/h cruise. Stored basket "
                "gasket strain is not yet an observable of either race channel.",
            ),
            ("domain", "hexamethylene-diamine-hydrogenator"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the AW-4 ADN pass, keep hydrogenator wall <= 165 C, and leave the catalyst "
                "basket gasket unmarked.",
            ),
            ("t0_us", 1756850400000486),
            ("gate_latency_us", 780),
            ("race_window_us", 380),
            ("race_window_rel_ms", [6.10, 6.48]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.wall.C 178 C pulse",
                                "ft.adn.tph 12.0 t/h cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Wall-first latches ADN 12.0 -> 6.4 t/h; feed-first keeps "
                            "cruise on a still-cooling basket-gasket model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one 2 kHz wall-RTD sample minus ADN-orifice group "
                            "delay on this hydrogenator bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter ~60 us (wall 26 + ADN 34): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 380 us window "
                            "would have kept 12.0 t/h cruise; predicted next-sample 171 C > 165 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "wall multiplex RTD, 2 kHz, 26 us timestamp jitter",
                    "ADN feed FT, 1 kHz, 34 us jitter",
                    "catalyst-basket AE puck (context until the blow)",
                    "hydrogen purity GC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("wall_cap_C", 165.0),
                        ("observed_wall_C", 178.0),
                        ("proposed_adn_tph", 12.0),
                        ("h2_bar", 28.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. ADN-H6 indexed on Adnamine-Wray AW-4; nitrile armed at 12.0 t/h.",
                    "2. Cruise 12.0 t/h; wall 178 C against 165 C metal-temperature cap.",
                    "3. ADN precursor at 1.120 ms; wall warm-start 178 C.",
                    "4. Race window [6.100, 6.480] ms opens on the hydrogenator bus.",
                    "5. rtd.wall.C 178 C at 6.140 ms (winner).",
                    "6. ft.adn.tph 12.0 t/h at 6.320 ms (loser by 180 us).",
                    "7. Gate at 6.920 ms (winner + 780 us): MODIFY clamp 12.0 -> 6.4 t/h.",
                    "8. Clamp executes; next-sample wall 154 C < 165 cap.",
                    "9. At 22.400 ms stored strain still blows 12 mm of basket gasket; AE burst.",
                    "10. Hydrogenator isolate 16 min (abort_s=960); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_adn_12"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("adn_tph", 12.0),
                        ("h2_bar", 28.4),
                        ("agitator_rpm", 38.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("wall_C", 178.0),
                        ("wall_cap_C", 165.0),
                        ("predicted_unclamped_next_C", 171.0),
                        ("adn_tph", 12.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 960),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 12.0 t/h cruise: 178 C looks like a hydrogen-GC spike, not "
                "basket contact, and ADN-H6 volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Wall 178 C won by 180 us, so the basket is loading heat, not still cooling. "
                "Holding 12.0 t/h predicts next-sample 171 C > 165 cap. MODIFY: ADN 12.0 -> "
                "6.4 t/h. Observed after clamp 154 C < 165. A full REJECT is not indicated: a "
                "sound ADN pass accepts 6.4 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "wall_C",
                            OrderedDict(
                                [
                                    ("cap", 165.0),
                                    ("observed", 178.0),
                                    ("predicted_unclamped_next", 171.0),
                                    ("clamped_adn_tph", 6.4),
                                    ("observed_after_clamp", 154.0),
                                ]
                            ),
                        ),
                        (
                            "adn_tph",
                            OrderedDict([("proposed", 12.0), ("clamped", 6.4)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 3.00),
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
            ("name", "clamped_adn_6p4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("adn_tph", 6.4),
                        ("h2_bar", 28.4),
                        ("agitator_rpm", 38.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: ADN 12.0 -> 6.4 t/h. Process-correct vs the 165 C wall "
                "cap. Basket-gasket blow still occurs at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held wall at 154 C. At 22.400 ms stored strain "
                "in the catalyst-basket gasket still blew a 12 mm face. Clamp reduced dump energy; "
                "it did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("adn", "clamp executed; peak 154 C < 165"),
                        ("gasket", "12 mm blow at 22.400 ms"),
                        ("repair", "16 min hydrogenator isolate (abort_s=960)"),
                        ("mission", "AW-4 ADN pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither wall RTD nor ADN FT predicted the gasket charge; ae.basket.blow is a new channel at 22.400 ms, 15.480 ms after the gate, still inside the 44 ms raster.",
                    "Delayed (abort_s=960): 16 min hydrogenator isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "16 min hydrogenator isolate after a 12 mm basket-gasket blow. Safety head -0.58 "
                "prices the split; task_progress stays +0.30 because the ADN clamp completed "
                "under the 165 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.wall.C (6.140 ms, 178 C)"),
                        ("loser", "ft.adn.tph (6.320 ms, 12.0 t/h)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Feed-first by < 180 us inside the 380 us window would have kept "
                            "12.0 t/h cruise; predicted next-sample 171 C would have exceeded "
                            "the 165 cap even without the gasket charge. The MODIFY is still the "
                            "correct process. The blow is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms basket-gasket blow (tick t_us=22400), inside "
                "the 44 ms raster. The correct MODIFY at 6.920 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=960 isolate tick.",
            ),
            ("delayed_surprise_s", 960.0),
            ("abort_s", 960),
        ]
    )
    spikes = [
        spike("enc.adn.ctx", 1.120, 0.42),
        spike("rtd.wall.C", 2.340, 0.61),
        spike("ft.adn.tph", 3.580, 0.50),
        spike("rtd.wall.C", 6.140, 1.32),
        spike("ft.adn.tph", 6.320, 1.14),
        spike("ctrl.gate", 6.920, 0.98),
        spike("rtd.wall.C", 8.460, 0.80),
        spike("ft.adn.tph", 11.100, 0.62),
        spike("ctrl.gate", 15.400, 0.84),
        spike("ae.basket.blow", 22.400, 1.46),
        spike("ae.basket.blow", 24.300, 0.91),
        spike("enc.adn.ctx", 31.600, 0.41),
        spike("rtd.wall.C", 40.200, 0.53),
    ]
    ras = raster_core(
        44,
        80,
        25,
        88,
        routing(
            "thalamic-relay.wall-basket",
            "spikenaut.policy.adn-clamp",
            [
                ("relay.rtd.wall", "policy.adn_clamp", 0.66),
                ("relay.ft.adn", "policy.adn_hold", 0.30),
                ("relay.ae.basket", "policy.adn_clamp", -0.45),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at wall win (6.140 ms) opens a 50 ms "
            "eligibility trace that still covers the 22.400 ms basket blow",
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
                    pop("adn_clamp", 42, 0.50, 250.0, 4),
                    pop("adn_hold", 42, 0.50, 62.5, 1),
                    pop("wall_veto", 22, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r94-486",
        "Adnamine-Wray AW-4 / ADN-H6: wall 178 C beats ADN feed by 180 us; correct "
        "MODIFY still eats an in-window basket-gasket blow (partnered negative total -0.45)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "44 ms raster. total -0.45 = 0.30 + -0.58 + -0.16 + 0.04 + -0.05. Named hydrogenator "
        "isolate (abort_s=960) is not netted into task_progress.",
        ras,
        gate,
        "hexamethylene-diamine-hydrogenator",
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
        "16 min hydrogenator isolate.",
        1,
    )


def record_487():
    ticks = [
        tick(1880, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(4420, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(4580, -0.03, -0.01, -0.03, -0.02, 0.01),
        tick(5060, -0.07, -0.05, -0.08, -0.05, 0.02),
        tick(7280, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(1140000000, -0.02, -0.01, -0.04, -0.01, 0.00),
    ]
    spikes = [
        spike("ft.butanol.ctx", 0.880, 0.40),
        spike("live.tc.C", 1.880, 0.58),
        spike("leftover.k.C", 2.640, 0.51),
        spike("live.tc.C", 4.420, 1.32),
        spike("leftover.k.C", 4.580, 1.15),
        spike("ctrl.gate", 5.060, 1.00),
        spike("live.tc.C", 7.280, 0.74),
        spike("leftover.k.C", 8.440, 0.61),
        spike("ctrl.gate", 12.200, 0.82),
        spike("ft.butanol.ctx", 16.800, 0.42),
        spike("live.tc.C", 21.600, 0.53),
        spike("leftover.k.C", 26.200, 0.47),
    ]
    excerpt = independent_excerpt(94487, 92, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Brass-catalyst bed MEK-B2 on Mekone-Howe MH-3 keeps 2-butanol at 11.0 t/h with a "
                "live Type-J reading of 384 C against a 520 C trip. A leftover Type-K millivolt "
                "table plus a stale ice-point cold-junction offset from last campaign still sit in "
                "the transmitter. Live-J-first should ACCEPT the feed; a weak supervisor that binds "
                "the Type-K table will REJECT a legal dehydrogenation bed.",
            ),
            ("domain", "mek-dehydrogenation-bed"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep 11.0 t/h 2-butanol on MEK-B2 while live Type-J stays <= 520 C; "
                "do not spend a leftover Type-K table or a 0 C ice-point CJ on the hold.",
            ),
            ("t0_us", 1756850400000487),
            ("gate_latency_us", 640),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.40, 4.72]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "live.tc.C 384 C Type J on 21.10 mV",
                                "leftover.k.C 538 C Type K + stale ice-point CJ",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-J-first should ACCEPT 11.0 t/h (384 C < 520 C trip). "
                            "Leftover-K-first tempts a weak supervisor to treat 538 C as live.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one MEK-B2 Type-J sample minus leftover-K transmitter group delay "
                            "on this brass-bed bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter ~54 us (live 24 + leftover 30): 3.0x over "
                            "a 2.0x trust floor. Order is correctly live-J-first. The error is binding "
                            "the leftover Type-K table plus ice-point CJ, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "MEK-B2 bed Type-J, 4 kHz, 24 us jitter, published Type J LIVE",
                    "leftover Type-K millivolt table, 4 kHz, 30 us jitter, STALE",
                    "2-butanol FT (context)",
                    "hydrogen offgas GC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("trip_C", 520.0),
                        ("live_C", 384.0),
                        ("published_tc_type", "J"),
                        ("bound_tc_type", "K"),
                        ("live_mV", 21.10),
                        ("type_k_C", 510.0),
                        ("cj_offset_C", 28.0),
                        ("bound_C", 538.0),
                        ("proposed_feed_tph", 11.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. MEK-B2 latched on Mekone-Howe MH-3; 2-butanol 11.0 t/h armed.",
                    "2. Live 21.10 mV Type J = 384 C; leftover Type-K table scales 510 C plus 28 C ice-point CJ = 538 C.",
                    "3. 2-butanol-FT precursor at 0.880 ms.",
                    "4. Race window [4.400, 4.720] ms.",
                    "5. live.tc.C 384 C at 4.420 ms (winner).",
                    "6. leftover.k.C 538 C at 4.580 ms (loser by 160 us).",
                    "7. Gate at 5.060 ms: REJECT hold 0.0 t/h (incorrect).",
                    "8. Legal 2-butanol cancelled; live 384 C still < 520 C trip.",
                    "9. Type-K bind remains; ice-point CJ 0 C unused as a live trip.",
                    "10. Delayed missed_window_s=1140 (19 min MEK-quality window) while B2 waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "feed_11"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 11.0),
                        ("hold", False),
                        ("bound_tc_type", "J"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 384.0),
                        ("trip_C", 520.0),
                        ("published_tc_type", "J"),
                        ("bound_tc_type", "J"),
                        ("live_mV", 21.10),
                        ("type_k_C", 510.0),
                        ("cj_offset_C", 28.0),
                        ("bound_C", 538.0),
                        ("tc_type_swap", False),
                        ("cj_offset_stale", False),
                        ("pv_live", True),
                        ("proposed_feed_tph", 11.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 54),
                        ("missed_window_s", 1140),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 11.0 t/h feed because live 21.10 mV on the published Type-J "
                "table is 384 C under the 520 C trip; 538 C is a leftover Type-K table plus ice-point "
                "CJ, not the live EU.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Leftover Type-K millivolt table scales 21.10 mV to 510 C, then a stale ice-point "
                "CJ adds 28 C to 538 C, over the 520 C trip once the supervisor treats that table as "
                "live. REJECT: hold 2-butanol 0.0 t/h until the tag recovers under 520 so the bed "
                "does not see a hot-spot event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "mek_C",
                            OrderedDict(
                                [
                                    ("published_live_trip", 520.0),
                                    ("observed_live", 384.0),
                                    ("misbound_tc_type", "K"),
                                    ("type_k_C", 510.0),
                                    ("cj_offset_C", 28.0),
                                    ("bound_C", 538.0),
                                    ("live_mV", 21.10),
                                    ("tc_type_swap", True),
                                    ("cj_offset_stale", True),
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
                        ("bound_tc_type", "K"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): feed 11.0 -> 0.0 t/h. Routing relay.tc.typek -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live 384 C never "
                "violated the 520 C trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze MEK-B2 at 0.0 t/h while live Type-J stayed 384 C under the "
                "520 C trip. 19 min MEK-quality window missed. Correct gate was ACCEPT of "
                "the already-legal 11.0 t/h feed.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held at 0.0 t/h; 11.0 t/h abandoned"),
                        ("live_C", "still 384 C, under 520 C published trip"),
                        ("loop", "19 min MEK-quality window missed"),
                        ("tc", "538 C leftover Type-K + ice-point CJ false positive, not a live over-trip"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 538 C reading is a leftover Type-K millivolt table (510 C) plus a stale 28 C ice-point CJ, not a published live over-trip.",
                    "Delayed (missed_window_s=1140): sister MEK-B3 ran the same 11.0 t/h quality window after QA rebound the Type-J map; B2's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live 384 C < published 520 C trip; leave 11.0 t/h; bind Type J and the 28 C terminal CJ.",
                        ),
                        ("correct_trip_C", 520.0),
                        ("wrong_bound_C", 538.0),
                        ("bound_tc_should_be", "J"),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [("feed_tph", 0.0), ("hold", True), ("bound_tc_type", "K")]
                            ),
                        ),
                        (
                            "cost",
                            "19 min missed MEK-quality window (task/efficiency); live bed never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "live.tc.C (4.420 ms, 384 C Type J on 21.10 mV)"),
                        ("loser", "leftover.k.C (4.580 ms, 538 C Type K + ice-point CJ)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Leftover-K-first by < 160 us would still show live 384 C < 520 C. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the live-J "
                            "win on a leftover Type-K table plus a stale ice-point CJ.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5060),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (5.060 ms, tick 4). The 19 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 1140.0),
            ("missed_window_s", 1140),
        ]
    )
    ras = raster_core(
        28,
        92,
        32,
        82,
        routing(
            "relay.tc.typek",
            "policy.hold_reject",
            [
                ("relay.tc.typek", "policy.hold_reject", 0.75),
                ("relay.live.tc", "policy.hold_reject", 0.18),
            ],
            "acetylcholine",
            0.06,
            "tc_type_swap_stdp; ACh tags the (wrong) hold_reject bind at the leftover-K shadow",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("missed_window_s", 1140),
                ("delayed_surprise_s", 1140),
                ("tc_type_swap", True),
                ("cj_offset_stale", True),
                ("live_C", 384.0),
                ("bound_C", 538.0),
                ("bound_tc_type", "K"),
                ("published_tc_type", "J"),
                ("cj_offset_C", 28.0),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 50, 0.50, 250.0, 4),
                    pop("go_accept", 50, 0.80, 6.25, 0),
                    pop("tc_ctx", 30, 0.55, 104.2, 1),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r94-487",
        "WRONG-REJECT at Mekone-Howe MH-3 / MEK-B2: live Type-J 384 C < 520 C trip; "
        "supervisor bound leftover Type-K table (510 C) plus stale 28 C ice-point CJ (538 C)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 384 < 520 on live Type J is true; clamp bound "
        "to a 538 C leftover Type-K + ice-point CJ. total -0.60 = -0.20 + -0.11 + -0.23 + -0.12 + 0.06.",
        ras,
        gate,
        "mek-dehydrogenation-bed",
        [
            "reject",
            "wrong-gate",
            "tc-type-swap",
            "cold-junction-offset",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed on a leftover TC type.",
        2,
        supervisor_error_type="wrong-reject",
    )


def record_488():
    ticks = [
        tick(2180, 0.01, 0.06, 0.01, 0.01, 0.01),
        tick(5240, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5412, 0.02, 0.07, 0.02, 0.02, 0.01),
        tick(6080, 0.03, 0.12, 0.04, 0.03, 0.02),
        tick(8120, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(600000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("ir.shell.ctx", 1.040, 0.43),
        spike("ae.shell.pps", 2.180, 0.62),
        spike("ir.shell.C", 3.520, 0.49),
        spike("ae.shell.pps", 5.240, 1.35),
        spike("ir.shell.C", 5.412, 1.12),
        spike("ctrl.gate", 6.080, 1.03),
        spike("ae.shell.pps", 8.120, 0.77),
        spike("ir.shell.ctx", 12.400, 0.44),
        spike("ir.shell.C", 16.800, 0.58),
        spike("ctrl.gate", 21.600, 0.81),
        spike("ae.shell.pps", 27.200, 0.50),
        spike("ir.shell.C", 32.400, 0.46),
        spike("ae.shell.ctx", 35.600, 0.40),
    ]
    excerpt = independent_excerpt(94488, 110, 36000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Kroll retort KR-2 on Zirconia-Yair ZY-HIL is staged for a 6.8 t/d magnesium charge "
                "while shell AE sits at 52 pps against a 16 pps crack floor. A shell pyrometer, lit "
                "by the pad lamp spectrum, still reports 742 C under an 860 C wall cap. AE-first "
                "holds the Mg charge; IR-first would commit 6.8 t/d into a cracked retort.",
            ),
            ("domain", "zirconium-kroll-retort"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Run KR-2 only if shell AE stays <= 16 pps; otherwise hold so a cracked retort is "
                "not loaded at 6.8 t/d.",
            ),
            ("t0_us", 1756850400000488),
            ("gate_latency_us", 840),
            ("race_window_us", 440),
            ("race_window_rel_ms", [5.20, 5.64]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.shell.pps 52 pps retort crack",
                                "ir.shell.C 742 C pad-lamp glint",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches retort hold 6.8 -> 0 t/d; IR-first would commit "
                            "6.8 t/d on a still-legal 742 C wall-cap story.",
                        ),
                        (
                            "window_derivation",
                            "440 us = one shell-AE slot versus shell-IR decode on this HIL Kroll bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 172 us vs combined jitter ~62 us (AE 28 + IR 34): 2.8x over "
                            "a 2.0x trust floor. Reversing order by < 172 us inside the 440 us "
                            "window would have committed 6.8 t/d into a 52 pps retort crack.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "retort-shell AE puck, 5 kHz, 28 us jitter",
                    "shell IR camera, 200 Hz, 34 us jitter",
                    "magnesium charge encoder (context)",
                    "argon header PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_crack_floor_pps", 16.0),
                        ("observed_ae_pps", 52.0),
                        ("wall_cap_C", 860.0),
                        ("observed_wall_C", 742.0),
                        ("proposed_mg_td", 6.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. KR-2 indexed on Zirconia-Yair ZY-HIL; Mg 6.8 t/d armed.",
                    "2. Shell IR 742 C under 860 C cap; AE already 52 pps.",
                    "3. IR-context precursor at 1.040 ms.",
                    "4. Race window [5.200, 5.640] ms.",
                    "5. ae.shell.pps 52 pps at 5.240 ms (winner).",
                    "6. ir.shell.C 742 C at 5.412 ms (loser by 172 us).",
                    "7. Gate at 6.080 ms: REJECT hold retort 0 t/d.",
                    "8. Pass cancelled; crack not loaded.",
                    "9. HIL pad lamp spectrum remains the shell glint source.",
                    "10. Delayed (abort_s=600): 10 min retort re-seat before the next charge.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "kroll_6p8"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("mg_td", 6.8),
                        ("hold", False),
                        ("retort", "KR-2"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 52.0),
                        ("ae_crack_floor_pps", 16.0),
                        ("wall_C", 742.0),
                        ("wall_cap_C", 860.0),
                        ("race_margin_us", 172),
                        ("combined_jitter_us", 62),
                        ("abort_s", 600),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 6.8 t/d because shell 742 C is under the 860 C "
                "cap and treats the AE puck as argon-header noise.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Shell AE 52 pps won by 172 us, so the retort is cracking, not still quiet. "
                "52 pps > 16 pps floor. REJECT: hold Mg 6.8 -> 0 t/d. Wall 742 C < 860 C "
                "does not license the charge once AE is over floor.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "shell_ae_pps",
                            OrderedDict(
                                [
                                    ("floor", 16.0),
                                    ("observed", 52.0),
                                    ("executed_mg_td", 0.0),
                                ]
                            ),
                        ),
                        (
                            "wall_C",
                            OrderedDict(
                                [
                                    ("cap", 860.0),
                                    ("observed", 742.0),
                                    ("does_not_license_charge", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 172),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 2.77),
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
            ("name", "retort_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("mg_td", 0.0),
                        ("hold", True),
                        ("retort", "KR-2"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (correct): Mg 6.8 -> 0 t/d. Routing relay.ae.shell -> "
                "policy.retort_hold. Crack is not loaded.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held KR-2 at 0 t/d. AE 52 pps beat shell 742 C; retort "
                "was already over the 16 pps crack floor. 10 min re-seat follows (abort_s=600).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("retort", "held at 0 t/d; 6.8 t/d abandoned"),
                        ("shell", "52 pps crack not loaded"),
                        ("wall", "742 C still under 860 C cap"),
                        ("reseat", "10 min retort re-seat queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Shell IR 742 C was a HIL pad-lamp glint, not a wall-cap exceedance.",
                    "Delayed (abort_s=600): 10 min retort re-seat before the next charge on ZY-HIL.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.shell.pps (5.240 ms, 52 pps)"),
                        ("loser", "ir.shell.C (5.412 ms, 742 C)"),
                        ("margin_us", 172),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 172 us would have committed 6.8 t/d into a retort "
                            "already at 52 pps. The REJECT is still the correct process; AE is the "
                            "licensing channel, not shell IR.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6080),
            (
                "reward_inflection_note",
                "Safety and task credit the correct REJECT at 6.080 ms (tick 4). The 10 min "
                "re-seat is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 600.0),
            ("abort_s", 600),
        ]
    )
    ras = raster_core(
        36,
        110,
        22,
        87,
        routing(
            "thalamic-relay.shell-ae",
            "spikenaut.policy.retort-hold",
            [
                ("relay.ae.shell", "policy.retort_hold", 0.68),
                ("relay.ir.shell", "policy.retort_commit", 0.28),
                ("relay.ae.shell", "policy.retort_hold", 0.12),
            ],
            "dopamine",
            0.07,
            "ae_floor_stdp; DA at shell win (5.240 ms) opens a 70 ms eligibility trace",
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
            ("decision_window_ms", 0.44),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("retort_hold", 54, 0.50, 210.0, 5),
                    pop("retort_commit", 54, 0.50, 42.1, 1),
                    pop("ae_veto", 30, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r94-488",
        "Zirconia-Yair ZY-HIL / KR-2: shell AE 52 pps beats wall 742 C; correct "
        "REJECT holds the Kroll magnesium charge",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 52 pps > 16 pps floor beats a legal shell IR. "
        "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "zirconium-kroll-retort",
        ["reject", "hil", "shell-ae", "kroll", "correct-gate"],
        "Teaches a shell-AE vs pad-lamp-glint race on a HIL Kroll retort: the crack floor, "
        "not the wall cap, licenses the charge.",
        3,
    )


def record_489():
    ticks = [
        tick(1600, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(4020, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(4176, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(4560, 0.12, 0.09, 0.05, 0.03, 0.02),
        tick(6420, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(240000000, 0.03, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.lab.ctx", 0.780, 0.41),
        spike("rtd.jacket.C", 1.600, 0.58),
        spike("ir.vapor.C", 2.720, 0.47),
        spike("rtd.jacket.C", 4.020, 1.28),
        spike("ir.vapor.C", 4.176, 1.10),
        spike("ctrl.gate", 4.560, 0.97),
        spike("rtd.jacket.C", 6.420, 0.72),
        spike("enc.lab.ctx", 10.200, 0.44),
        spike("ir.vapor.C", 14.400, 0.55),
        spike("ctrl.gate", 18.600, 0.80),
        spike("rtd.jacket.C", 22.000, 0.49),
        spike("enc.lab.ctx", 25.200, 0.38),
    ]
    excerpt = independent_excerpt(94489, 58, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "HF contactor HF-C1 of Alkylate-Naze AN-5 already shows jacket 8.4 C while a "
                "vapor-space IR smear still prints 42 C against a 24 C acid-cap the live RTD "
                "has not crossed. Jacket-first should ACCEPT 9.2 t/h LAB; glint-first would "
                "invent a hold on an already-legal alkylation pass.",
            ),
            ("domain", "linear-alkylbenzene-hf-alkylation"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Run C1 at 9.2 t/h while jacket stays <= 24 C; do not spend a vapor-space "
                "IR smear on the HF hold.",
            ),
            ("t0_us", 1756850400000489),
            ("gate_latency_us", 540),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.00, 4.32]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.jacket.C 8.4 C live",
                                "ir.vapor.C smear as 42 C",
                            ],
                        ),
                        (
                            "semantics",
                            "Jacket-first should ACCEPT 9.2 t/h (8.4 C < 24 C acid-cap). "
                            "Glint-first would hold on a simulated vapor smear.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one jacket-RTD sample versus vapor-IR decode on this "
                            "HF-alkylation bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 156 us vs combined jitter ~52 us (RTD 22 + IR 30): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 156 us inside the 320 us "
                            "window would have invented a hold on an already-legal 8.4 C jacket.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "jacket RTD, 4 kHz, 22 us jitter",
                    "vapor IR camera, 200 Hz, 30 us jitter",
                    "LAB olefin FT (context)",
                    "HF inventory load cell (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("jacket_cap_C", 24.0),
                        ("observed_jacket_C", 8.4),
                        ("vapor_shadow_C", 42.0),
                        ("proposed_lab_tph", 9.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. HF-C1 indexed on Alkylate-Naze AN-5; LAB 9.2 t/h armed.",
                    "2. Jacket 8.4 C; vapor-IR smear as 42 C over 24 C acid-cap.",
                    "3. LAB-encoder precursor at 0.780 ms.",
                    "4. Race window [4.000, 4.320] ms.",
                    "5. rtd.jacket.C 8.4 C at 4.020 ms (winner).",
                    "6. ir.vapor.C smear at 4.176 ms (loser by 156 us).",
                    "7. Gate at 4.560 ms: ACCEPT leave 9.2 t/h.",
                    "8. Jacket remains 8.4 C < 24 C; glint unused as a hold.",
                    "9. Simulated vapor scale remains the IR source.",
                    "10. Delayed (survey_hold_s=240): 4 min bromine-index survey after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "lab_9p2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("lab_tph", 9.2),
                        ("hold", False),
                        ("jacket_C", 8.4),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("jacket_C", 8.4),
                        ("jacket_cap_C", 24.0),
                        ("vapor_shadow_C", 42.0),
                        ("proposed_lab_tph", 9.2),
                        ("race_margin_us", 156),
                        ("combined_jitter_us", 52),
                        ("survey_hold_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 9.2 t/h because jacket 8.4 C is under the 24 C acid-cap; "
                "42 C is a vapor-space IR smear, not a jacket temperature.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Jacket 8.4 C won by 156 us and sits under the 24 C acid-cap. Vapor smear "
                "42 C is a simulated headspace scale, not a jacket reading. ACCEPT: leave 9.2 t/h. "
                "A hold would idle a legal HF alkylation pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "jacket_C",
                            OrderedDict(
                                [
                                    ("cap", 24.0),
                                    ("observed", 8.4),
                                    ("executed_lab_tph", 9.2),
                                ]
                            ),
                        ),
                        (
                            "vapor_shadow_C",
                            OrderedDict(
                                [
                                    ("observed", 42.0),
                                    ("not_a_jacket_reading", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 156),
                                    ("combined_jitter_us", 52),
                                    ("ratio", 3.00),
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
            ("name", "lab_9p2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("lab_tph", 9.2),
                        ("hold", False),
                        ("jacket_C", 8.4),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 9.2 t/h. Routing relay.rtd.jacket -> policy.lab_go. "
                "Vapor-IR unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left C1 at 9.2 t/h. Jacket 8.4 C beat vapor smear 42 C; "
                "the 24 C acid-cap was never crossed. 4 min bromine-index survey follows "
                "(survey_hold_s=240).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("lab", "9.2 t/h held as proposed"),
                        ("jacket", "8.4 C < 24 C acid-cap"),
                        ("glint", "42 C smear unused"),
                        ("survey", "4 min bromine-index survey queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "IR 42 C was a simulated vapor-space smear, not a jacket over-cap.",
                    "Delayed (survey_hold_s=240): 4 min bromine-index survey after the pass on AN-5.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.jacket.C (4.020 ms, 8.4 C)"),
                        ("loser", "ir.vapor.C (4.176 ms, smear 42 C)"),
                        ("margin_us", 156),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 156 us would still be a vapor smear over the "
                            "24 C acid-cap; a correct gate ACCEPTs either way. Reversing would only "
                            "have delayed confirmation of the same legal jacket.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4560),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 4.560 ms (tick 4). The 4 min "
                "survey is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 240.0),
            ("survey_hold_s", 240),
        ]
    )
    ras = raster_core(
        26,
        58,
        36,
        54,
        routing(
            "thalamic-relay.jacket-rtd",
            "spikenaut.policy.lab-go",
            [
                ("relay.rtd.jacket", "policy.lab_go", 0.70),
                ("relay.ir.vapor", "policy.glint_hold", 0.22),
                ("relay.rtd.jacket", "policy.lab_go", 0.10),
            ],
            "serotonin",
            0.04,
            "already_legal_stdp; 5-HT at jacket win (4.020 ms) tags the go bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_hold_s", 240),
                ("delayed_surprise_s", 240),
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
                    pop("lab_go", 38, 0.50, 246.7, 3),
                    pop("glint_hold", 38, 0.80, 8.2, 0),
                    pop("rtd_veto", 22, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r94-489",
        "Alkylate-Naze AN-5 / HF-C1: jacket 8.4 C beats vapor smear; correct ACCEPT "
        "of an already-legal 9.2 t/h (total +1.10)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Jacket 8.4 C < 24 C acid-cap; vapor smear unused. "
        "total +1.10 = 0.42 + 0.30 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "linear-alkylbenzene-hf-alkylation",
        ["accept", "simulated-smear", "jacket-vs-glint", "lab-hf", "simulated"],
        "Teaches that a vapor-space IR smear can lose to a legal jacket RTD inside a "
        "320 us window; reversing 156 us would have invented a hold on an already-legal HF alkylation.",
        4,
    )


def record_490():
    ticks = [
        tick(1820, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(5420, 0.09, 0.06, 0.04, 0.03, 0.02),
        tick(5584, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(6000, 0.12, 0.09, 0.06, 0.03, 0.02),
        tick(7860, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(420000000, 0.04, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.lactide.ctx", 0.920, 0.42),
        spike("rtd.melt.C", 1.820, 0.59),
        spike("ir.vapor.C", 3.040, 0.48),
        spike("rtd.melt.C", 5.420, 1.30),
        spike("ir.vapor.C", 5.584, 1.12),
        spike("ctrl.gate", 6.000, 0.99),
        spike("rtd.melt.C", 7.860, 0.73),
        spike("ft.lactide.ctx", 11.400, 0.44),
        spike("ir.vapor.C", 15.200, 0.54),
        spike("ctrl.gate", 18.400, 0.81),
        spike("rtd.melt.C", 21.200, 0.50),
    ]
    excerpt = independent_excerpt(94490, 50, 22000, 11, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Ring-opening kettle ROP-K3 at Polylact-Eyot PE-6 sits at 186 C melt while a vapor "
                "IR glint still reports 228 C against a 210 C jacket cap the live melt RTD has not "
                "crossed. Melt-first should ACCEPT 4.8 t/h lactide; glint-first would invent a hold "
                "on an already-legal ROP pass.",
            ),
            ("domain", "lactide-ring-opening"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run K3 at 4.8 t/h while melt stays <= 210 C; do not spend a vapor IR glint "
                "on the ROP hold.",
            ),
            ("t0_us", 1756850400000490),
            ("gate_latency_us", 580),
            ("race_window_us", 340),
            ("race_window_rel_ms", [5.40, 5.74]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.melt.C 186 C live",
                                "ir.vapor.C glint as 228 C",
                            ],
                        ),
                        (
                            "semantics",
                            "Melt-first should ACCEPT 4.8 t/h (186 C < 210 C jacket cap). "
                            "Glint-first would hold on a vapor IR glint.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one melt-RTD sample versus vapor-IR decode on this "
                            "ROP kettle bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 164 us vs combined jitter ~56 us (RTD 24 + IR 32): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 164 us inside the 340 us "
                            "window would have invented a hold on an already-legal 186 C melt.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "melt RTD, 4 kHz, 24 us jitter",
                    "vapor IR camera, 200 Hz, 32 us jitter",
                    "lactide FT (context)",
                    "tin-octoate pump encoder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("melt_cap_C", 210.0),
                        ("observed_melt_C", 186.0),
                        ("vapor_glint_C", 228.0),
                        ("proposed_lactide_tph", 4.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. ROP-K3 indexed on Polylact-Eyot PE-6; lactide 4.8 t/h armed.",
                    "2. Melt 186 C; vapor-IR glint as 228 C over 210 C jacket cap.",
                    "3. Lactide-FT precursor at 0.920 ms.",
                    "4. Race window [5.400, 5.740] ms.",
                    "5. rtd.melt.C 186 C at 5.420 ms (winner).",
                    "6. ir.vapor.C glint at 5.584 ms (loser by 164 us).",
                    "7. Gate at 6.000 ms: ACCEPT leave 4.8 t/h.",
                    "8. Melt remains 186 C < 210 C; glint unused as a hold.",
                    "9. Condensate film remains the IR source.",
                    "10. Delayed (dwell_s=420): 7 min Mw dwell after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "lactide_4p8"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("lactide_tph", 4.8),
                        ("hold", False),
                        ("jacket_C", 192.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("melt_C", 186.0),
                        ("melt_cap_C", 210.0),
                        ("vapor_glint_C", 228.0),
                        ("proposed_lactide_tph", 4.8),
                        ("race_margin_us", 164),
                        ("combined_jitter_us", 56),
                        ("dwell_s", 420),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.8 t/h because melt 186 C is under the 210 C jacket cap; "
                "228 C is a vapor IR glint, not a melt temperature.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Melt 186 C won by 164 us and sits under the 210 C jacket cap. Vapor glint "
                "228 C is condensate film, not a melt reading. ACCEPT: leave 4.8 t/h. "
                "A hold would idle a legal ROP pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "melt_C",
                            OrderedDict(
                                [
                                    ("cap", 210.0),
                                    ("observed", 186.0),
                                    ("executed_lactide_tph", 4.8),
                                ]
                            ),
                        ),
                        (
                            "vapor_glint_C",
                            OrderedDict(
                                [
                                    ("observed", 228.0),
                                    ("not_a_melt_reading", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 164),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 2.93),
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
            ("name", "lactide_4p8"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("lactide_tph", 4.8),
                        ("hold", False),
                        ("jacket_C", 192.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 4.8 t/h. Routing relay.rtd.melt -> policy.rop_go. "
                "Vapor-IR unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left K3 at 4.8 t/h. Melt 186 C beat vapor glint 228 C; "
                "the 210 C jacket cap was never crossed. 7 min Mw dwell follows "
                "(dwell_s=420).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("lactide", "4.8 t/h held as proposed"),
                        ("melt", "186 C < 210 C jacket cap"),
                        ("glint", "228 C unused"),
                        ("dwell", "7 min Mw dwell queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "IR 228 C was condensate-film glint, not a melt over-cap.",
                    "Delayed (dwell_s=420): 7 min Mw dwell after the pass on PE-6.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.melt.C (5.420 ms, 186 C)"),
                        ("loser", "ir.vapor.C (5.584 ms, glint 228 C)"),
                        ("margin_us", 164),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 164 us would still be condensate film over the "
                            "210 C jacket cap; a correct gate ACCEPTs either way. Reversing would only "
                            "have delayed confirmation of the same legal melt.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6000),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 6.000 ms (tick 4). The 7 min "
                "dwell is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 420.0),
            ("dwell_s", 420),
        ]
    )
    ras = raster_core(
        22,
        50,
        40,
        44,
        routing(
            "thalamic-relay.melt-rtd",
            "spikenaut.policy.rop-go",
            [
                ("relay.rtd.melt", "policy.rop_go", 0.72),
                ("relay.ir.vapor", "policy.glint_hold", 0.20),
                ("relay.rtd.melt", "policy.rop_go", 0.10),
            ],
            "adenosine",
            0.045,
            "already_legal_stdp; adenosine at melt win (5.420 ms) tags the go bind",
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
                    pop("rop_go", 36, 0.50, 245.1, 3),
                    pop("glint_hold", 36, 0.80, 8.2, 0),
                    pop("melt_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r94-490",
        "Polylact-Eyot PE-6 / ROP-K3: melt 186 C beats vapor glint; correct ACCEPT "
        "of an already-legal 4.8 t/h (total +1.14)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Melt 186 C < 210 C jacket cap; vapor glint unused. "
        "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
        ras,
        gate,
        "lactide-ring-opening",
        ["accept", "designed", "melt-vs-glint", "rop", "already-legal"],
        "Teaches that a vapor IR glint can lose to a legal melt RTD inside a "
        "340 us window; reversing 164 us would have invented a hold on an already-legal ROP kettle.",
        5,
    )

