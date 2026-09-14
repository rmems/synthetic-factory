def lif_531_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.42
    stim = (22000, 25000)
    seed = 103531
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
    take(burst, 9, label_times=(22400, 23100, 23800))
    clamp = [(t, nid) for t, nid in picked if t < 22000][:7]
    leak = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + leak, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.pack" for t, _ in picked]
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
            ("seed", 103531),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 liquor-pump clamp bias; stim 22-25 ms is the packing collapse.",
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


def record_531():
    excerpt, extra = lif_531_excerpt()
    ticks = [
        tick(2080, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5200, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5380, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5900, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22400, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    spikes = [
        spike("pt.rec.bar", 1.040, 0.41),
        spike("uv.se.gL", 2.080, 0.58),
        spike("pt.rec.bar", 3.400, 0.50),
        spike("uv.se.gL", 5.200, 1.31),
        spike("pt.rec.bar", 5.380, 1.12),
        spike("ctrl.gate", 5.900, 0.97),
        spike("uv.se.gL", 8.100, 0.82),
        spike("pt.rec.bar", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.pack.drop", 22.400, 1.48),
        spike("ae.pack.drop", 24.100, 0.93),
        spike("pt.rec.bar", 30.200, 0.40),
        spike("uv.se.gL", 36.400, 0.55),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Selenite-Hawes SH-5 circulating-liquor UV on packed tower T-2 is 18.4 g/L SeO2 "
                "against a 12.0 g/L stop, while recycle PT sits 1.6 bar under a 3.0 bar lock. "
                "Pump-cut on the liquor win is the legal gate; riding the recycle lock would leave "
                "the 22.0 m3/h cruise untouched. Ceramic-ring AE is silent until a later bed dump.",
            ),
            ("domain", "selenium-dioxide-scrubber"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep T-2 SeO2 liquor <= 12.0 g/L and finish the scrubber pass without "
                "dumping selenium dust through a collapsed packed bed.",
            ),
            ("t0_us", 1756850400000531),
            ("gate_latency_us", 700),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.200, 5.560]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "uv.se.gL 18.4 over 12.0 cap",
                                "pt.rec.bar 1.6 with header under 3.0",
                            ],
                        ),
                        (
                            "semantics",
                            "Liquor-first latches pump clamp 22.0 -> 11.0 m3/h; header-first keeps 22.0 "
                            "on a 'still under recycle-lock' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one UV liquor-SeO2 slot versus the recycle-header PT publisher "
                            "on this packed-tower scrubber bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (liquor 28 + recycle 34): 2.90x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 22.0 m3/h; predicted next-sample 16.8 g/L "
                            "> 12.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "circulating-liquor UV SeO2 cell, 2 kHz, 28 us jitter",
                    "recycle-header PT, 1 kHz, 34 us jitter",
                    "packing AE puck (context)",
                    "make-up Coriolis (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("se_cap_gL", 12.0),
                        ("observed_se_gL", 18.4),
                        ("liquor_m3h", 22.0),
                        ("rec_bar", 1.6),
                        ("rec_cap_bar", 3.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. T-2 indexed on Selenite-Hawes SH-5; liquor 22.0 m3/h; SeO2 18.4 g/L.",
                    "2. Recycle 1.6 bar under 3.0 lock; scrubber pass armed.",
                    "3. Recycle PT precursor at 1.040 ms.",
                    "4. Race window [5.200, 5.560] ms.",
                    "5. uv.se.gL 18.4 at 5.200 ms (winner).",
                    "6. pt.rec.bar 1.6 at 5.380 ms (loser by 180 us).",
                    "7. Gate at 5.900 ms: MODIFY clamp liquor 22.0 -> 11.0 m3/h.",
                    "8. After clamp liquor 9.6 g/L <= 12.0; recycle still 1.6 bar.",
                    "9. At 22.400 ms a packing collapse dumps 0.3 t selenium dust.",
                    "10. 15 min tower isolate (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_liquor_pump"),
            (
                "parameters",
                OrderedDict(
                    [("liquor_m3h", 22.0), ("se_gL", 18.4), ("rec_bar", 1.6)]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("se_gL", 18.4),
                        ("se_cap_gL", 12.0),
                        ("predicted_unclamped_next_gL", 16.8),
                        ("liquor_m3h", 22.0),
                        ("rec_bar", 1.6),
                        ("rec_cap_bar", 3.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 22.0 m3/h liquor because recycle 1.6 bar is under 3.0, treating "
                "the 18.4 g/L SeO2 as a fogged UV cell rather than a packed-tower cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "SeO2 liquor 18.4 g/L won by 180 us, so the scrubber is off-spec, not still "
                "a recycle-header story. Holding 22.0 m3/h predicts next-sample 16.8 g/L > 12.0 "
                "cap. MODIFY: liquor 22.0 -> 11.0 m3/h. Observed after clamp 9.6 g/L <= 12.0. "
                "A full REJECT is not indicated: a clean selenium pass accepts 11.0 m3/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "se_gL",
                            OrderedDict(
                                [
                                    ("cap", 12.0),
                                    ("observed", 18.4),
                                    ("predicted_unclamped_next", 16.8),
                                    ("clamped_liquor_m3h", 11.0),
                                    ("observed_after_clamp", 9.6),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 180), ("combined_jitter_us", 62), ("ratio", 2.9)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "clamped_liquor_pump"),
            (
                "parameters",
                OrderedDict(
                    [("liquor_m3h", 11.0), ("se_gL", 9.6), ("rec_bar", 1.6)]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: liquor 22.0 -> 11.0 m3/h. Process-correct vs the 12.0 g/L SeO2 cap. "
                "Packing still collapses at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held SeO2 liquor at 9.6 g/L. At 22.400 ms a packing "
                "collapse already seated on the ceramic rings dumped 0.3 t of selenium dust. Clamp "
                "reduced dump energy; it did not prevent the collapse. Partnered negative: process "
                "heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("liquor", "clamp executed; peak 9.6 g/L <= 12.0 cap"),
                        ("packing", "collapsed at 22.400 ms; 0.3 t selenium dust"),
                        ("repair", "15 min tower isolate (abort_s=900)"),
                        ("mission", "SH-5 scrubber pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither SeO2 liquor nor recycle PT predicted the seated packing collapse; ae.pack.drop is a new channel at 22.400 ms, 16.500 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min tower isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min tower isolate after the packing collapse. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the liquor clamp completed under the 12.0 g/L "
                "cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "uv.se.gL (5.200 ms, 18.4 g/L)"),
                        ("loser", "pt.rec.bar (5.380 ms, 1.6 bar)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Header-first by < 180 us inside the 360 us window would have kept "
                            "22.0 m3/h; predicted next-sample 16.8 g/L would have missed "
                            "the 12.0 cap even without the collapse. The MODIFY is still the correct "
                            "process. The collapse is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms packing drop (tick t_us=22400), inside the "
                "42 ms raster. The correct MODIFY at 5.900 ms is in the same excerpt. Do not "
                "put inflection on the abort_s=900 isolation tick.",
            ),
            ("delayed_surprise_s", 900),
        ]
    )
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.seo2-liquor",
            "spikenaut.policy.pump-clamp",
            [
                ("relay.uv.se", "policy.pump_clamp", 0.68),
                ("relay.pt.rec", "policy.header_hold", 0.29),
                ("relay.ae.pack", "policy.pump_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at liquor win (5.200 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.400 ms packing collapse",
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
                    pop_budget("pump_clamp", 50, 0.5, 220.0, 0.36),
                    pop_budget("header_hold", 40, 0.8, 50.0, 0.36),
                    pop("pack_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r103-531",
        "Selenite-Hawes SH-5 / Scrubber T-2: SeO2 liquor beats recycle header by 180 us; correct "
        "MODIFY still eats an in-window packing collapse (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the 42 ms "
        "raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named tower isolate "
        "(abort_s=900) is not netted into task_progress.",
        ras,
        gate,
        "selenium-dioxide-scrubber",
        [
            "modify",
            "partnered-negative-total",
            "independent-lif-raster",
            "sidecar-sim-only",
            "in-window-world-charge",
            "designed",
        ],
        "A critic can see the world-charge as a LIF burst inside the raster while process "
        "heads stay honest. Credit assignment is spikes, not prose across a 15 min tower isolate.",
        1,
    )


def record_532():
    ticks = [
        tick(2240, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5600, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5780, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6120, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6460, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(660000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.co.nm3h", 1.120, 0.42),
        spike("uv.co.ppm", 2.240, 0.57),
        spike("enc.co.nm3h", 3.500, 0.49),
        spike("uv.co.ppm", 5.600, 1.29),
        spike("sp.shadow.ppm", 5.780, 1.10),
        spike("ctrl.gate", 6.120, 0.96),
        spike("uv.co.ppm", 8.400, 0.80),
        spike("enc.co.nm3h", 10.400, 0.63),
        spike("ctrl.gate", 12.600, 0.84),
        spike("uv.co.ppm", 16.600, 0.41),
        spike("sp.shadow.ppm", 22.200, 0.54),
        spike("uv.co.ppm", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(103532, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Mond decomposer D-4 at Nickcarb-Linnick NL-8 reads live off-gas CO at 184 ppm, "
                "94 above the 90 ppm cap. A leftover faceplate still prints a parked shadow "
                "setpoint of 62 ppm, tagged LEFTOVER from last campaign. Live-PV-first must cut "
                "CO 8.4 Nm3/h to 3.6; the weak supervisor binds the leftover SP as live and opens "
                "CO to 12.8 Nm3/h because 62 still looks legal.",
            ),
            ("domain", "nickel-carbonyl-decomposer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the NL-8 Mond pass with live off-gas CO <= 90 ppm, leave Ni(CO)4 feed at "
                "2.1 t/h, and keep the leftover faceplate out of the live SP slot.",
            ),
            ("t0_us", 1756850400000532),
            ("gate_latency_us", 520),
            ("race_window_us", 340),
            ("race_window_rel_ms", [5.600, 5.940]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "uv.co.ppm 184 ppm on LIVE D-4 off-gas",
                                "sp.shadow.ppm 62 ppm on LEFTOVER D4_SP.SHADOW faceplate",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-PV-first should MODIFY-cut CO on D-4; leftover-SP-as-live is a false "
                            "shadow-setpoint bind that opens CO because the parked faceplate still looks legal.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live off-gas UV slot versus the leftover faceplate publisher "
                            "on this Mond decomposer PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (live 28 + shadow 32). Order is "
                            "correctly live-PV-first. The error is leftover-SP bind: D4_SP.SHADOW is "
                            "LEFTOVER, so using it as live SP opens CO instead of cutting D-4.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live off-gas UV CO on D-4, 2 kHz, 28 us jitter, tag=D4_UV.CO status=LIVE",
                    "leftover faceplate shadow SP, 1 kHz, 32 us jitter, tag=D4_SP.SHADOW status=LEFTOVER",
                    "CO feed FT D-4 (context)",
                    "Ni(CO)4 Coriolis (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_ppm", 90.0),
                        ("live_pv_ppm", 184.0),
                        ("shadow_sp_ppm", 62.0),
                        ("live_status", "LIVE"),
                        ("faceplate_status", "LEFTOVER"),
                        ("shadow_as_live_sp", False),
                        ("co_nm3h", 8.4),
                        ("nicarbonyl_tph", 2.1),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. D-4 LIVE decomposing; off-gas 184 ppm; Ni(CO)4 2.1 t/h; CO 8.4 Nm3/h.",
                    "2. Leftover faceplate D4_SP.SHADOW still LEFTOVER at 62 ppm from last campaign.",
                    "3. CO precursor at 1.120 ms.",
                    "4. Race window [5.600, 5.940] ms.",
                    "5. uv.co.ppm 184 ppm at 5.600 ms (winner).",
                    "6. sp.shadow.ppm 62 ppm at 5.780 ms (loser by 180 us).",
                    "7. Gate at 6.120 ms: WRONG-MODIFY binds leftover shadow SP as live SP.",
                    "8. CO 8.4 -> 12.8 Nm3/h (opened); live off-gas stays 184 ppm.",
                    "9. Live 184 stays > 90; D-4 dumps carbonyl gas.",
                    "10. Delayed (abort_s=660): 11 min decomposer dump while D-4 stays over cap.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_mond_live"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("co_nm3h", 8.4),
                        ("nicarbonyl_tph", 2.1),
                        ("bind_shadow_sp", False),
                        ("shadow_as_live_sp", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_pv_ppm", 184.0),
                        ("cap_ppm", 90.0),
                        ("shadow_sp_ppm", 62.0),
                        ("live_status", "LIVE"),
                        ("faceplate_status", "LEFTOVER"),
                        ("co_nm3h", 8.4),
                        ("nicarbonyl_tph", 2.1),
                        ("correct_co_nm3h", 3.6),
                        ("correct_nicarbonyl_tph", 2.1),
                        ("correct_gate", "MODIFY"),
                        ("t_gate_us", 6120),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 660),
                        ("leftover_tag", "D4_SP.SHADOW"),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping 8.4 Nm3/h CO on D-4 because the leftover faceplate SP at "
                "62 ppm looks under the 90 cap, treating the live 184 ppm as a wet-well echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Off-gas 184 ppm exceeds the 90 ppm cap, so a cut is required, but the highlighted "
                "stem is D4_SP.SHADOW. Apply a 12.8 Nm3/h CO 'setpoint' move on the leftover "
                "faceplate (which opens). Leave LIVE D-4 at 8.4 Nm3/h unused, then overshoot to 12.8.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "offgas",
                            OrderedDict(
                                [
                                    ("cap_ppm", 90.0),
                                    ("live_pv_ppm", 184.0),
                                    ("shadow_sp_ppm", 62.0),
                                    ("executed_co_nm3h", 12.8),
                                    ("correct_co_nm3h", 3.6),
                                    ("correct_gate", "MODIFY"),
                                ]
                            ),
                        ),
                        (
                            "faceplate",
                            OrderedDict(
                                [
                                    ("t_gate_us", 6120),
                                    ("bind_shadow_sp", True),
                                    ("shadow_as_live_sp", True),
                                    ("faceplate_status", "LEFTOVER"),
                                    ("wrong_sp", True),
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
            ("name", "leftover_shadow_sp_open"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("co_nm3h", 12.8),
                        ("nicarbonyl_tph", 2.1),
                        ("bind_shadow_sp", True),
                        ("shadow_as_live_sp", True),
                        ("live_pv_ppm", 184.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / shadow-setpoint on a leftover faceplate): 12.8 Nm3/h CO OPEN "
                "applied because D4_SP.SHADOW at 62 ppm was treated as the live SP and looked legal. "
                "Routing relay.sp.shadow -> policy.shadow_open; no positive weight to policy.live_cut.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY opened CO on a Mond decomposer that needed a live-PV cut. Live "
                "184 ppm was over the 90 ppm cap at t_gate; D4_SP.SHADOW is LEFTOVER so the "
                "12.8 Nm3/h 'setpoint' opened the valve. 11 min decomposer dump (abort_s=660). Correct "
                "gate was MODIFY; cut D-4 CO 8.4 -> 3.6 Nm3/h at t_gate_us=6120 and leave the "
                "leftover faceplate unbound.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live_uv", "D-4 left illegal at 184 ppm; CO opened 8.4 -> 12.8 Nm3/h"),
                        ("leftover_sp", "D4_SP.SHADOW treated as live SP while still LEFTOVER"),
                        ("dump", "11 min carbonyl dump, D-4 over cap"),
                        ("mission", "Mond decomposition deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-PV-first was the correct order and live off-gas was over cap; the MODIFY spent that win as a leftover-SP open.",
                    "Delayed (abort_s=660): NL-8 holds 11 min while D-4 is dumped and purged; next batch 13 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY; cut live D-4 CO 8.4 -> 3.6 Nm3/h at t_gate_us=6120; bind_shadow_sp=false; shadow_as_live_sp=false; leave Ni(CO)4 at 2.1 t/h; leave D4_SP.SHADOW unbound.",
                        ),
                        ("correct_actuator", "D-4_co_direct"),
                        ("wrong_sp", "D4_SP.SHADOW_as_live"),
                        ("t_gate_us", 6120),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("co_nm3h", 12.8),
                                    ("bind_shadow_sp", True),
                                    ("shadow_as_live_sp", True),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "11 min decomposer dump (task/efficiency); live off-gas never returned under 90 ppm while the cut was spent as a leftover-SP open on D4_SP.SHADOW.",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "uv.co.ppm (5.600 ms, 184 ppm)"),
                        ("loser", "sp.shadow.ppm (5.780 ms, 62 ppm)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Shadow-first by < 180 us would still be 62 ppm on a leftover faceplate; "
                            "a correct gate binds uv.co.ppm to policy.live_cut at t_gate either "
                            "way. The wrong MODIFY spent the live win on a leftover-SP bind.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6120),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the leftover-SP bind (6.120 ms, tick 4). "
                "The 11 min decomposer dump is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 660),
        ]
    )
    ras = raster_core(
        28,
        88,
        34,
        84,
        routing(
            "thalamic-relay.mond-shadow-sp",
            "spikenaut.policy.shadow-open",
            [
                ("relay.sp.shadow", "policy.shadow_open", 0.74),
                ("relay.uv.co", "policy.shadow_open", 0.21),
            ],
            "acetylcholine",
            0.08,
            "shadow_sp_stdp; ACh tags the (wrong) leftover-faceplate-as-live open at the live UV win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 660),
                ("delayed_surprise_s", 660),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.34),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("shadow_open", 48, 0.45, 300.0, 0.34),
                    pop("live_cut", 48, 0.90),
                    pop("pair_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r103-532",
        "WRONG-MODIFY at Nickcarb-Linnick NL-8 / Decomposer D-4: live 184 ppm CO over 90 ppm cap; "
        "12.8 Nm3/h CO OPEN on leftover faceplate SP D4_SP.SHADOW (shadow-setpoint / leftover faceplate)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-modify / shadow-setpoint on a leftover faceplate. Sidecar arithmetic 184 > 90 on live "
        "off-gas is true; MODIFY bound to shadow_open. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
        ras,
        gate,
        "nickel-carbonyl-decomposer",
        [
            "modify",
            "wrong-gate",
            "shadow-setpoint",
            "leftover-faceplate",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live-PV-first race can still be a wrong gate when the "
        "MODIFY treats a leftover faceplate SP as live and opens CO. Convictable "
        "from live_pv_ppm vs cap, faceplate_status, shadow_as_live_sp, and routing without Mond physics.",
        2,
        supervisor_error_type="wrong-modify",
    )


def record_533():
    ticks = [
        tick(2736, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6840, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7020, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7640, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(7960, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("i.cell.kA", 1.360, 0.40),
        spike("ae.yf.pps", 2.736, 0.56),
        spike("i.cell.kA", 4.100, 0.48),
        spike("ae.yf.pps", 6.840, 1.34),
        spike("i.cell.kA", 7.020, 1.11),
        spike("ctrl.gate", 7.640, 0.98),
        spike("ae.yf.pps", 10.400, 0.81),
        spike("i.cell.kA", 14.800, 0.62),
        spike("ctrl.gate", 18.200, 0.84),
        spike("ae.yf.pps", 28.400, 0.52),
        spike("i.cell.kA", 36.100, 0.39),
        spike("ae.yf.pps", 42.200, 0.44),
    ]
    excerpt = independent_excerpt(103533, 120, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "On the YS-HIL stand, yttrium-fluoride cell YF-3 rattles at 64 pps against a 16 pps "
                "hush floor while rectifier current is still 28 kA under a 44 kA trip. Parking the "
                "9 MW tap is the only legal move; a kA-first close would slam power into a singing "
                "cathode. The puck outranks the Hall stack.",
            ),
            ("domain", "yttrium-fluoride-electrolyzer"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep YF-3 from dispatching a growling yttrium cathode while cell current remains under "
                "its own cap.",
            ),
            ("t0_us", 1756850400000533),
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
                                "ae.yf.pps 64 over 16 cap",
                                "i.cell.kA 28 under 44 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; current-first dispatches 9 MW on a 'kA still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one AE puck slot versus the cell-CT publisher on this HIL yttrium-fluoride bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + CT 32): 3.10x over a "
                            "2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have dispatched 9 MW into a growling yttrium cathode.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "cathode AE puck, 50 kHz, 26 us jitter",
                    "cell CT, 1 kHz, 32 us jitter",
                    "tap-to-tap encoder (context)",
                    "bath TC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 16.0),
                        ("observed_ae_pps", 64.0),
                        ("cell_kA", 28.0),
                        ("cell_cap_kA", 44.0),
                        ("proposed_mw", 9.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. YF-3 HIL indexed; 9 MW tap armed.",
                    "2. Cell 28 kA under 44; AE 64 pps over 16.",
                    "3. CT precursor at 1.360 ms.",
                    "4. Race window [6.840, 7.160] ms.",
                    "5. ae.yf.pps 64 at 6.840 ms (winner).",
                    "6. i.cell.kA 28 at 7.020 ms (loser by 180 us).",
                    "7. Gate at 7.640 ms: REJECT hold, do not dispatch.",
                    "8. Power 0 MW; current left at 28 kA.",
                    "9. Cathode inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min cell reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_tap"),
            (
                "parameters",
                OrderedDict([("mw", 9.0), ("hold", False), ("cell_kA", 28.0)]),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 64.0),
                        ("ae_cap_pps", 16.0),
                        ("cell_kA", 28.0),
                        ("cell_cap_kA", 44.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 9 MW because cell 28 kA is under 44, treating the 64 pps AE "
                "as rectifier hash rather than a growling yttrium cathode.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Cathode AE 64 pps won by 180 us, so the yttrium-fluoride cell is growling, not still "
                "a current story. 28 kA is under 44 and does not authorize dispatch. REJECT: "
                "hold power 9 -> 0 MW. A MODIFY that only trims kA would leave the growl.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ae_pps",
                            OrderedDict(
                                [
                                    ("cap", 16.0),
                                    ("observed", 64.0),
                                    ("executed_mw", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 180), ("combined_jitter_us", 58), ("ratio", 3.1)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_cell"),
            (
                "parameters",
                OrderedDict([("mw", 0.0), ("hold", True), ("cell_kA", 28.0)]),
            ),
            (
                "gate_effect",
                "REJECT: power 9 -> 0 MW. Cell current left at 28 kA under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held YF-3. AE 64 pps beat cell 28 kA by 180 us. Current was legal; "
                "the cathode was not. 8 min cell reset (abort_s=480) is delayed survey, not a "
                "process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("power", "held at 0 MW"),
                        ("current", "left 28 kA < 44 cap"),
                        ("cathode", "8 min cell reset (abort_s=480)"),
                        ("mission", "HIL slip not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Cell CT never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min cell reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.yf.pps (6.840 ms, 64 pps)"),
                        ("loser", "i.cell.kA (7.020 ms, 28 kA)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Current-first by < 180 us inside the 320 us window would have "
                            "dispatched 9 MW into a growling yttrium cathode. The REJECT is still "
                            "the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7640),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.640 ms, tick 4). The 8 min cell "
                "reset is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    ras = raster_core(
        46,
        120,
        20,
        110,
        routing(
            "thalamic-relay.yf-ae",
            "spikenaut.policy.yf-hold",
            [
                ("relay.ae.yf", "policy.yf_hold", 0.70),
                ("relay.i.cell", "policy.ka_go", 0.24),
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
            ("decision_window_ms", 0.32),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop_budget("yf_hold", 56, 0.45, 280.0, 0.32),
                    pop("ka_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r103-533",
        "Yttria-Scarth YS-HIL / Cell YF-3: cathode AE 64 pps beats cell 28 kA by 180 us; "
        "correct REJECT holds the tap",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 64 > 16 cap beats legal cell current. total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "yttrium-fluoride-electrolyzer",
        ["reject", "hil", "ae-vs-ka", "growling-cathode", "tick6-sidecar-bound"],
        "Teaches that a legal cell-current header can lose to cathode AE inside a 320 us "
        "window; reversing 180 us would have dispatched a growling yttrium-fluoride cell.",
        3,
    )


def record_534():
    ticks = [
        tick(2880, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7200, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7380, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7840, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8200, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.skin.C", 1.200, 0.40),
        spike("dens.reflux.m", 2.880, 0.55),
        spike("tc.skin.C", 4.400, 0.48),
        spike("dens.reflux.m", 7.200, 1.26),
        spike("tc.skin.C", 7.380, 1.08),
        spike("ctrl.gate", 7.840, 0.95),
        spike("dens.reflux.m", 11.200, 0.78),
        spike("tc.skin.C", 14.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("dens.reflux.m", 22.600, 0.50),
        spike("tc.skin.C", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(103534, 48, 28000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("gecl4_tph", 9.6),
            ("reflux_m", 6.8),
            ("skin_C", 58.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Germanyl-Tofts GT-6 GeCl4 rectifier R-1 nuclear gauge reads 6.8 m versus a "
                "12.0 m flood trip. Jacket skin is 58 C, 30 K shy of 88 C. The 9.6 t/h crude-GeCl4 "
                "recipe sits inside both caps; a skin-first hold would idle a dry column.",
            ),
            ("domain", "germanium-tetrachloride-rectifier"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the GT-6 rectification pass with reflux <= 12.0 m and skin <= 88 C.",
            ),
            ("t0_us", 1756850400000534),
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
                                "dens.reflux.m 6.8 under 12.0 trip",
                                "tc.skin.C 58 under 88 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Level-first confirms the already-legal 9.6 t/h crude-GeCl4 feed; skin-first "
                            "would have treated the densitometer as a flood echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one nuclear-density slot versus the skin-TC publisher on this simulated GeCl4-rectifier bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (dens 26 + TC 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed GeCl4 feed illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "nuclear densitometer on reflux drum, 26 us jitter",
                    "skin TC well, 32 us jitter",
                    "crude-GeCl4 Coriolis (context)",
                    "delta-P packing (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("reflux_cap_m", 12.0),
                        ("observed_reflux_m", 6.8),
                        ("skin_cap_C", 88.0),
                        ("observed_skin_C", 58.0),
                        ("hcl_wt_pct", 0.8),
                        ("hcl_cap_wt_pct", 2.0),
                        ("proposed_gecl4_tph", 9.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. R-1 indexed on Germanyl-Tofts GT-6; 9.6 t/h crude GeCl4 armed.",
                    "2. Caps: reflux 12.0 m, skin 88 C, HCl 2.0 wt percent.",
                    "3. Skin TC precursor at 1.200 ms.",
                    "4. Race window [7.200, 7.560] ms.",
                    "5. dens.reflux.m 6.8 at 7.200 ms (winner).",
                    "6. tc.skin.C 58 at 7.380 ms (loser by 180 us).",
                    "7. Gate at 7.840 ms: ACCEPT 9.6 t/h already legal.",
                    "8. Crude GeCl4 continues; no extra hold.",
                    "9. 6 min survey confirms reflux still under 12.0 m.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "feed_gecl4_96"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("reflux_m", 6.8),
                        ("reflux_cap_m", 12.0),
                        ("skin_C", 58.0),
                        ("skin_cap_C", 88.0),
                        ("hcl_wt_pct", 0.8),
                        ("hcl_cap_wt_pct", 2.0),
                        ("gecl4_tph", 9.6),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 9.6 t/h crude-GeCl4 feed because reflux 6.8 m is under 12.0 and skin "
                "58 C is under 88 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Reflux level 6.8 m won by 180 us and is under 12.0. Skin 58 C is under 88 C. "
                "HCl 0.8 wt percent is under 2.0. ACCEPT the already-legal GeCl4 feed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "reflux_m",
                            OrderedDict(
                                [
                                    ("cap", 12.0),
                                    ("observed", 6.8),
                                    ("executed_gecl4_tph", 9.6),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 180), ("combined_jitter_us", 58), ("ratio", 3.1)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "feed_gecl4_96"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 9.6 t/h crude GeCl4 and 6.8 m reflux unchanged. Routing relay.dens.reflux -> policy.reflux_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left R-1 on a 9.6 t/h / 6.8 m reflux crude-GeCl4 feed. Skin TC hitch did "
                "not justify a hold. 6 min survey confirmed reflux still under 12.0 m.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "still 9.6 t/h crude GeCl4"),
                        ("reflux", "6.8 m under 12.0 trip"),
                        ("skin", "58 C under 88"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Skin TC 58 C hitch is residual, not a runaway trip.",
                    "Delayed (survey_s=360): 6 min survey restacks R-1 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "dens.reflux.m (7.200 ms, 6.8 m)"),
                        ("loser", "tc.skin.C (7.380 ms, 58 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Skin-first by < 180 us would only delay confirmation. The GeCl4 feed "
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
    ras = raster_core(
        28,
        48,
        42,
        56,
        routing(
            "thalamic-relay.gecl4-level",
            "spikenaut.policy.reflux-go",
            [
                ("relay.dens.reflux", "policy.reflux_go", 0.68),
                ("relay.tc.skin", "policy.skin_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_gecl4_stdp; 5-HT tags the reflux_go bind at the densitometer win",
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
            ("decision_window_ms", 0.36),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("reflux_go", 40, 0.45, 250.0, 0.36),
                    pop("skin_hold", 32, 0.90),
                    pop("reflux_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r103-534",
        "Germanyl-Tofts GT-6 / Rectifier R-1: reflux 6.8 m beats skin 58 C by 180 us; ACCEPT "
        "already-legal 9.6 t/h crude GeCl4",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal crude-GeCl4 rectification feed. total +1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "germanium-tetrachloride-rectifier",
        [
            "accept",
            "already-legal",
            "simulated-gecl4-rectifier",
            "dens-vs-tc",
            "sidecar-convictable",
            "simulated",
        ],
        "Teaches that a reflux densitometer under trip can confirm an already-legal GeCl4 feed "
        "without a skin-TC hitch becoming a hold.",
        4,
    )


def record_535():
    ticks = [
        tick(2016, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5040, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5920, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(240000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("ir.hood.C", 0.980, 0.41),
        spike("tc.bed.C", 2.016, 0.60),
        spike("ir.hood.C", 3.200, 0.51),
        spike("tc.bed.C", 5.040, 1.30),
        spike("ir.hood.C", 5.200, 1.12),
        spike("ctrl.gate", 5.640, 0.97),
        spike("tc.bed.C", 8.100, 0.78),
        spike("ir.hood.C", 12.400, 0.62),
        spike("ctrl.gate", 16.200, 0.85),
        spike("tc.bed.C", 20.400, 0.54),
        spike("ir.hood.C", 22.800, 0.43),
    ]
    excerpt = independent_excerpt(103535, 80, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("oxalate_tph", 4.8),
            ("bed_C", 742.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Ceriax-Howk CH-2 oxalate calciner K-7 bed well is 742 C, 78 K shy of the "
                "820 C stack limit, and hood IR is 410 C versus a 560 C look. "
                "Keeping 4.8 t/h oxalate is lawful; a hood-first veto would park a quiet cerium kiln.",
            ),
            ("domain", "cerium-oxalate-calciner"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run K-7 at 4.8 t/h, keep bed <= 820 C and hood IR <= 560 C, and leave "
                "the cerium oxide pass on schedule.",
            ),
            ("t0_us", 1756850400000535),
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
                                "tc.bed.C 742 under 820 cap",
                                "ir.hood.C 410 under 560 look",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first confirms the already-legal 4.8 t/h oxalate run; hood-first would "
                            "have treated the bed TC as a hitch echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one bed-TC slot versus the hood-IR publisher on this calciner bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (TC 22 + IR 30): 3.08x over a "
                            "2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal 4.8 t/h oxalate run.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed TC well, 2 kHz, 22 us jitter",
                    "hood IR pyrometer, 1 kHz, 30 us jitter",
                    "off-gas O2 cell (context)",
                    "screw encoder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 820.0),
                        ("observed_bed_C", 742.0),
                        ("oxalate_tph", 4.8),
                        ("hood_C", 410.0),
                        ("hood_look_C", 560.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Kiln K-7 indexed on Ceriax-Howk CH-2; 4.8 t/h oxalate armed.",
                    "2. Bed 742 C under 820; hood IR 410 C under 560.",
                    "3. Hood IR precursor at 0.980 ms.",
                    "4. Race window [5.040, 5.320] ms.",
                    "5. tc.bed.C 742 at 5.040 ms (winner).",
                    "6. ir.hood.C 410 at 5.200 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 4.8 t/h.",
                    "8. Bed stays 742 C; hood stays 410 C.",
                    "9. Oxide pass on-spec.",
                    "10. Delayed (dwell_s=240): 4 min screw reseq.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_oxalate_tph"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 742.0),
                        ("bed_cap_C", 820.0),
                        ("oxalate_tph", 4.8),
                        ("hood_C", 410.0),
                        ("hood_look_C", 560.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.8 t/h because bed 742 C is under 820 and hood IR "
                "410 C is under 560.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed TC 742 C won by 160 us, so the kiln is already legal, not still climbing. "
                "Hood IR 410 C is under 560. ACCEPT the 4.8 t/h oxalate run. A REJECT would idle a legal cerium kiln.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 820.0),
                                    ("observed", 742.0),
                                    ("executed_oxalate_tph", 4.8),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 160), ("combined_jitter_us", 52), ("ratio", 3.08)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_oxalate_tph"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: leave 4.8 t/h; bed 742 C; hood IR legal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 4.8 t/h oxalate run. Bed 742 C beat hood IR "
                "410 C by 160 us. 4 min screw reseq (dwell_s=240) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "4.8 t/h held"),
                        ("bed", "742 C < 820 cap"),
                        ("kiln", "K-7 on-spec"),
                        ("reseq", "4 min screw reseq (dwell_s=240)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Hood IR never approached 560 C; bed was already under cap.",
                    "Delayed (dwell_s=240): 4 min screw reseq after oxide pass.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bed.C (5.040 ms, 742 C)"),
                        ("loser", "ir.hood.C (5.200 ms, 410 C)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Hood-first by < 160 us inside the 280 us window would have "
                            "REJECTED an already-legal 4.8 t/h oxalate run. The ACCEPT is still the "
                            "correct gate.",
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
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.ce-bed",
            "spikenaut.policy.calciner-go",
            [
                ("relay.tc.bed", "policy.calciner_go", 0.67),
                ("relay.ir.hood", "policy.calciner_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the bed-TC win as an already-legal oxalate run",
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
            ("decision_window_ms", 0.28),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("calciner_go", 40, 0.45, 250.0, 0.28),
                    pop("calciner_hold", 32, 0.90),
                    pop("bed_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r103-535",
        "Ceriax-Howk CH-2 / Calciner K-7: bed 742 C beats hood IR 410 C by 160 us; "
        "correct ACCEPT of an already-legal 4.8 t/h oxalate run",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Bed 742 < 820; hood 410 < 560. total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
        ras,
        gate,
        "cerium-oxalate-calciner",
        ["accept", "designed", "bed-vs-hood", "already-legal-feed", "tick6-sidecar-bound"],
        "Teaches that a legal hood-IR header can lose to bed TC inside a 280 us window; "
        "reversing 160 us would have REJECTED an already-legal oxalate calciner run.",
        5,
    )
