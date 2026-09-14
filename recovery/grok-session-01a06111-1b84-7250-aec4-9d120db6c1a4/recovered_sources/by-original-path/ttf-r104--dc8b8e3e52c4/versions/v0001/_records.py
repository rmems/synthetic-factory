def lif_536_excerpt():
    n = 80
    dt_us = 100
    tau_m_ms = 17.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.89
    i_stim_peak = 2.56
    stim = (22000, 25600)
    seed = 104536
    window_us = 46000
    i_clamp_extra = 0.70
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
    early = [(t, nid) for t, nid in spikes if t < 22000]
    burst = [(t, nid) for t, nid in spikes if 22000 <= t < 25600]
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
            group = [1 for tt, _ in picked if (tt < 22000) == (pool[0][0] < 22000)]
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
    clamp = [(t, nid) for t, nid in picked if t < 22000][:7]
    pack = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + pack, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(
            f"LIF excerpt too short {len(picked)} (early={len(early)} burst={len(burst)})"
        )
    channels = ["lif.clamp" if t < 22000 else "lif.pack" for t, _ in picked]
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
            ("stim_t_us", [22000, 25600]),
            ("i_clamp_extra", 0.70),
            ("clamp_n", 16),
            ("seed", 104536),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-15 carry +0.70 SOCl2-clamp bias; stim 22.0-25.6 ms is the packing collapse.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 900),
            ("delayed_surprise_s", 900),
        ]
    )
    return excerpt_items(picked, channels), extra


