def lif_421_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.42
    stim = (22000, 25000)
    seed = 81421
    window_us = 42000
    i_clamp_extra = 0.62
    clamp_n = 14
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
    burst = [(t, nid) for t, nid in spikes if 22000 <= t < 25000]
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
    take(burst, 9, label_times=(22600, 23100, 23800))
    clamp = [(t, nid) for t, nid in picked if t < 22000][:7]
    spall = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + spall, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.spall" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 76),
            ("dt_us", 100),
            ("tau_m_ms", 19.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.91),
            ("i_stim_peak", 2.42),
            ("stim_t_us", [22000, 25000]),
            ("i_clamp_extra", 0.62),
            ("clamp_n", 14),
            ("seed", 81421),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 SiCl4-MFC clamp bias; stim 22-25 ms is the burner brick spall.",
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


def record_421():
    excerpt, extra = lif_421_excerpt()
    ticks = [
        tick(2112, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5280, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5460, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5980, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22600, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Halosil-Knowe HK-4 flame burner B-2 dumps 52 kg/h SiCl4 against a 32 kg/h "
                "hydrolysis cap, while the H2/O2 flame pyrometer still prints 1060 C (limit 1140). "
                "MFC-priority clamps 52 -> 24 kg/h; a flame-first policy would leave cruise. A "
                "loose burner brick is already seated and only the later AE burst names it.",
            ),
            ("domain", "fumed-silica-flame"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep B-2 SiCl4 <= 32 kg/h and finish the fumed-silica flame without dumping "
                "product through a spalled burner brick.",
            ),
            ("t0_us", 1756850400000421),
            ("gate_latency_us", 700),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.280, 5.640]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "mfc.sicl4.kgh 52 over 32 cap",
                                "tc.flame.C 1060 with skin under 1140",
                            ],
                        ),
                        (
                            "semantics",
                            "Silane-tetrachloride-first latches MFC clamp 52 -> 24 kg/h; "
                            "pyrometer-first keeps 52 on a 'still under flame-skin cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one SiCl4 MFC slot versus the flame-pyrometer publisher on "
                            "this fumed-silica burner bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (MFC 28 + TC 34): 2.90x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 52 kg/h; predicted next-sample 44 kg/h "
                            "> 32 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "SiCl4 MFC, 2 kHz, 28 us jitter",
                    "flame pyrometer + skin TC, 1 kHz, 34 us jitter",
                    "burner-brick AE puck (context)",
                    "H2/O2 header FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("sicl4_cap_kgh", 32.0),
                        ("observed_sicl4_kgh", 52.0),
                        ("flame_C", 1060.0),
                        ("flame_cap_C", 1140.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. B-2 indexed on Halosil-Knowe HK-4; SiCl4 52 kg/h; flame 1060 C.",
                    "2. Skin under 1140 C cap; flame hydrolysis armed.",
                    "3. Pyrometer precursor at 1.180 ms.",
                    "4. Race window [5.280, 5.640] ms.",
                    "5. mfc.sicl4.kgh 52 at 5.280 ms (winner).",
                    "6. tc.flame.C 1060 at 5.460 ms (loser by 180 us).",
                    "7. Gate at 5.980 ms: MODIFY clamp 52 -> 24 kg/h.",
                    "8. After clamp SiCl4 20 kg/h <= 32; flame still 1060 C.",
                    "9. At 22.600 ms a burner brick spall dumps 2 bags of fume.",
                    "10. 15 min burner isolate (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_sicl4_mfc"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("sicl4_kgh", 52.0),
                        ("flame_C", 1060.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("sicl4_kgh", 52.0),
                        ("sicl4_cap_kgh", 32.0),
                        ("predicted_unclamped_next_kgh", 44.0),
                        ("flame_C", 1060.0),
                        ("flame_cap_C", 1140.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 52 kg/h because flame 1060 C is under 1140, treating the "
                "52 kg/h SiCl4 as a still-wet MFC rather than a hydrolysis-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "SiCl4 52 kg/h won by 180 us, so the burner is over-cap, not still a flame-skin "
                "story. Holding 52 kg/h predicts next-sample 44 kg/h > 32 cap. MODIFY: SiCl4 "
                "52 -> 24 kg/h. Observed after clamp 20 kg/h <= 32. A full REJECT is not "
                "indicated: a clean flame accepts 24 kg/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "sicl4_kgh",
                            OrderedDict(
                                [
                                    ("cap", 32.0),
                                    ("observed", 52.0),
                                    ("predicted_unclamped_next", 44.0),
                                    ("clamped_sicl4_kgh", 24.0),
                                    ("observed_after_clamp", 20.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 2.90),
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
            ("name", "clamped_sicl4_mfc"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("sicl4_kgh", 24.0),
                        ("flame_C", 1060.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: SiCl4 52 -> 24 kg/h. Process-correct vs the 32 kg/h hydrolysis cap. "
                "Burner brick still spalls at 22.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held SiCl4 at 20 kg/h. At 22.600 ms a burner brick "
                "already seated under the quill dumped 2 bags of fume. Clamp reduced dump "
                "energy; it did not prevent the spall. Partnered negative: process heads stay "
                "honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("sicl4", "clamp executed; peak 20 kg/h <= 32 cap"),
                        ("brick", "spalled at 22.600 ms; 2 bags dumped"),
                        ("repair", "15 min burner isolate (abort_s=900)"),
                        ("mission", "HK-4 flame incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither SiCl4 MFC nor flame pyrometer predicted the seated burner brick; ae.brick.spall is a new channel at 22.600 ms, 16.620 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min burner isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min burner isolate after the brick spall. Safety head -0.60 prices the "
                "dump; task_progress stays +0.32 because the MFC clamp completed under the 32 "
                "kg/h cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "mfc.sicl4.kgh (5.280 ms, 52 kg/h)"),
                        ("loser", "tc.flame.C (5.460 ms, 1060 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Pyrometer-first by < 180 us inside the 360 us window would have kept "
                            "52 kg/h; predicted next-sample 44 kg/h would have missed the 32 "
                            "cap even without the spall. The MODIFY is still the correct "
                            "process. The spall is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22600),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.600 ms burner-brick spall (tick t_us=22600), inside "
                "the 42 ms raster. The correct MODIFY at 5.980 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=900 isolation tick.",
            ),
            ("delayed_surprise_s", 900),
        ]
    )
    spikes = [
        spike("tc.flame.C", 1.180, 0.41),
        spike("mfc.sicl4.kgh", 2.112, 0.58),
        spike("tc.flame.C", 3.400, 0.50),
        spike("mfc.sicl4.kgh", 5.280, 1.31),
        spike("tc.flame.C", 5.460, 1.12),
        spike("ctrl.gate", 5.980, 0.97),
        spike("mfc.sicl4.kgh", 8.100, 0.82),
        spike("tc.flame.C", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.brick.spall", 22.600, 1.48),
        spike("ae.brick.spall", 24.100, 0.93),
        spike("tc.flame.C", 30.200, 0.40),
        spike("mfc.sicl4.kgh", 36.400, 0.55),
    ]
    dw = 0.36
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.flame-sicl4",
            "spikenaut.policy.mfc-clamp",
            [
                ("relay.mfc.sicl4", "policy.sicl4_clamp", 0.68),
                ("relay.tc.flame", "policy.temp_hold", 0.29),
                ("relay.ae.brick", "policy.sicl4_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at SiCl4 win (5.280 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.600 ms burner-brick spall",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", dw),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("sicl4_clamp", 50, 0.50, 220.0, dw),
                    pop_budget("temp_hold", 40, 0.80, 50.0, dw),
                    pop("spall_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r81-421"),
            (
                "title",
                "Halosil-Knowe HK-4 / Burner B-2: SiCl4 beats flame pyrometer by 180 us; "
                "correct MODIFY still eats an in-window burner-brick spall (partnered negative "
                "total -0.44)",
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
                    "42 ms raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named "
                    "burner isolate (abort_s=900) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "fumed-silica-flame",
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
                    "15 min burner isolate.",
                    1,
                ),
            ),
        ]
    )


def record_422():
    ticks = [
        tick(2160, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5400, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5580, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5920, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6260, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("ft.steam.hs", 1.080, 0.42),
        spike("ft.steam.ls", 2.160, 0.57),
        spike("ft.steam.hs", 3.400, 0.49),
        spike("ft.steam.hs", 5.400, 1.29),
        spike("ft.steam.ls", 5.580, 1.10),
        spike("ctrl.gate", 5.920, 0.96),
        spike("ft.steam.hs", 8.200, 0.80),
        spike("ft.steam.ls", 10.200, 0.63),
        spike("ctrl.gate", 12.400, 0.84),
        spike("ft.steam.hs", 16.400, 0.41),
        spike("ft.steam.ls", 22.100, 0.54),
        spike("ft.steam.hs", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(81422, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Bromal-Wythe BW-7 steaming tower T-3 high-select steam reads 16.8 t/h against "
                "an 11.0 t/h cap. The currently-losing low-select transmitter still prints 3.6 t/h. "
                "HS-priority should cut the 16.8 t/h leg; a weak supervisor binds the losing LS "
                "transmitter and spends the cut there.",
            ),
            ("domain", "bromine-blowout-tower"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the BW-7 bromine blowout with live high-select steam <= 11.0 t/h, leave "
                "the low-select spare at 3.6 t/h, and bind the winning HS transmitter only.",
            ),
            ("t0_us", 1756850400000422),
            ("gate_latency_us", 520),
            ("race_window_us", 340),
            ("race_window_rel_ms", [5.400, 5.740]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.steam.hs 16.8 t/h LIVE high-select",
                                "ft.steam.ls 3.6 t/h currently-losing low-select",
                            ],
                        ),
                        (
                            "semantics",
                            "High-select-first should latch MODIFY of the 16.8 t/h HS leg; "
                            "low-select-first is a false under-cap if 3.6 t/h is treated as the PV.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live HS Coriolis slot versus the LS transmitter on this "
                            "blowout high/low-select pair.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (HS 28 + LS 32). Order is "
                            "correctly HS-first. The error is the selector bound to the losing "
                            "leg, not the race winner: 16.8 t/h is still over the 11.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "high-select steam Coriolis, 2 kHz, 28 us jitter, status=LIVE",
                    "low-select steam Coriolis, 1 kHz, 32 us jitter, currently losing",
                    "bromine ORP (context)",
                    "air-blow FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("steam_cap_tph", 11.0),
                        ("live_hs_tph", 16.8),
                        ("ls_tph", 3.6),
                        ("select_bound_correct", "high"),
                        ("air_nm3h", 420.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. T-3 LIVE already steaming; HS 16.8 t/h; LS 3.6 t/h.",
                    "2. High-select should pick HS; LS is the currently-losing transmitter.",
                    "3. HS precursor at 1.080 ms.",
                    "4. Race window [5.400, 5.740] ms.",
                    "5. ft.steam.hs 16.8 at 5.400 ms (winner).",
                    "6. ft.steam.ls 3.6 at 5.580 ms (loser by 180 us).",
                    "7. Gate at 5.920 ms: WRONG-MODIFY binds low-select losing leg.",
                    "8. LS 3.6 -> 0.90 t/h; HS left at 16.8 t/h; brine dumps bromine.",
                    "9. Live HS stays over 11.0; the cut was spent on the losing transmitter.",
                    "10. Delayed (abort_s=720): 12 min tower dump while T-3 is quenched.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cut_hs_steam"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("hs_tph", 7.2),
                        ("ls_tph", 3.6),
                        ("select_bound", "high"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_hs_tph", 16.8),
                        ("cap_tph", 11.0),
                        ("ls_tph", 3.6),
                        ("select_bound_correct", "high"),
                        ("air_nm3h", 420.0),
                        ("t_gate_us", 5920),
                        ("correct_hs_tph", 7.2),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes cutting HS steam 16.8 -> 7.2 t/h because live high-select is "
                "over the 11.0 t/h cap; the 3.6 t/h LS reading is the currently-losing transmitter.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Steam 3.6 t/h is under the 11.0 cap (true if the low-select loser is the PV). "
                "Apply a 0.90 t/h cut on the highlighted LS transmitter, because FT.STEAM.LS is "
                "still in the mimic. Leave the live HS unread as the select winner.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "steam_flow",
                            OrderedDict(
                                [
                                    ("cap_tph", 11.0),
                                    ("live_hs_tph", 16.8),
                                    ("ls_tph", 3.6),
                                    ("executed_hs_tph", 16.8),
                                    ("executed_ls_tph", 0.90),
                                    ("correct_hs_tph", 7.2),
                                ]
                            ),
                        ),
                        (
                            "selector_bind",
                            OrderedDict(
                                [
                                    ("t_gate_us", 5920),
                                    ("select_bound", "low"),
                                    ("wrong_leg", True),
                                    ("live_leg", "high"),
                                    ("losing_leg", "low"),
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
            ("name", "steam_cut_wrong_leg"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("hs_tph", 16.8),
                        ("ls_tph", 0.90),
                        ("select_bound", "low"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / selector-wrong-leg): 0.90 t/h LS cut applied because the "
                "currently-losing low-select transmitter was bound. Routing relay.ft.ls -> "
                "policy.ls_cut; no positive weight to policy.hs_cut.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY clamped the losing low-select steam leg. Live HS 16.8 t/h was over "
                "the 11.0 t/h cap at t_gate; LS 3.6 t/h was the currently-losing transmitter. "
                "HS stayed open and dumped bromine. 12 min tower dump (abort_s=720). Correct "
                "gate was MODIFY HS 16.8 -> 7.2 t/h on high-select at t_gate_us=5920.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live_hs", "left 16.8 t/h over the 11.0 cap"),
                        ("losing_ls", "cut 3.6 -> 0.90 t/h on the currently-losing transmitter"),
                        ("dump", "12 min bromine dump, T-3 quench"),
                        ("mission", "blowout deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "HS-first was the correct order and the HS number was over cap; the MODIFY spent that win on the currently-losing low-select transmitter.",
                    "Delayed (abort_s=720): BW-7 holds 12 min while T-3 is dumped and restacked; next brine 14 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY steam HS 16.8 -> 7.2 t/h on LIVE high-select at t_gate_us=5920; select_bound=high; leave LS at 3.6 t/h.",
                        ),
                        ("correct_actuator", "T-3_steam_hs_tph"),
                        ("wrong_leg", "low-select currently-losing transmitter"),
                        ("t_gate_us", 5920),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("hs_tph", 16.8),
                                    ("ls_tph", 0.90),
                                    ("select_bound", "low"),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min bromine dump (task/efficiency); legal HS cut was skipped because the currently-losing LS transmitter was bound as PV.",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.steam.hs (5.400 ms, 16.8 t/h LIVE high-select)"),
                        ("loser", "ft.steam.ls (5.580 ms, 3.6 t/h currently-losing)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "LS-first by < 180 us would still be 3.6 t/h under the 11.0 t/h cap "
                            "on the losing transmitter; a correct gate binds ft.steam.hs to "
                            "policy.hs_cut at t_gate either way. The wrong MODIFY spent the HS "
                            "win on a selector-wrong-leg clamp.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5920),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong-leg bind (5.920 ms, tick 4). "
                "The 12 min tower dump is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 720),
        ]
    )
    dw = 0.34
    ras = raster_core(
        28,
        88,
        34,
        84,
        routing(
            "thalamic-relay.br2-select",
            "spikenaut.policy.wrong-leg-cut",
            [
                ("relay.ft.ls", "policy.ls_cut", 0.74),
                ("relay.ft.hs", "policy.ls_cut", 0.21),
            ],
            "acetylcholine",
            0.08,
            "selector_cap_stdp; ACh tags the (wrong) ls_cut bind at the HS win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 720),
                ("delayed_surprise_s", 720),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", dw),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("ls_cut", 48, 0.45, 300.0, dw),
                    pop("hs_cut", 48, 0.90),
                    pop("select_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r81-422"),
            (
                "title",
                "WRONG-MODIFY at Bromal-Wythe BW-7 / Tower T-3: live HS 16.8 t/h over cap; "
                "0.90 t/h cut applied on the currently-losing LS transmitter (selector-wrong-leg)",
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
                    "Wrong-modify / selector-wrong-leg. Sidecar arithmetic 16.8 > 11.0 on live "
                    "HS is true; MODIFY bound to ls_cut. total -0.68 = -0.22 + -0.24 + "
                    "-0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "bromine-blowout-tower",
                    [
                        "modify",
                        "wrong-gate",
                        "selector-wrong-leg",
                        "high-low-select",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct HS-first race can still be a wrong gate "
                    "when the MODIFY clamps the currently-losing low-select transmitter. "
                    "Convictable from select_bound, live_hs_tph vs cap, and routing without "
                    "bromine-blowout physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_423():
    ticks = [
        tick(2736, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6840, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7020, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7640, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(7960, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("pt.vessel.MPa", 1.360, 0.40),
        spike("ae.pox.pps", 2.736, 0.56),
        spike("pt.vessel.MPa", 4.100, 0.48),
        spike("ae.pox.pps", 6.840, 1.34),
        spike("pt.vessel.MPa", 7.020, 1.11),
        spike("ctrl.gate", 7.640, 0.98),
        spike("ae.pox.pps", 10.400, 0.81),
        spike("pt.vessel.MPa", 14.800, 0.62),
        spike("ctrl.gate", 18.200, 0.84),
        spike("ae.pox.pps", 28.400, 0.52),
        spike("pt.vessel.MPa", 36.100, 0.39),
        spike("ae.pox.pps", 42.200, 0.44),
    ]
    excerpt = independent_excerpt(81423, 120, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Poxore-Slade PS-HIL autoclave A-4 is a hardware-in-loop POX whose lining AE is "
                "52 pps against a 10 pps growl trip, even though vessel pressure sits at 3.8 MPa "
                "below the 5.5 MPa header limit. Acoustic-priority freezes the 18 t/h slurry "
                "charge; a pressure-priority push would still send ore because the PT looks "
                "in-spec. The HIL mockup, not the dead-ore plant floor, owns the gate.",
            ),
            ("domain", "gold-pox-autoclave"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep A-4 from dispatching a growling POX while vessel pressure remains under "
                "its own cap.",
            ),
            ("t0_us", 1756850400000423),
            ("gate_latency_us", 800),
            ("race_window_us", 320),
            ("race_window_rel_ms", [6.840, 7.160]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.pox.pps 52 over 10 cap",
                                "pt.vessel.MPa 3.8 under 5.5 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; pressure-first dispatches 18 t/h slurry on a "
                            "'header still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one AE puck slot versus the vessel-PT publisher on this "
                            "HIL POX-autoclave bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + PT 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have dispatched 18 t/h into a growling lining.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "lining AE puck, 50 kHz, 26 us jitter",
                    "vessel PT, 1 kHz, 32 us jitter",
                    "slurry weigh-belt (context)",
                    "oxygen FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 10.0),
                        ("observed_ae_pps", 52.0),
                        ("vessel_MPa", 3.8),
                        ("vessel_cap_MPa", 5.5),
                        ("proposed_slurry_tph", 18.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. A-4 HIL indexed; 18 t/h slurry armed.",
                    "2. Vessel 3.8 MPa under 5.5; AE 52 pps over 10.",
                    "3. Pressure precursor at 1.360 ms.",
                    "4. Race window [6.840, 7.160] ms.",
                    "5. ae.pox.pps 52 at 6.840 ms (winner).",
                    "6. pt.vessel.MPa 3.8 at 7.020 ms (loser by 180 us).",
                    "7. Gate at 7.640 ms: REJECT hold, do not dispatch.",
                    "8. Feed 0 t/h; pressure left at 3.8 MPa.",
                    "9. Lining inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min autoclave reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_slurry"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("slurry_tph", 18.0),
                        ("hold", False),
                        ("vessel_MPa", 3.8),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 52.0),
                        ("ae_cap_pps", 10.0),
                        ("vessel_MPa", 3.8),
                        ("vessel_cap_MPa", 5.5),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18 t/h slurry because vessel 3.8 MPa is under 5.5, treating "
                "the 52 pps AE as agitator hash rather than a growling lining.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Lining AE 52 pps won by 180 us, so the autoclave is growling, not still a "
                "header story. Vessel 3.8 MPa is under 5.5 and does not authorize dispatch. "
                "REJECT: hold feed 18 -> 0 t/h. A MODIFY that only trims oxygen would leave "
                "the growl.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ae_pps",
                            OrderedDict(
                                [
                                    ("cap", 10.0),
                                    ("observed", 52.0),
                                    ("executed_slurry_tph", 0.0),
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
            ("name", "hold_pox_autoclave"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("slurry_tph", 0.0),
                        ("hold", True),
                        ("vessel_MPa", 3.8),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: slurry 18 -> 0 t/h. Vessel left at 3.8 MPa under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held A-4. AE 52 pps beat vessel 3.8 MPa by 180 us. Header was "
                "legal; the lining was not. 8 min autoclave reset (abort_s=480) is delayed "
                "survey, not a process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held at 0 t/h"),
                        ("vessel", "left 3.8 MPa < 5.5 cap"),
                        ("lining", "8 min autoclave reset (abort_s=480)"),
                        ("mission", "HIL slurry not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Vessel PT never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min autoclave reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.pox.pps (6.840 ms, 52 pps)"),
                        ("loser", "pt.vessel.MPa (7.020 ms, 3.8 MPa)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Pressure-first by < 180 us inside the 320 us window would have "
                            "dispatched 18 t/h into a growling lining. The REJECT is still the "
                            "correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7640),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.640 ms, tick 4). The 8 min "
                "autoclave reset is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    dw = 0.32
    ras = raster_core(
        46,
        120,
        20,
        110,
        routing(
            "thalamic-relay.pox-ae",
            "spikenaut.policy.pox-hold",
            [
                ("relay.ae.pox", "policy.pox_hold", 0.70),
                ("relay.pt.vessel", "policy.header_go", 0.24),
            ],
            "dopamine",
            0.05,
            "hold_stdp; DA tags the AE win as a reject-hold bind",
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
            ("decision_window_ms", dw),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop_budget("pox_hold", 56, 0.45, 280.0, dw),
                    pop("header_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r81-423"),
            (
                "title",
                "Poxore-Slade PS-HIL / Autoclave A-4: lining AE 52 pps beats vessel 3.8 MPa "
                "by 180 us; correct REJECT holds slurry",
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
                    "Correct REJECT. AE 52 > 10 cap beats legal vessel header. "
                    "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "gold-pox-autoclave",
                    [
                        "reject",
                        "hil",
                        "ae-vs-header",
                        "growling-lining",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal vessel header can lose to lining AE inside a 320 us "
                    "window; reversing 180 us would have dispatched a growling POX autoclave.",
                    3,
                ),
            ),
        ]
    )


def record_424():
    ticks = [
        tick(2880, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7200, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7380, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7840, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8200, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.shell.C", 1.200, 0.40),
        spike("gc.nh3.wt", 2.880, 0.55),
        spike("tc.shell.C", 4.400, 0.48),
        spike("gc.nh3.wt", 7.200, 1.26),
        spike("tc.shell.C", 7.380, 1.08),
        spike("ctrl.gate", 7.840, 0.95),
        spike("gc.nh3.wt", 11.200, 0.78),
        spike("tc.shell.C", 14.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("gc.nh3.wt", 22.600, 0.50),
        spike("tc.shell.C", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(81424, 48, 28000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("urea_tph", 9.5),
            ("nh3_wt_pct", 1.48),
            ("shell_C", 78.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Carbam-Eyot CE-5 pool condenser C-1 shows free NH3 at 1.48 wt percent "
                "(spec 2.20) and a 78 C shell (spec 95). The simulated loop wants to keep 9.5 "
                "t/h moving. Ammonia-GC confirmation should green-light that rate; a "
                "shell-priority critic would stall a lawful pool as if the titer were still "
                "rising.",
            ),
            ("domain", "urea-pool-condenser"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the CE-5 recycle with free NH3 <= 2.20 wt percent and shell <= 95 C.",
            ),
            ("t0_us", 1756850400000424),
            ("gate_latency_us", 640),
            ("race_window_us", 360),
            ("race_window_rel_ms", [7.200, 7.560]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "gc.nh3.wt 1.48 under 2.20 cap",
                                "tc.shell.C 78 under 95 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "GC-first confirms the already-legal 9.5 t/h recycle; shell-first "
                            "would have treated the GC as a climb echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one online-GC slot versus the shell-TC publisher on this "
                            "simulated urea-pool bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (GC 26 + TC 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed recycle illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "online ammonia GC, 26 us jitter",
                    "shell TC well, 32 us jitter",
                    "urea FT (context)",
                    "carbamate recycle FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("nh3_cap_wt_pct", 2.20),
                        ("observed_nh3_wt_pct", 1.48),
                        ("shell_cap_C", 95.0),
                        ("observed_shell_C", 78.0),
                        ("proposed_urea_tph", 9.5),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. C-1 indexed on Carbam-Eyot CE-5; 9.5 t/h recycle armed.",
                    "2. Caps: NH3 2.20 wt percent, shell 95 C.",
                    "3. Shell-TC precursor at 1.200 ms.",
                    "4. Race window [7.200, 7.560] ms.",
                    "5. gc.nh3.wt 1.48 at 7.200 ms (winner).",
                    "6. tc.shell.C 78 at 7.380 ms (loser by 180 us).",
                    "7. Gate at 7.840 ms: ACCEPT 9.5 t/h already legal.",
                    "8. Recycle continues; no extra hold.",
                    "9. 6 min survey confirms NH3 still under 2.20.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "recycle_95"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("nh3_wt_pct", 1.48),
                        ("nh3_cap_wt_pct", 2.20),
                        ("shell_C", 78.0),
                        ("shell_cap_C", 95.0),
                        ("urea_tph", 9.5),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 9.5 t/h recycle because NH3 1.48 is under 2.20 and shell "
                "78 C is under 95 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Free ammonia 1.48 wt percent won by 180 us and is under 2.20. Shell 78 C "
                "is under 95 C. ACCEPT the already-legal recycle.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "nh3_wt_pct",
                            OrderedDict(
                                [
                                    ("cap", 2.20),
                                    ("observed", 1.48),
                                    ("executed_urea_tph", 9.5),
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
            ("name", "recycle_95"),
            ("parameters", OrderedDict(params.items())),
            (
                "gate_effect",
                "ACCEPT: 9.5 t/h recycle and 1.48 wt percent NH3 unchanged. Routing "
                "relay.gc.nh3 -> policy.pool_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left C-1 on a 9.5 t/h / 1.48 wt percent NH3 recycle. Shell "
                "hitch did not justify a hold. 6 min survey confirmed NH3 still under 2.20.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("recycle", "still 9.5 t/h"),
                        ("nh3", "1.48 under 2.20 cap"),
                        ("shell", "78 C under 95"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Shell TC 78 C hitch is residual, not a runaway trip.",
                    "Delayed (survey_s=360): 6 min survey restacks C-1 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "gc.nh3.wt (7.200 ms, 1.48 wt percent)"),
                        ("loser", "tc.shell.C (7.380 ms, 78 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Shell-first by < 180 us would only delay confirmation. The recycle "
                            "stays legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7840),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (7.840 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 360),
        ]
    )
    dw = 0.36
    ras = raster_core(
        28,
        48,
        42,
        56,
        routing(
            "thalamic-relay.nh3-gc",
            "spikenaut.policy.pool-go",
            [
                ("relay.gc.nh3", "policy.pool_go", 0.68),
                ("relay.tc.shell", "policy.shell_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_pool_stdp; 5-HT tags the pool_go bind at the GC win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 360),
                ("delayed_surprise_s", 360),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", dw),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("pool_go", 40, 0.45, 250.0, dw),
                    pop("shell_hold", 32, 0.90),
                    pop("nh3_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r81-424"),
            (
                "title",
                "Carbam-Eyot CE-5 / Pool C-1: free NH3 1.48 beats shell 78 C by 180 us; "
                "ACCEPT already-legal 9.5 t/h urea recycle",
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
                    "Correct ACCEPT of an already-legal urea-pool recycle. total +1.06 = "
                    "0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "urea-pool-condenser",
                    [
                        "accept",
                        "already-legal",
                        "simulated-urea-pool",
                        "gc-vs-tc",
                        "sidecar-convictable",
                        "simulated",
                    ],
                    "Teaches that an ammonia GC under cap can confirm an already-legal "
                    "recycle without a shell hitch becoming a hold.",
                    4,
                ),
            ),
        ]
    )


def record_425():
    ticks = [
        tick(2016, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5040, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5920, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(240000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.dome.C", 0.980, 0.41),
        spike("gc.topgas.CO", 2.016, 0.60),
        spike("tc.dome.C", 3.200, 0.51),
        spike("gc.topgas.CO", 5.040, 1.30),
        spike("tc.dome.C", 5.200, 1.12),
        spike("ctrl.gate", 5.640, 0.97),
        spike("gc.topgas.CO", 8.100, 0.78),
        spike("tc.dome.C", 12.400, 0.62),
        spike("ctrl.gate", 16.200, 0.85),
        spike("gc.topgas.CO", 20.400, 0.54),
        spike("tc.dome.C", 22.800, 0.43),
    ]
    excerpt = independent_excerpt(81425, 80, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("ore_tph", 4.8),
            ("topgas_co_pct", 18.6),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Melter-Taing MT-2 smelt-reduction gasifier G-1 assays 18.6 percent top-gas CO "
                "versus a 24.0 percent ceiling, with 1380 C dome versus 1480 C. Ore at 4.8 t/h "
                "sits inside both limits. GC-priority should keep the char bed turning; "
                "dome-priority would park a lawful reduction as if the offgas were still climbing.",
            ),
            ("domain", "corex-melter-gasifier"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run G-1 at 4.8 t/h ore, keep top-gas CO <= 24.0 percent and dome <= 1480 C, "
                "and leave the char bed on schedule.",
            ),
            ("t0_us", 1756850400000425),
            ("gate_latency_us", 600),
            ("race_window_us", 280),
            ("race_window_rel_ms", [5.040, 5.320]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "gc.topgas.CO 18.6 under 24.0 cap",
                                "tc.dome.C 1380 under 1480 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "GC-first confirms the already-legal 4.8 t/h ore; dome-first "
                            "would have treated the titer as a hitch echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one top-gas GC slot versus the dome-TC publisher on this "
                            "smelt-reduction gasifier bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (GC 22 + dome 30): 3.08x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal ore feed.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "online top-gas CO GC, 2 kHz, 22 us jitter",
                    "dome TC, 1 kHz, 30 us jitter",
                    "ore weigh-belt (context)",
                    "char-bed DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("co_cap_pct", 24.0),
                        ("observed_co_pct", 18.6),
                        ("ore_tph", 4.8),
                        ("dome_C", 1380.0),
                        ("dome_cap_C", 1480.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Gasifier G-1 indexed on Melter-Taing MT-2; ore 4.8 t/h armed.",
                    "2. Top-gas CO 18.6 percent under 24.0; dome 1380 C under 1480.",
                    "3. Dome precursor at 0.980 ms.",
                    "4. Race window [5.040, 5.320] ms.",
                    "5. gc.topgas.CO 18.6 at 5.040 ms (winner).",
                    "6. tc.dome.C 1380 at 5.200 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 4.8 t/h ore.",
                    "8. CO stays 18.6; dome stays 1380 C.",
                    "9. Char bed stays on-spec.",
                    "10. Delayed (dwell_s=240): 4 min dust-catcher reseq.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_ore_feed"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("topgas_co_pct", 18.6),
                        ("co_cap_pct", 24.0),
                        ("ore_tph", 4.8),
                        ("dome_C", 1380.0),
                        ("dome_cap_C", 1480.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.8 t/h ore because top-gas CO 18.6 is under 24.0 and dome "
                "1380 C is under 1480.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Top-gas CO 18.6 percent won by 160 us, so the gasifier is already legal, "
                "not still climbing. Dome 1380 C is under 1480. ACCEPT the 4.8 t/h ore. A "
                "REJECT would idle a legal smelt-reduction bed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "topgas_co_pct",
                            OrderedDict(
                                [
                                    ("cap", 24.0),
                                    ("observed", 18.6),
                                    ("executed_ore_tph", 4.8),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 160),
                                    ("combined_jitter_us", 52),
                                    ("ratio", 3.08),
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
            ("name", "hold_ore_feed"),
            ("parameters", OrderedDict(params.items())),
            ("gate_effect", "ACCEPT: leave 4.8 t/h ore; CO 18.6; dome legal."),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 4.8 t/h ore. Top-gas CO 18.6 beat dome "
                "1380 C by 160 us. 4 min dust-catcher reseq (dwell_s=240) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("ore", "4.8 t/h held"),
                        ("co", "18.6 < 24.0 cap"),
                        ("gasifier", "G-1 on-spec"),
                        ("reseq", "4 min dust-catcher reseq (dwell_s=240)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Dome never approached 1480 C; top-gas CO was already under cap.",
                    "Delayed (dwell_s=240): 4 min dust-catcher reseq after the bed.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "gc.topgas.CO (5.040 ms, 18.6 percent)"),
                        ("loser", "tc.dome.C (5.200 ms, 1380 C)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Dome-first by < 160 us inside the 280 us window would have REJECTED "
                            "an already-legal ore feed. The ACCEPT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5640),
            (
                "reward_inflection_note",
                "Task and safety rise at the correct ACCEPT (5.640 ms, tick 4). The 4 min reseq "
                "is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 240),
        ]
    )
    dw = 0.28
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.topgas-gc",
            "spikenaut.policy.ore-go",
            [
                ("relay.gc.topgas", "policy.ore_go", 0.67),
                ("relay.tc.dome", "policy.ore_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the CO win as an already-legal ore feed",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("dwell_s", 240),
                ("delayed_surprise_s", 240),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", dw),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("ore_go", 40, 0.45, 250.0, dw),
                    pop("ore_hold", 32, 0.90),
                    pop("co_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r81-425"),
            (
                "title",
                "Melter-Taing MT-2 / Gasifier G-1: top-gas CO 18.6 percent beats dome 1380 C "
                "by 160 us; correct ACCEPT of an already-legal 4.8 t/h ore",
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
                    "Correct ACCEPT. CO 18.6 < 24.0; dome 1380 < 1480. "
                    "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "corex-melter-gasifier",
                    [
                        "accept",
                        "designed",
                        "co-vs-dome",
                        "already-legal-ore",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal dome temperature can lose to top-gas CO inside a "
                    "280 us window; reversing 160 us would have REJECTED an already-legal ore.",
                    5,
                ),
            ),
        ]
    )