def record_536():
    excerpt, extra = lif_536_excerpt()
    ticks = [
        tick(2480, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6220, 0.07, -0.04, -0.03, 0.01, -0.01),
        tick(6400, 0.05, -0.03, -0.02, 0.00, 0.00),
        tick(7040, 0.08, -0.06, -0.03, 0.02, -0.01),
        tick(23200, 0.06, -0.40, -0.04, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Thionyl-chloride still SOCL-C4 at Thionyl-Scroggs TS-2 is already pushing 9.2 t/h "
                "distillate into a 172 C reboiler wall against a 160 C metal-temperature cap. A "
                "wall-first latch clamps the SOCl2; a feed-first story would keep the 9.2 t/h cruise. "
                "Stored packing strain is not yet an observable of either race channel.",
            ),
            ("domain", "thionyl-chloride-still"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the TS-2 SOCl2 cut, keep reboiler wall <= 160 C, and leave the ceramic "
                "packing unmarked.",
            ),
            ("t0_us", 1756850400000536),
            ("gate_latency_us", 820),
            ("race_window_us", 380),
            ("race_window_rel_ms", [6.20, 6.58]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.wall.C 172 C pulse",
                                "ft.socl.tph 9.2 t/h cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Wall-first latches SOCl2 9.2 -> 5.1 t/h; feed-first keeps "
                            "cruise on a still-cooling packing model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one 2 kHz wall-RTD sample minus SOCl2-orifice group "
                            "delay on this still bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter ~60 us (wall 26 + SOCl2 34): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 380 us window "
                            "would have kept 9.2 t/h cruise; predicted next-sample 166 C > 160 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "reboiler multiplex RTD, 2 kHz, 26 us timestamp jitter",
                    "SOCl2 distillate FT, 1 kHz, 34 us jitter",
                    "ceramic-packing AE puck (context until the collapse)",
                    "overhead HCl GC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("wall_cap_C", 160.0),
                        ("observed_wall_C", 172.0),
                        ("proposed_socl_tph", 9.2),
                        ("reflux_ratio", 2.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. SOCL-C4 indexed on Thionyl-Scroggs TS-2; distillate armed at 9.2 t/h.",
                    "2. Cruise 9.2 t/h; wall 172 C against 160 C metal-temperature cap.",
                    "3. SOCl2 precursor at 1.180 ms; wall warm-start 172 C.",
                    "4. Race window [6.200, 6.580] ms opens on the still bus.",
                    "5. rtd.wall.C 172 C at 6.220 ms (winner).",
                    "6. ft.socl.tph 9.2 t/h at 6.400 ms (loser by 180 us).",
                    "7. Gate at 7.040 ms (winner + 820 us): MODIFY clamp 9.2 -> 5.1 t/h.",
                    "8. Clamp executes; next-sample wall 151 C < 160 cap.",
                    "9. At 23.200 ms stored strain still collapses 14 mm of ceramic packing; AE burst.",
                    "10. Still isolate 15 min (abort_s=900); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_socl_9p2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("socl_tph", 9.2),
                        ("reflux_ratio", 2.4),
                        ("steam_tph", 4.1),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("wall_C", 172.0),
                        ("wall_cap_C", 160.0),
                        ("predicted_unclamped_next_C", 166.0),
                        ("socl_tph", 9.2),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 9.2 t/h cruise: 172 C looks like an HCl-GC spike, not "
                "packing contact, and SOCL-C4 volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Wall 172 C won by 180 us, so the packing is loading heat, not still cooling. "
                "Holding 9.2 t/h predicts next-sample 166 C > 160 cap. MODIFY: SOCl2 9.2 -> "
                "5.1 t/h. Observed after clamp 151 C < 160. A full REJECT is not indicated: a "
                "sound SOCl2 cut accepts 5.1 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "wall_C",
                            OrderedDict(
                                [
                                    ("cap", 160.0),
                                    ("observed", 172.0),
                                    ("predicted_unclamped_next", 166.0),
                                    ("clamped_socl_tph", 5.1),
                                    ("observed_after_clamp", 151.0),
                                ]
                            ),
                        ),
                        (
                            "socl_tph",
                            OrderedDict([("proposed", 9.2), ("clamped", 5.1)]),
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
            ("name", "clamped_socl_5p1"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("socl_tph", 5.1),
                        ("reflux_ratio", 2.4),
                        ("steam_tph", 4.1),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: SOCl2 9.2 -> 5.1 t/h. Process-correct vs the 160 C wall "
                "cap. Packing collapse still occurs at 23.200 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held wall at 151 C. At 23.200 ms stored strain "
                "in the ceramic packing still collapsed a 14 mm face. Clamp reduced dump energy; "
                "it did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("socl", "clamp executed; peak 151 C < 160"),
                        ("packing", "14 mm collapse at 23.200 ms"),
                        ("repair", "15 min still isolate (abort_s=900)"),
                        ("mission", "TS-2 SOCl2 cut incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither wall RTD nor SOCl2 FT predicted the packing charge; ae.pack.blow is a new channel at 23.200 ms, 16.160 ms after the gate, still inside the 46 ms raster.",
                    "Delayed (abort_s=900): 15 min still isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min still isolate after a 14 mm ceramic packing collapse. Safety head -0.60 "
                "prices the split; task_progress stays +0.32 because the SOCl2 clamp completed "
                "under the 160 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.wall.C (6.220 ms, 172 C)"),
                        ("loser", "ft.socl.tph (6.400 ms, 9.2 t/h)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Feed-first by < 180 us inside the 380 us window would have kept "
                            "9.2 t/h cruise; predicted next-sample 166 C would have exceeded "
                            "the 160 cap even without the packing charge. The MODIFY is still the "
                            "correct process. The collapse is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 23200),
            (
                "reward_inflection_note",
                "Safety collapses at the 23.200 ms packing blow (tick t_us=23200), inside "
                "the 46 ms raster. The correct MODIFY at 7.040 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=900 isolate tick.",
            ),
            ("delayed_surprise_s", 900.0),
            ("abort_s", 900),
        ]
    )
    spikes = [
        spike("enc.socl.ctx", 1.180, 0.42),
        spike("rtd.wall.C", 2.480, 0.61),
        spike("ft.socl.tph", 3.640, 0.50),
        spike("rtd.wall.C", 6.220, 1.32),
        spike("ft.socl.tph", 6.400, 1.14),
        spike("ctrl.gate", 7.040, 0.98),
        spike("rtd.wall.C", 8.560, 0.80),
        spike("ft.socl.tph", 11.200, 0.62),
        spike("ctrl.gate", 15.600, 0.84),
        spike("ae.pack.blow", 23.200, 1.46),
        spike("ae.pack.blow", 25.100, 0.91),
        spike("enc.socl.ctx", 32.400, 0.41),
        spike("rtd.wall.C", 41.800, 0.53),
    ]
    ras = raster_core(
        46,
        80,
        25,
        92,
        routing(
            "thalamic-relay.wall-pack",
            "spikenaut.policy.socl-clamp",
            [
                ("relay.rtd.wall", "policy.socl_clamp", 0.66),
                ("relay.ft.socl", "policy.socl_hold", 0.30),
                ("relay.ae.pack", "policy.socl_clamp", -0.45),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at wall win (6.220 ms) opens a 50 ms "
            "eligibility trace that still covers the 23.200 ms packing collapse",
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
                    pop("socl_clamp", 42, 0.50, 250.0, 4),
                    pop("socl_hold", 42, 0.50, 62.5, 1),
                    pop("wall_veto", 22, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r104-536",
        "Thionyl-Scroggs TS-2 / SOCL-C4: wall 172 C beats SOCl2 feed by 180 us; correct "
        "MODIFY still eats an in-window packing collapse (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "46 ms raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named still "
        "isolate (abort_s=900) is not netted into task_progress.",
        ras,
        gate,
        "thionyl-chloride-still",
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
        "15 min still isolate.",
        1,
    )


def record_537():
    ticks = [
        tick(1920, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(4480, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(4660, -0.03, -0.01, -0.03, -0.02, 0.01),
        tick(5280, -0.07, -0.06, -0.07, -0.04, 0.02),
        tick(7440, -0.02, -0.01, -0.02, 0.00, 0.01),
        tick(1080000000, -0.02, -0.01, -0.04, -0.01, 0.00),
    ]
    spikes = [
        spike("ft.pocl.ctx", 0.920, 0.40),
        spike("live.rtd.C", 1.920, 0.58),
        spike("sim.tag.C", 2.680, 0.51),
        spike("live.rtd.C", 4.480, 1.32),
        spike("sim.tag.C", 4.660, 1.15),
        spike("ctrl.gate", 5.280, 1.00),
        spike("live.rtd.C", 7.440, 0.74),
        spike("sim.tag.C", 8.600, 0.61),
        spike("ctrl.gate", 12.400, 0.82),
        spike("ft.pocl.ctx", 17.200, 0.42),
        spike("live.rtd.C", 22.000, 0.53),
        spike("sim.tag.C", 26.800, 0.47),
    ]
    excerpt = independent_excerpt(104537, 90, 30000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Phosphorus-oxychloride kettle POCL-R3 on Phosphox-Lingmoor PL-5 keeps POCl3 at "
                "8.4 t/h with a live jacket RTD of 86.0 C against a 118.0 C trip. A leftover "
                "MODE_SIMULATE tag from last SAT still writes a 142.0 C simulated PV. Live-RTD-first "
                "should ACCEPT the feed; a weak supervisor that binds the simulation tag as live will "
                "REJECT a legal oxychloride kettle.",
            ),
            ("domain", "phosphorus-oxychloride-reactor"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep 8.4 t/h POCl3 on POCL-R3 while live jacket stays <= 118.0 C; "
                "do not spend a leftover MODE_SIMULATE SAT PV on the hold.",
            ),
            ("t0_us", 1756850400000537),
            ("gate_latency_us", 800),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.46, 4.78]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "live.rtd.C 86.0 C jacket LIVE",
                                "sim.tag.C 142.0 C MODE_SIMULATE SAT leftover",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-RTD-first should ACCEPT 8.4 t/h (86.0 C < 118.0 C trip). "
                            "Sim-tag-first tempts a weak supervisor to treat 142.0 C as live.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one POCL-R3 jacket-RTD sample minus leftover sim-tag group delay "
                            "on this oxychloride bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter ~56 us (live 24 + sim 32): 3.2x over "
                            "a 2.0x trust floor. Order is correctly live-RTD-first. The error is binding "
                            "the leftover MODE_SIMULATE tag as process T, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "POCL-R3 jacket RTD, 4 kHz, 24 us jitter, published LIVE analog",
                    "leftover MODE_SIMULATE SAT PV, 4 kHz, 32 us jitter, STALE sim tag",
                    "POCl3 FT (context)",
                    "PCl3 inventory load cell (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("trip_C", 118.0),
                        ("live_C", 86.0),
                        ("sim_pv_C", 142.0),
                        ("mode_simulate", True),
                        ("proposed_feed_tph", 8.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. POCL-R3 latched on Phosphox-Lingmoor PL-5; POCl3 8.4 t/h armed.",
                    "2. Live jacket 86.0 C; leftover MODE_SIMULATE SAT tag still prints 142.0 C.",
                    "3. POCl3-FT precursor at 0.920 ms.",
                    "4. Race window [4.460, 4.780] ms.",
                    "5. live.rtd.C 86.0 C at 4.480 ms (winner).",
                    "6. sim.tag.C 142.0 C at 4.660 ms (loser by 180 us).",
                    "7. Gate at 5.280 ms: REJECT hold 0.0 t/h (incorrect).",
                    "8. Legal POCl3 cancelled; live 86.0 C still < 118.0 C trip.",
                    "9. MODE_SIMULATE bind remains; SAT high-limit unused as a live trip.",
                    "10. Delayed missed_window_s=1080 (18 min oxychloride-quality window) while R3 waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "feed_8p4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 8.4),
                        ("hold", False),
                        ("bound_pv", "live"),
                        ("mode_simulate", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 86.0),
                        ("trip_C", 118.0),
                        ("sim_pv_C", 142.0),
                        ("mode_simulate", True),
                        ("sim_tag_as_live", False),
                        ("pv_live", True),
                        ("proposed_feed_tph", 8.4),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 56),
                        ("missed_window_s", 1080),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 8.4 t/h feed because live jacket 86.0 C is under the 118.0 C "
                "trip; 142.0 C is a leftover MODE_SIMULATE SAT PV, not the live EU.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Leftover MODE_SIMULATE tag still writes 142.0 C from last SAT high-limit inject, "
                "over the 118.0 C trip once the supervisor treats that simulated PV as live. REJECT: "
                "hold POCl3 0.0 t/h until the tag recovers under 118 so the kettle does not see a "
                "hot-spot event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "pocl_C",
                            OrderedDict(
                                [
                                    ("published_live_trip", 118.0),
                                    ("observed_live", 86.0),
                                    ("sim_pv_C", 142.0),
                                    ("mode_simulate", True),
                                    ("sim_tag_as_live", True),
                                    ("executed_feed_tph", 0.0),
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
            ("name", "feed_hold_sim_tag"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 0.0),
                        ("hold", True),
                        ("bound_pv", "sim"),
                        ("mode_simulate", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): feed 8.4 -> 0.0 t/h. Routing relay.sim.tag -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live 86.0 C never "
                "violated the 118.0 C trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze POCL-R3 at 0.0 t/h while live jacket stayed 86.0 C under the "
                "118.0 C trip. 18 min oxychloride-quality window missed. Correct gate was ACCEPT of "
                "the already-legal 8.4 t/h feed.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held at 0.0 t/h; 8.4 t/h abandoned"),
                        ("live_C", "still 86.0 C, under 118.0 C published trip"),
                        ("loop", "18 min oxychloride-quality window missed"),
                        ("sim", "142.0 C MODE_SIMULATE SAT leftover false positive, not a live over-trip"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 142.0 C reading is a leftover MODE_SIMULATE SAT high-limit inject, not a published live over-trip.",
                    "Delayed (missed_window_s=1080): sister POCL-R4 ran the same 8.4 t/h quality window after QA cleared MODE_SIMULATE; R3's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live 86.0 C < published 118.0 C trip; leave 8.4 t/h; drop MODE_SIMULATE; bind live jacket RTD.",
                        ),
                        ("correct_trip_C", 118.0),
                        ("wrong_bound_C", 142.0),
                        ("bound_pv_should_be", "live"),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("feed_tph", 0.0),
                                    ("hold", True),
                                    ("bound_pv", "sim"),
                                    ("mode_simulate", True),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "18 min missed oxychloride-quality window (task/efficiency); live kettle never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "live.rtd.C (4.480 ms, 86.0 C jacket LIVE)"),
                        ("loser", "sim.tag.C (4.660 ms, 142.0 C MODE_SIMULATE)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Sim-tag-first by < 180 us would still show live 86.0 C < 118.0 C. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the live-RTD "
                            "win on a leftover MODE_SIMULATE SAT PV.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5280),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (5.280 ms, tick 4). The 18 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 1080.0),
            ("missed_window_s", 1080),
        ]
    )
    ras = raster_core(
        30,
        90,
        30,
        81,
        routing(
            "relay.sim.tag",
            "policy.hold_reject",
            [
                ("relay.sim.tag", "policy.hold_reject", 0.76),
                ("relay.live.rtd", "policy.hold_reject", 0.16),
            ],
            "acetylcholine",
            0.06,
            "sim_tag_as_live_stdp; ACh tags the (wrong) hold_reject bind at the leftover MODE_SIMULATE shadow",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("missed_window_s", 1080),
                ("delayed_surprise_s", 1080),
                ("mode_simulate", True),
                ("sim_tag_as_live", True),
                ("live_C", 86.0),
                ("trip_C", 118.0),
                ("sim_pv_C", 142.0),
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
                    pop("sim_ctx", 30, 0.55, 104.2, 1),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r104-537",
        "WRONG-REJECT at Phosphox-Lingmoor PL-5 / POCL-R3: live jacket 86.0 C < 118.0 C trip; "
        "supervisor bound leftover MODE_SIMULATE SAT PV 142.0 C as live",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 86.0 < 118.0 on live jacket is true; clamp bound "
        "to a 142.0 C MODE_SIMULATE SAT leftover. total -0.58 = -0.20 + -0.12 + -0.22 + -0.10 + 0.06.",
        ras,
        gate,
        "phosphorus-oxychloride-reactor",
        [
            "reject",
            "wrong-gate",
            "mode-simulate-as-pv",
            "simulation-tag-as-live",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed on a leftover MODE_SIMULATE tag.",
        2,
        supervisor_error_type="wrong-reject",
    )


def record_538():
    ticks = [
        tick(2180, 0.01, 0.06, 0.01, 0.01, 0.01),
        tick(5240, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5412, 0.02, 0.07, 0.02, 0.02, 0.01),
        tick(6080, 0.03, 0.12, 0.04, 0.03, 0.02),
        tick(8120, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(540000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("ir.bus.ctx", 1.040, 0.43),
        spike("ae.cell.pps", 2.180, 0.62),
        spike("ir.bus.C", 3.520, 0.49),
        spike("ae.cell.pps", 5.240, 1.35),
        spike("ir.bus.C", 5.412, 1.12),
        spike("ctrl.gate", 6.080, 1.03),
        spike("ae.cell.pps", 8.120, 0.77),
        spike("ir.bus.ctx", 12.400, 0.44),
        spike("ir.bus.C", 16.800, 0.58),
        spike("ctrl.gate", 21.600, 0.81),
        spike("ae.cell.pps", 27.200, 0.50),
        spike("ir.bus.C", 32.400, 0.46),
        spike("ae.cell.ctx", 35.600, 0.40),
    ]
    excerpt = independent_excerpt(104538, 108, 38000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Chlorate cell KCLO-C7 on Chlorox-Raisbeck CR-HIL is staged for a 12.4 kA pass "
                "while cell AE sits at 58 pps against an 18 pps crack floor. A bus pyrometer, lit "
                "by the pad lamp spectrum, still reports 62 C under a 95 C bus-cap. AE-first "
                "holds the current; IR-first would commit 12.4 kA into a cracked cell.",
            ),
            ("domain", "potassium-chlorate-cell"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Run KCLO-C7 only if cell AE stays <= 18 pps; otherwise hold so a cracked cell is "
                "not loaded at 12.4 kA.",
            ),
            ("t0_us", 1756850400000538),
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
                                "ae.cell.pps 58 pps anode crack",
                                "ir.bus.C 62 C pad-lamp glint",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches cell hold 12.4 -> 0 kA; IR-first would commit "
                            "12.4 kA on a still-legal 62 C bus-cap story.",
                        ),
                        (
                            "window_derivation",
                            "440 us = one cell-AE slot versus bus-IR decode on this HIL chlorate bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 172 us vs combined jitter ~62 us (AE 28 + IR 34): 2.8x over "
                            "a 2.0x trust floor. Reversing order by < 172 us inside the 440 us "
                            "window would have committed 12.4 kA into a 58 pps anode crack.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "cell-shell AE puck, 5 kHz, 28 us jitter",
                    "bus IR camera, 200 Hz, 34 us jitter",
                    "rectifier current encoder (context)",
                    "brine header PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_crack_floor_pps", 18.0),
                        ("observed_ae_pps", 58.0),
                        ("bus_cap_C", 95.0),
                        ("observed_bus_C", 62.0),
                        ("proposed_ka", 12.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. KCLO-C7 indexed on Chlorox-Raisbeck CR-HIL; 12.4 kA armed.",
                    "2. Bus IR 62 C under 95 C cap; AE already 58 pps.",
                    "3. IR-context precursor at 1.040 ms.",
                    "4. Race window [5.200, 5.640] ms.",
                    "5. ae.cell.pps 58 pps at 5.240 ms (winner).",
                    "6. ir.bus.C 62 C at 5.412 ms (loser by 172 us).",
                    "7. Gate at 6.080 ms: REJECT hold cell 0 kA.",
                    "8. Pass cancelled; crack not loaded.",
                    "9. HIL pad lamp spectrum remains the bus glint source.",
                    "10. Delayed (abort_s=540): 9 min cell re-seat before the next pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "chlorate_12p4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ka", 12.4),
                        ("hold", False),
                        ("cell", "KCLO-C7"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 58.0),
                        ("ae_crack_floor_pps", 18.0),
                        ("bus_C", 62.0),
                        ("bus_cap_C", 95.0),
                        ("race_margin_us", 172),
                        ("combined_jitter_us", 62),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 12.4 kA because bus 62 C is under the 95 C "
                "cap and treats the AE puck as brine-header noise.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Cell AE 58 pps won by 172 us, so the anode is cracking, not still quiet. "
                "58 pps > 18 pps floor. REJECT: hold 12.4 -> 0 kA. Bus 62 C < 95 C "
                "does not license the pass once AE is over floor.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "cell_ae_pps",
                            OrderedDict(
                                [
                                    ("floor", 18.0),
                                    ("observed", 58.0),
                                    ("executed_ka", 0.0),
                                ]
                            ),
                        ),
                        (
                            "bus_C",
                            OrderedDict(
                                [
                                    ("cap", 95.0),
                                    ("observed", 62.0),
                                    ("does_not_license_pass", True),
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
            ("name", "cell_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ka", 0.0),
                        ("hold", True),
                        ("cell", "KCLO-C7"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (correct): 12.4 -> 0 kA. Routing relay.ae.cell -> "
                "policy.cell_hold. Crack is not loaded.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held KCLO-C7 at 0 kA. AE 58 pps beat bus 62 C; cell "
                "was already over the 18 pps crack floor. 9 min re-seat follows (abort_s=540).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("cell", "held at 0 kA; 12.4 kA abandoned"),
                        ("shell", "58 pps crack not loaded"),
                        ("bus", "62 C still under 95 C cap"),
                        ("reseat", "9 min cell re-seat queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Bus IR 62 C was a HIL pad-lamp glint, not a bus-cap exceedance.",
                    "Delayed (abort_s=540): 9 min cell re-seat before the next pass on CR-HIL.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.cell.pps (5.240 ms, 58 pps)"),
                        ("loser", "ir.bus.C (5.412 ms, 62 C)"),
                        ("margin_us", 172),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 172 us would have committed 12.4 kA into a cell "
                            "already at 58 pps. The REJECT is still the correct process; AE is the "
                            "licensing channel, not bus IR.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6080),
            (
                "reward_inflection_note",
                "Safety and task credit the correct REJECT at 6.080 ms (tick 4). The 9 min "
                "re-seat is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 540.0),
            ("abort_s", 540),
        ]
    )
    ras = raster_core(
        38,
        108,
        22,
        90,
        routing(
            "thalamic-relay.cell-ae",
            "spikenaut.policy.cell-hold",
            [
                ("relay.ae.cell", "policy.cell_hold", 0.68),
                ("relay.ir.bus", "policy.cell_commit", 0.28),
                ("relay.ae.cell", "policy.cell_hold", 0.12),
            ],
            "dopamine",
            0.07,
            "ae_floor_stdp; DA at cell win (5.240 ms) opens a 70 ms eligibility trace",
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
            ("decision_window_ms", 0.44),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("cell_hold", 54, 0.50, 210.0, 5),
                    pop("cell_commit", 54, 0.50, 42.1, 1),
                    pop("ae_veto", 30, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r104-538",
        "Chlorox-Raisbeck CR-HIL / KCLO-C7: cell AE 58 pps beats bus 62 C; correct "
        "REJECT holds the potassium-chlorate pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 58 pps > 18 pps floor beats a legal bus IR. "
        "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "potassium-chlorate-cell",
        ["reject", "hil", "cell-ae", "chlorate", "correct-gate"],
        "Teaches a cell-AE vs pad-lamp-glint race on a HIL chlorate cell: the crack floor, "
        "not the bus cap, licenses the pass.",
        3,
    )


def record_539():
    ticks = [
        tick(1600, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(4020, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(4176, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(4560, 0.12, 0.09, 0.05, 0.03, 0.02),
        tick(6420, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(300000000, 0.03, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.ndf.ctx", 0.780, 0.41),
        spike("rtd.melt.C", 1.600, 0.58),
        spike("ir.pyro.C", 2.720, 0.47),
        spike("rtd.melt.C", 4.020, 1.28),
        spike("ir.pyro.C", 4.176, 1.10),
        spike("ctrl.gate", 4.560, 0.97),
        spike("rtd.melt.C", 6.420, 0.72),
        spike("enc.ndf.ctx", 10.200, 0.44),
        spike("ir.pyro.C", 14.400, 0.55),
        spike("ctrl.gate", 18.600, 0.80),
        spike("rtd.melt.C", 22.000, 0.49),
        spike("enc.ndf.ctx", 23.400, 0.38),
    ]
    excerpt = independent_excerpt(104539, 60, 24000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Calciotherm crucible ND-F3 of Neodym-Scarth NS-6 already shows melt 980 C while a "
                "pyrometer smear still prints 1240 C against a 1180 C wall-cap the live RTD "
                "has not crossed. Melt-first should ACCEPT 4.2 t/h NdF3; smear-first would "
                "invent a hold on an already-legal calciotherm pass.",
            ),
            ("domain", "neodymium-fluoride-calciotherm"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Run ND-F3 at 4.2 t/h while melt stays <= 1180 C; do not spend a pyrometer "
                "smear on the calciotherm hold.",
            ),
            ("t0_us", 1756850400000539),
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
                                "rtd.melt.C 980 C live",
                                "ir.pyro.C smear as 1240 C",
                            ],
                        ),
                        (
                            "semantics",
                            "Melt-first should ACCEPT 4.2 t/h (980 C < 1180 C wall-cap). "
                            "Smear-first would hold on a simulated pyrometer glint.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one melt-RTD sample versus pyrometer decode on this "
                            "calciotherm bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 156 us vs combined jitter ~52 us (RTD 22 + IR 30): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 156 us inside the 320 us "
                            "window would have invented a hold on an already-legal 980 C melt.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "crucible melt RTD, 4 kHz, 22 us jitter",
                    "pyrometer camera, 200 Hz, 30 us jitter",
                    "NdF3 charge encoder (context)",
                    "argon header PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("melt_cap_C", 1180.0),
                        ("observed_melt_C", 980.0),
                        ("pyro_shadow_C", 1240.0),
                        ("proposed_ndf_tph", 4.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. ND-F3 indexed on Neodym-Scarth NS-6; NdF3 4.2 t/h armed.",
                    "2. Melt 980 C; pyrometer smear as 1240 C over 1180 C wall-cap.",
                    "3. NdF3-encoder precursor at 0.780 ms.",
                    "4. Race window [4.000, 4.320] ms.",
                    "5. rtd.melt.C 980 C at 4.020 ms (winner).",
                    "6. ir.pyro.C smear at 4.176 ms (loser by 156 us).",
                    "7. Gate at 4.560 ms: ACCEPT leave 4.2 t/h.",
                    "8. Melt remains 980 C < 1180 C; smear unused as a hold.",
                    "9. Simulated pyrometer scale remains the IR source.",
                    "10. Delayed (survey_hold_s=300): 5 min REE-assay survey after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "ndf_4p2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ndf_tph", 4.2),
                        ("hold", False),
                        ("melt_C", 980.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("melt_C", 980.0),
                        ("melt_cap_C", 1180.0),
                        ("pyro_shadow_C", 1240.0),
                        ("proposed_ndf_tph", 4.2),
                        ("race_margin_us", 156),
                        ("combined_jitter_us", 52),
                        ("survey_hold_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.2 t/h because melt 980 C is under the 1180 C wall-cap; "
                "1240 C is a pyrometer smear, not a melt temperature.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Melt 980 C won by 156 us and sits under the 1180 C wall-cap. Pyrometer smear "
                "1240 C is a simulated scale, not a melt reading. ACCEPT: leave 4.2 t/h. "
                "A hold would idle a legal calciotherm pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "melt_C",
                            OrderedDict(
                                [
                                    ("cap", 1180.0),
                                    ("observed", 980.0),
                                    ("executed_ndf_tph", 4.2),
                                ]
                            ),
                        ),
                        (
                            "pyro_shadow_C",
                            OrderedDict(
                                [
                                    ("observed", 1240.0),
                                    ("not_a_melt_reading", True),
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
            ("name", "ndf_4p2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ndf_tph", 4.2),
                        ("hold", False),
                        ("melt_C", 980.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 4.2 t/h. Routing relay.rtd.melt -> policy.ndf_go. "
                "Pyrometer unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left ND-F3 at 4.2 t/h. Melt 980 C beat pyrometer smear 1240 C; "
                "the 1180 C wall-cap was never crossed. 5 min REE-assay survey follows "
                "(survey_hold_s=300).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("ndf", "4.2 t/h held as proposed"),
                        ("melt", "980 C < 1180 C wall-cap"),
                        ("glint", "1240 C smear unused"),
                        ("survey", "5 min REE-assay survey queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "IR 1240 C was a simulated pyrometer smear, not a melt over-cap.",
                    "Delayed (survey_hold_s=300): 5 min REE-assay survey after the pass on NS-6.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.melt.C (4.020 ms, 980 C)"),
                        ("loser", "ir.pyro.C (4.176 ms, smear 1240 C)"),
                        ("margin_us", 156),
                        (
                            "counterfactual_if_reversed",
                            "Smear-first by < 156 us would still be a pyrometer glint over the "
                            "1180 C wall-cap; a correct gate ACCEPTs either way. Reversing would only "
                            "have delayed confirmation of the same legal melt.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4560),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 4.560 ms (tick 4). The 5 min "
                "survey is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 300.0),
            ("survey_hold_s", 300),
        ]
    )
    ras = raster_core(
        24,
        60,
        38,
        55,
        routing(
            "thalamic-relay.melt-rtd",
            "spikenaut.policy.ndf-go",
            [
                ("relay.rtd.melt", "policy.ndf_go", 0.70),
                ("relay.ir.pyro", "policy.glint_hold", 0.22),
                ("relay.rtd.melt", "policy.ndf_go", 0.10),
            ],
            "serotonin",
            0.04,
            "already_legal_stdp; 5-HT at melt win (4.020 ms) tags the go bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_hold_s", 300),
                ("delayed_surprise_s", 300),
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
                    pop("ndf_go", 38, 0.50, 246.7, 3),
                    pop("pyro_hold", 38, 0.80, 8.2, 0),
                    pop("rtd_veto", 22, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r104-539",
        "Neodym-Scarth NS-6 / ND-F3: melt 980 C beats pyrometer smear; correct ACCEPT "
        "of an already-legal 4.2 t/h (total +1.10)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Melt 980 C < 1180 C wall-cap; pyrometer smear unused. "
        "total +1.10 = 0.42 + 0.30 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "neodymium-fluoride-calciotherm",
        ["accept", "simulated-smear", "melt-vs-glint", "calciotherm", "simulated"],
        "Teaches that a pyrometer smear can lose to a legal melt RTD inside a "
        "320 us window; reversing 156 us would have invented a hold on an already-legal calciotherm.",
        4,
    )


def record_540():
    ticks = [
        tick(1960, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(5080, 0.09, 0.07, 0.03, 0.03, 0.02),
        tick(5260, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.10, 0.05, 0.03, 0.02),
        tick(7420, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(480000000, 0.04, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.lipf.ctx", 0.880, 0.42),
        spike("rtd.liquor.C", 1.960, 0.59),
        spike("ir.vapor.C", 3.120, 0.48),
        spike("rtd.liquor.C", 5.080, 1.30),
        spike("ir.vapor.C", 5.260, 1.12),
        spike("ctrl.gate", 5.640, 0.99),
        spike("rtd.liquor.C", 7.420, 0.73),
        spike("ft.lipf.ctx", 11.200, 0.44),
        spike("ir.vapor.C", 15.000, 0.54),
        spike("ctrl.gate", 18.200, 0.81),
        spike("rtd.liquor.C", 21.000, 0.50),
    ]
    excerpt = independent_excerpt(104540, 52, 22000, 11, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "LiPF6 crystallizer LIPF-K2 at Hexafluor-Dubbs HD-3 already holds liquor at 42.0 C "
                "while a vapor-space IR smear still prints 71 C against a 58 C liquor-cap the live "
                "RTD has not crossed. Liquor-first should ACCEPT 3.6 t/h LiPF6; smear-first would "
                "invent a hold on an already-legal hexafluorophosphate crop.",
            ),
            ("domain", "lithium-hexafluorophosphate-crystallizer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run K2 at 3.6 t/h while liquor stays <= 58 C; do not spend a vapor-space "
                "IR smear on the LiPF6 hold.",
            ),
            ("t0_us", 1756850400000540),
            ("gate_latency_us", 580),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.06, 5.42]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.liquor.C 42.0 C live",
                                "ir.vapor.C smear as 71 C",
                            ],
                        ),
                        (
                            "semantics",
                            "Liquor-first should ACCEPT 3.6 t/h (42.0 C < 58 C liquor-cap). "
                            "Smear-first would hold on a vapor-space glint.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one liquor-RTD sample versus vapor-IR decode on this "
                            "LiPF6 crystallizer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter ~58 us (RTD 24 + IR 34): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have invented a hold on an already-legal 42.0 C liquor.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "liquor RTD, 4 kHz, 24 us jitter",
                    "vapor IR camera, 200 Hz, 34 us jitter",
                    "LiPF6 slurry FT (context)",
                    "HF inventory load cell (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("liquor_cap_C", 58.0),
                        ("observed_liquor_C", 42.0),
                        ("vapor_shadow_C", 71.0),
                        ("proposed_lipf_tph", 3.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. LIPF-K2 indexed on Hexafluor-Dubbs HD-3; LiPF6 3.6 t/h armed.",
                    "2. Liquor 42.0 C; vapor-IR smear as 71 C over 58 C liquor-cap.",
                    "3. LiPF6-FT precursor at 0.880 ms.",
                    "4. Race window [5.060, 5.420] ms.",
                    "5. rtd.liquor.C 42.0 C at 5.080 ms (winner).",
                    "6. ir.vapor.C smear at 5.260 ms (loser by 180 us).",
                    "7. Gate at 5.640 ms: ACCEPT leave 3.6 t/h.",
                    "8. Liquor remains 42.0 C < 58 C; smear unused as a hold.",
                    "9. Vapor-space scale remains the IR source.",
                    "10. Delayed (dwell_s=480): 8 min crystal-size dwell after the crop.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "lipf_3p6"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("lipf_tph", 3.6),
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
                        ("liquor_cap_C", 58.0),
                        ("vapor_shadow_C", 71.0),
                        ("proposed_lipf_tph", 3.6),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("dwell_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 3.6 t/h because liquor 42.0 C is under the 58 C liquor-cap; "
                "71 C is a vapor-space IR smear, not a liquor temperature.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Liquor 42.0 C won by 180 us and sits under the 58 C liquor-cap. Vapor smear "
                "71 C is headspace scale, not a liquor reading. ACCEPT: leave 3.6 t/h. "
                "A hold would idle a legal LiPF6 crop.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "liquor_C",
                            OrderedDict(
                                [
                                    ("cap", 58.0),
                                    ("observed", 42.0),
                                    ("executed_lipf_tph", 3.6),
                                ]
                            ),
                        ),
                        (
                            "vapor_shadow_C",
                            OrderedDict(
                                [
                                    ("observed", 71.0),
                                    ("not_a_liquor_reading", True),
                                ]
                            ),
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
            ("name", "lipf_3p6"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("lipf_tph", 3.6),
                        ("hold", False),
                        ("liquor_C", 42.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 3.6 t/h. Routing relay.rtd.liquor -> policy.lipf_go. "
                "Vapor-IR unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left K2 at 3.6 t/h. Liquor 42.0 C beat vapor smear 71 C; "
                "the 58 C liquor-cap was never crossed. 8 min crystal-size dwell follows "
                "(dwell_s=480).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("lipf", "3.6 t/h held as proposed"),
                        ("liquor", "42.0 C < 58 C liquor-cap"),
                        ("glint", "71 C smear unused"),
                        ("dwell", "8 min crystal-size dwell queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "IR 71 C was a vapor-space smear, not a liquor over-cap.",
                    "Delayed (dwell_s=480): 8 min crystal-size dwell after the crop on HD-3.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.liquor.C (5.080 ms, 42.0 C)"),
                        ("loser", "ir.vapor.C (5.260 ms, smear 71 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Smear-first by < 180 us would still be a vapor glint over the "
                            "58 C liquor-cap; a correct gate ACCEPTs either way. Reversing would only "
                            "have delayed confirmation of the same legal liquor.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5640),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 5.640 ms (tick 4). The 8 min "
                "dwell is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480.0),
            ("dwell_s", 480),
        ]
    )
    ras = raster_core(
        22,
        52,
        42,
        48,
        routing(
            "thalamic-relay.liquor-rtd",
            "spikenaut.policy.lipf-go",
            [
                ("relay.rtd.liquor", "policy.lipf_go", 0.71),
                ("relay.ir.vapor", "policy.glint_hold", 0.20),
                ("relay.rtd.liquor", "policy.lipf_go", 0.11),
            ],
            "adenosine",
            0.045,
            "already_legal_stdp; adenosine at liquor win (5.080 ms) tags the go bind",
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
                    pop("lipf_go", 34, 0.50, 277.8, 3),
                    pop("vapor_hold", 34, 0.80, 8.2, 0),
                    pop("rtd_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r104-540",
        "Hexafluor-Dubbs HD-3 / LIPF-K2: liquor 42.0 C beats vapor smear; correct ACCEPT "
        "of an already-legal 3.6 t/h (total +1.14)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Liquor 42.0 C < 58 C liquor-cap; vapor smear unused. "
        "total +1.14 = 0.44 + 0.32 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "lithium-hexafluorophosphate-crystallizer",
        ["accept", "liquor-vs-glint", "lipf6", "designed", "already-legal"],
        "Teaches that a vapor-space IR smear can lose to a legal liquor RTD inside a "
        "360 us window; reversing 180 us would have invented a hold on an already-legal LiPF6 crop.",
        5,
    )
