def lif_591_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.42
    stim = (22000, 25000)
    seed = 115591
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
    channels = ["lif.clamp" if t < 22000 else "lif.retort" for t, _ in picked]
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
            ("seed", 115591),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 air-cut clamp bias; stim 22-25 ms is the retort-tube leak.",
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


def record_591():
    excerpt, extra = lif_591_excerpt()
    ticks = [
        tick(2080, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5200, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5380, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5900, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22400, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    spikes = [
        spike("pt.air.bar", 1.040, 0.41),
        spike("i2.vapor.gNm3", 2.080, 0.58),
        spike("pt.air.bar", 3.400, 0.50),
        spike("i2.vapor.gNm3", 5.200, 1.31),
        spike("pt.air.bar", 5.380, 1.12),
        spike("ctrl.gate", 5.900, 0.97),
        spike("i2.vapor.gNm3", 8.100, 0.82),
        spike("pt.air.bar", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.retort.leak", 22.400, 1.48),
        spike("ae.retort.leak", 24.100, 0.93),
        spike("pt.air.bar", 30.200, 0.40),
        spike("i2.vapor.gNm3", 36.400, 0.55),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Iodprill-Healey IH-4 sublimer S-2 UV cell already sits 2.4 g/Nm3 over the 7.0 "
                "iodine-vapor stop: 9.4 g/Nm3 in condenser off-gas. Air-header PT is 2.6 bar, 1.4 shy of "
                "the 4.0 bar blower lock. UV-first clamps air 14.0 t/h down to 8.4; header-first "
                "would keep 14.0 t/h cruising. Retort AE stays mute until a later tube leak.",
            ),
            ("domain", "iodine-prill-sublimer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep S-2 I2 vapor <= 7.0 g/Nm3 and finish the prill pass without "
                "dumping iodine-wet prills through a cracked retort tube.",
            ),
            ("t0_us", 1756850400000591),
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
                                "i2.vapor.gNm3 9.4 over 7.0 cap",
                                "pt.air.bar 2.6 with header under 4.0",
                            ],
                        ),
                        (
                            "semantics",
                            "Vapor-first latches air clamp 14.0 -> 8.4 t/h; header-first keeps 14.0 "
                            "on a 'still under blower-cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one UV-absorption iodine-vapor slot versus the air-header PT publisher "
                            "on this iodine-prill sublimer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (vapor 28 + air 34): 2.90x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 14.0 t/h; predicted next-sample 8.2 g/Nm3 "
                            "> 7.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "off-gas UV I2 vapor cell, 2 kHz, 28 us jitter",
                    "air-header PT, 1 kHz, 34 us jitter",
                    "retort-tube AE puck (context)",
                    "prill Coriolis (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("i2_cap_gNm3", 7.0),
                        ("observed_i2_gNm3", 9.4),
                        ("air_tph", 14.0),
                        ("air_bar", 2.6),
                        ("air_cap_bar", 4.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. S-2 indexed on Iodprill-Healey IH-4; air 14.0 t/h; I2 vapor 9.4 g/Nm3.",
                    "2. Header 2.6 bar under 4.0 cap; prill pass armed.",
                    "3. Air header PT precursor at 1.040 ms.",
                    "4. Race window [5.200, 5.560] ms.",
                    "5. i2.vapor.gNm3 9.4 at 5.200 ms (winner).",
                    "6. pt.air.bar 2.6 at 5.380 ms (loser by 180 us).",
                    "7. Gate at 5.900 ms: MODIFY clamp air 14.0 -> 8.4 t/h.",
                    "8. After clamp vapor 6.4 g/Nm3 <= 7.0; header still 2.6 bar.",
                    "9. At 22.400 ms a retort-tube leak dumps 0.3 t I2-wet prills.",
                    "10. 15 min retort isolate (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_air_flow"),
            (
                "parameters",
                OrderedDict(
                    [("air_tph", 14.0), ("i2_gNm3", 9.4), ("air_bar", 2.6)]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("i2_gNm3", 9.4),
                        ("i2_cap_gNm3", 7.0),
                        ("predicted_unclamped_next_gNm3", 8.2),
                        ("air_tph", 14.0),
                        ("air_bar", 2.6),
                        ("air_cap_bar", 4.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 14.0 t/h air because header 2.6 bar is under 4.0, treating "
                "the 9.4 g/Nm3 vapor as a fogged UV cell rather than a condenser-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "I2 vapor 9.4 g/Nm3 won by 180 us, so the sublimer is off-spec, not still "
                "an air-header story. Holding 14.0 t/h air predicts next-sample 8.2 g/Nm3 > 7.0 "
                "cap. MODIFY: air 14.0 -> 8.4 t/h. Observed after clamp 6.4 g/Nm3 <= 7.0. "
                "A full REJECT is not indicated: a clean iodine-prill pass accepts 8.4 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "i2_gNm3",
                            OrderedDict(
                                [
                                    ("cap", 7.0),
                                    ("observed", 9.4),
                                    ("predicted_unclamped_next", 8.2),
                                    ("clamped_air_tph", 8.4),
                                    ("observed_after_clamp", 6.4),
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
            ("name", "clamped_air_flow"),
            (
                "parameters",
                OrderedDict(
                    [("air_tph", 8.4), ("i2_gNm3", 6.4), ("air_bar", 2.6)]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: air 14.0 -> 8.4 t/h. Process-correct vs the 7.0 g/Nm3 vapor cap. "
                "Retort still leaks at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held I2 vapor at 6.4 g/Nm3. At 22.400 ms a retort-tube "
                "leak already seated on S-2 dumped 0.3 t of I2-wet prills. Clamp reduced dump "
                "energy; it did not prevent the leak. Partnered negative: process heads stay "
                "honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("offgas", "clamp executed; peak 6.4 g/Nm3 <= 7.0 cap"),
                        ("retort", "leaked at 22.400 ms; 0.3 t I2-wet prills"),
                        ("repair", "15 min retort isolate (abort_s=900)"),
                        ("mission", "IH-4 sublimer pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither I2 vapor nor air PT predicted the seated retort-tube leak; ae.retort.leak is a new channel at 22.400 ms, 16.500 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min retort isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min retort isolate after the tube leak. Safety head -0.60 prices the leak; "
                "task_progress stays +0.32 because the air clamp completed under the 7.0 g/Nm3 "
                "cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "i2.vapor.gNm3 (5.200 ms, 9.4 g/Nm3)"),
                        ("loser", "pt.air.bar (5.380 ms, 2.6 bar)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Header-first by < 180 us inside the 360 us window would have kept "
                            "14.0 t/h; predicted next-sample 8.2 g/Nm3 would have missed "
                            "the 7.0 cap even without the leak. The MODIFY is still the correct "
                            "process. The leak is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms retort-tube leak (tick t_us=22400), inside the "
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
            "thalamic-relay.i2-vapor",
            "spikenaut.policy.air-clamp",
            [
                ("relay.i2.vapor", "policy.air_clamp", 0.68),
                ("relay.pt.air", "policy.header_hold", 0.29),
                ("relay.ae.retort", "policy.air_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at vapor win (5.200 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.400 ms retort-tube leak",
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
                    pop_budget("air_clamp", 50, 0.5, 220.0, 0.36),
                    pop_budget("header_hold", 40, 0.8, 50.0, 0.36),
                    pop("retort_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r115-591",
        "Iodprill-Healey IH-4 / Sublimer S-2: I2 vapor beats air header by 180 us; correct "
        "MODIFY still eats an in-window retort-tube leak (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the 42 ms "
        "raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named retort isolate "
        "(abort_s=900) is not netted into task_progress.",
        ras,
        gate,
        "iodine-prill-sublimer",
        [
            "modify",
            "partnered-negative-total",
            "independent-lif-raster",
            "sidecar-sim-only",
            "in-window-world-charge",
            "designed",
        ],
        "A critic can see the world-charge as a LIF burst inside the raster while process "
        "heads stay honest. Credit assignment is spikes, not prose across a 15 min retort isolate.",
        1,
    )


def record_592():
    ticks = [
        tick(2240, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5600, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5780, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6120, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6460, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("ft.f2.kgh", 1.120, 0.42),
        spike("enc.hf.ppm", 2.240, 0.57),
        spike("ft.f2.kgh", 3.500, 0.49),
        spike("enc.hf.ppm", 5.600, 1.29),
        spike("zt.split.pct", 5.780, 1.10),
        spike("ctrl.gate", 6.120, 0.96),
        spike("enc.hf.ppm", 8.400, 0.80),
        spike("ft.f2.kgh", 10.400, 0.63),
        spike("ctrl.gate", 12.600, 0.84),
        spike("enc.hf.ppm", 16.600, 0.41),
        spike("zt.split.pct", 22.200, 0.54),
        spike("enc.hf.ppm", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(115592, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Bromtrif-Ramsgill BR-9 cell C-6 is already over the published HF cap: live "
                "encoder 18.4 ppm versus 8.0. Split-range FV-22 sits at 62 percent, on the high "
                "half (KOH quench). Live-first must cut F2 4.8 to 2.0 kg/h; the weak supervisor "
                "inverts the 4 percent switch hysteresis and opens F2 4.8 to 7.2 kg/h.",
            ),
            ("domain", "bromine-trifluoride-cell"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the BR-9 BrF3 pass with live HF <= 8.0 ppm, leave KOH quench on the high "
                "half, and keep inverted hysteresis out of the live slot.",
            ),
            ("t0_us", 1756850400000592),
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
                                "enc.hf.ppm 18.4 ppm on LIVE C-6",
                                "zt.split.pct 62 percent high-half stem",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-encoder-first should MODIFY-cut F2 on C-6; inverted-hysteresis "
                            "treats 62 percent as still on the N2 half and opens F2 because the "
                            "switch has not 'latched' quench.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live HF-encoder slot versus the split-range stem publisher "
                            "on this BrF3 cell PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (live 28 + stem 32). Order is "
                            "correctly live-encoder-first. The error is inverted hysteresis: stem "
                            "is already 62 percent on the high half, so chasing the low half opens "
                            "F2 instead of cutting under 8.0 ppm.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live HF encoder on C-6, 2 kHz, 28 us jitter, tag=C6_HF.PV status=LIVE",
                    "split-range stem ZT, 1 kHz, 32 us jitter, tag=FV22.ZT status=LIVE",
                    "F2 feed Coriolis (context)",
                    "KOH quench FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_ppm", 8.0),
                        ("live_hf_ppm", 18.4),
                        ("split_pos_pct", 62.0),
                        ("split_switch_pct", 50.0),
                        ("hyst_band_pct", 4.0),
                        ("hyst_polarity", "inverted"),
                        ("live_status", "LIVE"),
                        ("f2_kgh", 4.8),
                        ("koh_m3h", 3.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. C-6 LIVE fluorinating; HF 18.4 ppm; F2 4.8 kg/h; stem 62 percent.",
                    "2. Split-range: 0-50 N2 sweep, 50-100 KOH quench; hysteresis should be high-exclusive.",
                    "3. F2 precursor at 1.120 ms.",
                    "4. Race window [5.600, 5.940] ms.",
                    "5. enc.hf.ppm 18.4 at 5.600 ms (winner).",
                    "6. zt.split.pct 62 at 5.780 ms (loser by 180 us).",
                    "7. Gate at 6.120 ms: WRONG-MODIFY binds inverted hysteresis as live switch.",
                    "8. F2 4.8 -> 7.2 kg/h (opened); live HF stays 18.4 over 8.0.",
                    "9. Live 18.4 stays > 8.0; C-6 dumps BrF3 off-gas.",
                    "10. Delayed (abort_s=720): 12 min F2 dump while C-6 stays over cap.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_brf3_live"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("f2_kgh", 4.8),
                        ("koh_m3h", 3.6),
                        ("bind_inverted_hysteresis", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_hf_ppm", 18.4),
                        ("cap_ppm", 8.0),
                        ("split_pos_pct", 62.0),
                        ("split_switch_pct", 50.0),
                        ("hyst_band_pct", 4.0),
                        ("hyst_polarity", "inverted"),
                        ("live_status", "LIVE"),
                        ("f2_kgh", 4.8),
                        ("koh_m3h", 3.6),
                        ("correct_f2_kgh", 2.0),
                        ("correct_koh_m3h", 3.6),
                        ("correct_gate", "MODIFY"),
                        ("t_gate_us", 6120),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 720),
                        ("split_tag", "FV22.ZT"),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping 4.8 kg/h F2 on C-6 because inverted hysteresis still "
                "paints the 62 percent stem as the N2 half, treating the 8.0 ppm cap as a stale bar.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "HF 18.4 ppm exceeds the 8.0 cap, so a cut is required, but the highlighted "
                "stem is FV22.ZT at 62 percent with inverted 4 percent hysteresis. Apply a 7.2 "
                "kg/h 'chase' on the low half (which opens F2). Leave LIVE C-6 unused, then "
                "overshoot to 7.2.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "hf",
                            OrderedDict(
                                [
                                    ("cap_ppm", 8.0),
                                    ("live_hf_ppm", 18.4),
                                    ("split_pos_pct", 62.0),
                                    ("executed_f2_kgh", 7.2),
                                    ("correct_f2_kgh", 2.0),
                                    ("correct_gate", "MODIFY"),
                                ]
                            ),
                        ),
                        (
                            "hysteresis",
                            OrderedDict(
                                [
                                    ("t_gate_us", 6120),
                                    ("bind_inverted_hysteresis", True),
                                    ("hyst_polarity", "inverted"),
                                    ("wrong_pair", True),
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
            ("name", "inverted_hysteresis_open"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("f2_kgh", 7.2),
                        ("koh_m3h", 3.6),
                        ("bind_inverted_hysteresis", True),
                        ("live_hf_ppm", 18.4),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / wrong-hysteresis on a split-range valve): 7.2 kg/h F2 "
                "OPEN applied because inverted 4 percent hysteresis treated 62 percent as the "
                "N2 half. Routing relay.zt.split -> policy.hyst_open; no positive weight to "
                "policy.live_cut.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY opened F2 on a BrF3 cell that needed a live cut. Live 18.4 ppm "
                "was over the 8.0 cap at t_gate; stem 62 percent is already on the quench half "
                "so the 7.2 kg/h 'chase' opened the F2 valve. 12 min F2 dump (abort_s=720). "
                "Correct gate was MODIFY; cut C-6 F2 4.8 -> 2.0 kg/h at t_gate_us=6120 and leave "
                "hysteresis high-exclusive.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live_pv", "C-6 left illegal at 18.4 ppm; F2 opened 4.8 -> 7.2"),
                        ("split", "FV22.ZT treated as N2 half while already 62 percent quench"),
                        ("dump", "12 min BrF3 off-gas dump, C-6 over cap"),
                        ("mission", "BrF3 fluorination deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-encoder-first was the correct order and live HF was over cap; the MODIFY spent that win as an inverted-hysteresis chase.",
                    "Delayed (abort_s=720): BR-9 holds 12 min while C-6 is dumped and recharged; next batch 14 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY; cut live C-6 F2 4.8 -> 2.0 kg/h at t_gate_us=6120; bind_inverted_hysteresis=false; leave KOH at 3.6 m3/h; leave FV22.ZT as high-half quench.",
                        ),
                        ("correct_actuator", "C-6_F2_direct"),
                        ("wrong_pair", "FV22.ZT_inverted_hysteresis"),
                        ("t_gate_us", 6120),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("f2_kgh", 7.2),
                                    ("bind_inverted_hysteresis", True),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min F2 dump (task/efficiency); live HF never returned under 8.0 ppm while the cut was spent as an inverted-hysteresis chase on FV22.ZT.",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "enc.hf.ppm (5.600 ms, 18.4 ppm)"),
                        ("loser", "zt.split.pct (5.780 ms, 62 percent high-half stem)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Stem-first by < 180 us would still be 62 percent on the quench half; "
                            "a correct gate binds enc.hf.ppm to policy.live_cut at t_gate either "
                            "way. The wrong MODIFY spent the live win on an inverted-hysteresis chase.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6120),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the inverted-hysteresis bind (6.120 ms, tick 4). "
                "The 12 min F2 dump is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 720),
        ]
    )
    ras = raster_core(
        28,
        88,
        34,
        84,
        routing(
            "thalamic-relay.brf3-hysteresis",
            "spikenaut.policy.hyst-open",
            [
                ("relay.zt.split", "policy.hyst_open", 0.74),
                ("relay.enc.hf", "policy.hyst_open", 0.21),
            ],
            "acetylcholine",
            0.08,
            "hysteresis_stdp; ACh tags the (wrong) inverted-hysteresis chase at the live encoder win",
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
            ("decision_window_ms", 0.34),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("hyst_open", 48, 0.45, 300.0, 0.34),
                    pop("live_cut", 48, 0.90),
                    pop("pair_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r115-592",
        "WRONG-MODIFY at Bromtrif-Ramsgill BR-9 / Cell C-6: live 18.4 ppm over 8.0 cap; "
        "7.2 kg/h F2 OPEN on inverted 4 percent split-range hysteresis (wrong-hysteresis / split-range)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-modify / wrong-hysteresis on a split-range valve. Sidecar arithmetic 18.4 > 8.0 on live "
        "HF is true; MODIFY bound to hyst_open. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
        ras,
        gate,
        "bromine-trifluoride-cell",
        [
            "modify",
            "wrong-gate",
            "wrong-hysteresis",
            "split-range",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live-encoder-first race can still be a wrong gate when the "
        "MODIFY inverts split-range hysteresis and opens F2. Convictable from live_hf_ppm vs cap, "
        "split_pos_pct, hyst_polarity, bind_inverted_hysteresis, and routing without BrF3 physics.",
        2,
        supervisor_error_type="wrong-modify",
    )


def record_593():
    ticks = [
        tick(2736, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6840, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7020, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7640, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(7960, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("p.melt.MW", 1.360, 0.40),
        spike("ae.ir.pps", 2.736, 0.56),
        spike("p.melt.MW", 4.100, 0.48),
        spike("ae.ir.pps", 6.840, 1.34),
        spike("p.melt.MW", 7.020, 1.11),
        spike("ctrl.gate", 7.640, 0.98),
        spike("ae.ir.pps", 10.400, 0.81),
        spike("p.melt.MW", 14.800, 0.62),
        spike("ctrl.gate", 18.200, 0.84),
        spike("ae.ir.pps", 28.400, 0.52),
        spike("p.melt.MW", 36.100, 0.39),
        spike("ae.ir.pps", 42.200, 0.44),
    ]
    excerpt = independent_excerpt(115593, 120, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Iridyl-Pateley IP-HIL lining AE puck on crucible IR-2 is 56 pps, fourfold the 14 pps "
                "quiet band. Melt CT remains 3.1 MW, 2.1 shy of the 5.2 MW trip. Legal action "
                "parks the 3.8 MW tap at zero; a power-first dispatch would energize a noisy "
                "iridium shell. Melt kW meters do not outrank the puck.",
            ),
            ("domain", "iridium-crucible-melt"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep IR-2 from dispatching a growling lining while melt power remains under "
                "its own cap.",
            ),
            ("t0_us", 1756850400000593),
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
                                "ae.ir.pps 56 over 14 cap",
                                "p.melt.MW 3.1 under 5.2 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; power-first dispatches 3.8 MW on a 'MW still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one AE puck slot versus the melt-CT publisher on this HIL iridium-crucible bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + CT 32): 3.10x over a "
                            "2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have dispatched 3.8 MW into a growling lining.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "lining AE puck, 50 kHz, 26 us jitter",
                    "melt CT, 1 kHz, 32 us jitter",
                    "Ir-charge encoder (context)",
                    "crucible wall TC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 14.0),
                        ("observed_ae_pps", 56.0),
                        ("melt_MW", 3.1),
                        ("melt_cap_MW", 5.2),
                        ("proposed_mw", 3.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. IR-2 HIL indexed; 3.8 MW tap armed.",
                    "2. Melt 3.1 MW under 5.2; AE 56 pps over 14.",
                    "3. CT precursor at 1.360 ms.",
                    "4. Race window [6.840, 7.160] ms.",
                    "5. ae.ir.pps 56 at 6.840 ms (winner).",
                    "6. p.melt.MW 3.1 at 7.020 ms (loser by 180 us).",
                    "7. Gate at 7.640 ms: REJECT hold, do not dispatch.",
                    "8. Power 0 MW; current left at 3.1 MW.",
                    "9. Shell inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min crucible reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_crucible"),
            (
                "parameters",
                OrderedDict([("mw", 3.8), ("hold", False), ("melt_MW", 3.1)]),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 56.0),
                        ("ae_cap_pps", 14.0),
                        ("melt_MW", 3.1),
                        ("melt_cap_MW", 5.2),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 3.8 MW because melt 3.1 MW is under 5.2, treating the 56 pps AE "
                "as rectifier hash rather than a growling lining.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Lining AE 56 pps won by 180 us, so the iridium crucible is growling, not still "
                "a current story. 3.1 MW is under 5.2 and does not authorize dispatch. REJECT: "
                "hold power 3.8 -> 0 MW. A MODIFY that only trims MW would leave the growl.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ae_pps",
                            OrderedDict(
                                [
                                    ("cap", 14.0),
                                    ("observed", 56.0),
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
            ("name", "hold_crucible"),
            (
                "parameters",
                OrderedDict([("mw", 0.0), ("hold", True), ("melt_MW", 3.1)]),
            ),
            (
                "gate_effect",
                "REJECT: power 3.8 -> 0 MW. Melt left at 3.1 MW under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held IR-2. AE 56 pps beat melt 3.1 MW by 180 us. Power was legal; "
                "the lining was not. 8 min crucible reset (abort_s=480) is delayed survey, not a "
                "process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("power", "held at 0 MW"),
                        ("current", "left 3.1 MW < 5.2 cap"),
                        ("lining", "8 min crucible reset (abort_s=480)"),
                        ("mission", "HIL crucible not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Melt CT never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min crucible reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.ir.pps (6.840 ms, 56 pps)"),
                        ("loser", "p.melt.MW (7.020 ms, 3.1 MW)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Power-first by < 180 us inside the 320 us window would have "
                            "dispatched 3.8 MW into a growling lining. The REJECT is still "
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
            "thalamic-relay.ir-ae",
            "spikenaut.policy.ir-hold",
            [
                ("relay.ae.ir", "policy.ir_hold", 0.70),
                ("relay.p.melt", "policy.mw_go", 0.24),
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
                    pop_budget("ir_hold", 56, 0.45, 280.0, 0.32),
                    pop("mw_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r115-593",
        "Iridyl-Pateley IP-HIL / Crucible IR-2: lining AE 56 pps beats melt 3.1 MW by 180 us; "
        "correct REJECT holds the tap",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 56 > 14 cap beats legal melt power. total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "iridium-crucible-melt",
        ["reject", "hil", "ae-vs-mw", "growling-lining", "tick6-sidecar-bound"],
        "Teaches that a legal melt-power header can lose to lining AE inside a 320 us "
        "window; reversing 180 us would have dispatched a growling iridium crucible.",
        3,
    )


def record_594():
    ticks = [
        tick(2880, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7200, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7380, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7840, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8200, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.jacket.C", 1.200, 0.40),
        spike("conv.epdm.pct", 2.880, 0.55),
        spike("tc.jacket.C", 4.400, 0.48),
        spike("conv.epdm.pct", 7.200, 1.26),
        spike("tc.jacket.C", 7.380, 1.08),
        spike("ctrl.gate", 7.840, 0.95),
        spike("conv.epdm.pct", 11.200, 0.78),
        spike("tc.jacket.C", 14.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("conv.epdm.pct", 22.600, 0.50),
        spike("tc.jacket.C", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(115594, 48, 28000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("epdm_tph", 5.4),
            ("conv_pct", 71.0),
            ("jacket_C", 48.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Epdmsol-Askrigg EA-3 kettle K-5 NIR converter already sits at 71 percent versus an "
                "88 percent gel trip. Jacket skin is 48 C, 34 K shy of 82 C. The 5.4 t/h EPDM-solution "
                "recipe sits inside both caps; a jacket-first hold would idle a quiet terpolymer train.",
            ),
            ("domain", "epdm-solution-polymerizer"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the EA-3 solution pass with conversion <= 88 percent and jacket <= 82 C.",
            ),
            ("t0_us", 1756850400000594),
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
                                "conv.epdm.pct 71 under 88 trip",
                                "tc.jacket.C 48 under 82 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Conversion-first confirms the already-legal 5.4 t/h EPDM feed; jacket-first "
                            "would have treated the NIR as a gel echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one NIR-conversion slot versus the jacket-TC publisher on this simulated EPDM-solution bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (NIR 26 + TC 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed EPDM feed illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "NIR converter on EPDM kettle, 26 us jitter",
                    "jacket TC well, 32 us jitter",
                    "ethylene/propylene Coriolis (context)",
                    "delta-P kettle (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("conv_cap_pct", 88.0),
                        ("observed_conv_pct", 71.0),
                        ("jacket_cap_C", 82.0),
                        ("observed_jacket_C", 48.0),
                        ("en_wt_pct", 4.2),
                        ("en_cap_wt_pct", 8.0),
                        ("proposed_epdm_tph", 5.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. K-5 indexed on Epdmsol-Askrigg EA-3; 5.4 t/h EPDM armed.",
                    "2. Caps: conversion 88 percent, skin 82 C, EN 8.0 wt percent.",
                    "3. Jacket TC precursor at 1.200 ms.",
                    "4. Race window [7.200, 7.560] ms.",
                    "5. conv.epdm.pct 71 at 7.200 ms (winner).",
                    "6. tc.jacket.C 48 at 7.380 ms (loser by 180 us).",
                    "7. Gate at 7.840 ms: ACCEPT 5.4 t/h already legal.",
                    "8. EPDM continues; no extra hold.",
                    "9. 6 min survey confirms conversion still under 88 percent.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "feed_epdm_54"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("conv_pct", 71.0),
                        ("conv_cap_pct", 88.0),
                        ("jacket_C", 48.0),
                        ("jacket_cap_C", 82.0),
                        ("en_wt_pct", 4.2),
                        ("en_cap_wt_pct", 8.0),
                        ("epdm_tph", 5.4),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 5.4 t/h EPDM-solution feed because conversion 71 percent is under 88 and jacket "
                "48 C is under 82 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Conversion 71 percent won by 180 us and is under 88. Jacket 48 C is under 82 C. "
                "EN 4.2 wt percent is under 8.0. ACCEPT the already-legal EPDM feed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "conv_pct",
                            OrderedDict(
                                [
                                    ("cap", 88.0),
                                    ("observed", 71.0),
                                    ("executed_epdm_tph", 5.4),
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
            ("name", "feed_epdm_54"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 5.4 t/h EPDM and 71 percent conversion unchanged. Routing relay.conv.epdm -> policy.epdm_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left K-5 on a 5.4 t/h / 71 percent conversion EPDM feed. Jacket TC hitch did "
                "not justify a hold. 6 min survey confirmed conversion still under 88 percent.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "still 5.4 t/h EPDM"),
                        ("conversion", "71 percent under 88 trip"),
                        ("jacket", "48 C under 82"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Jacket TC 48 C hitch is residual, not a runaway trip.",
                    "Delayed (survey_s=360): 6 min survey restacks K-5 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "conv.epdm.pct (7.200 ms, 71 percent)"),
                        ("loser", "tc.jacket.C (7.380 ms, 48 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Jacket-first by < 180 us would only delay confirmation. The EPDM feed "
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
            "thalamic-relay.epdm-conv",
            "spikenaut.policy.epdm-go",
            [
                ("relay.conv.epdm", "policy.epdm_go", 0.68),
                ("relay.tc.jacket", "policy.jacket_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_epdm_stdp; 5-HT tags the epdm_go bind at the NIR win",
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
                    pop_budget("epdm_go", 40, 0.45, 250.0, 0.36),
                    pop("jacket_hold", 32, 0.90),
                    pop("epdm_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r115-594",
        "Epdmsol-Askrigg EA-3 / Kettle K-5: conversion 71 percent beats jacket 48 C by 180 us; ACCEPT "
        "already-legal 5.4 t/h EPDM",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal EPDM-solution feed. total +1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "epdm-solution-polymerizer",
        [
            "accept",
            "already-legal",
            "simulated-epdm-kettle",
            "conversion-vs-jacket",
            "sidecar-convictable",
            "simulated",
        ],
        "Teaches that a NIR converter under trip can confirm an already-legal EPDM feed "
        "without a jacket-TC hitch becoming a hold.",
        4,
    )


def record_595():
    ticks = [
        tick(2016, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5040, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5920, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(240000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.so3.tph", 0.980, 0.41),
        spike("tc.bed.C", 2.016, 0.60),
        spike("ft.so3.tph", 3.200, 0.51),
        spike("tc.bed.C", 5.040, 1.30),
        spike("ft.so3.tph", 5.200, 1.12),
        spike("ctrl.gate", 5.640, 0.97),
        spike("tc.bed.C", 8.100, 0.78),
        spike("ft.so3.tph", 12.400, 0.62),
        spike("ctrl.gate", 16.200, 0.85),
        spike("tc.bed.C", 20.400, 0.54),
        spike("ft.so3.tph", 22.800, 0.43),
    ]
    excerpt = independent_excerpt(115595, 80, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("bps_tph", 4.1),
            ("bed_C", 164.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Bpsreact-Thirsk BT-7 BPS reactor R-1 bed well is 164 C, 34 K shy of the "
                "198 C stack limit, and SO3 feed is 1.12 t/h versus a 1.80 t/h trip. "
                "Keeping 4.1 t/h phenol is lawful; an SO3-first veto would idle a quiet BPS stack.",
            ),
            ("domain", "bisphenol-s-reactor"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run R-1 at 4.1 t/h, keep bed <= 198 C and SO3 <= 1.80 t/h, and leave "
                "the sulfonation on schedule.",
            ),
            ("t0_us", 1756850400000595),
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
                                "tc.bed.C 164 under 198 cap",
                                "ft.so3.tph 1.12 under 1.80 trip",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first confirms the already-legal 4.1 t/h run; SO3-first would "
                            "have treated the bed TC as a hitch echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one bed-TC slot versus the SO3 Coriolis publisher on this BPS reactor bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (TC 22 + FT 30): 3.08x over a "
                            "2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal 4.1 t/h run.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed TC well, 2 kHz, 22 us jitter",
                    "SO3 in-line Coriolis, 1 kHz, 30 us jitter",
                    "reboiler PT (context)",
                    "phenol feed (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 198.0),
                        ("observed_bed_C", 164.0),
                        ("bps_tph", 4.1),
                        ("so3_tph", 1.12),
                        ("so3_cap_tph", 1.80),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Reactor R-1 indexed on Bpsreact-Thirsk BT-7; 4.1 t/h armed.",
                    "2. Bed 164 C under 198; SO3 1.12 t/h under 1.80.",
                    "3. SO3 precursor at 0.980 ms.",
                    "4. Race window [5.040, 5.320] ms.",
                    "5. tc.bed.C 164 at 5.040 ms (winner).",
                    "6. ft.so3.tph 1.12 at 5.200 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 4.1 t/h.",
                    "8. Bed stays 164 C; SO3 stays 1.12 t/h.",
                    "9. BPS reactor on-spec.",
                    "10. Delayed (dwell_s=240): 4 min reboiler reseq.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_bps_tph"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 164.0),
                        ("bed_cap_C", 198.0),
                        ("bps_tph", 4.1),
                        ("so3_tph", 1.12),
                        ("so3_cap_tph", 1.80),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.1 t/h because bed 164 C is under 198 and SO3 "
                "1.12 t/h is under 1.80.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed TC 164 C won by 160 us, so the reactor is already legal, not still climbing. "
                "SO3 1.12 t/h is under 1.80. ACCEPT the 4.1 t/h run. A REJECT would idle a legal BPS reactor.",
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
                                    ("observed", 164.0),
                                    ("executed_bps_tph", 4.1),
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
            ("name", "hold_bps_tph"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: leave 4.1 t/h; bed 164 C; SO3 legal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 4.1 t/h BPS run. Bed 164 C beat SO3 "
                "1.12 t/h by 160 us. 4 min reboiler reseq (dwell_s=240) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("growth", "4.1 t/h held"),
                        ("bed", "164 C < 198 cap"),
                        ("chamber", "R-1 on-spec"),
                        ("reseq", "4 min reboiler reseq (dwell_s=240)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "SO3 never approached 1.80 t/h; bed was already under cap.",
                    "Delayed (dwell_s=240): 4 min reboiler reseq after monolayer.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bed.C (5.040 ms, 164 C)"),
                        ("loser", "ft.so3.tph (5.200 ms, 1.12 t/h)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "SO3-first by < 160 us inside the 280 us window would have "
                            "REJECTED an already-legal 4.1 t/h run. The ACCEPT is still the "
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
            "thalamic-relay.bps-bed",
            "spikenaut.policy.bps-go",
            [
                ("relay.tc.bed", "policy.bps_go", 0.67),
                ("relay.ft.so3", "policy.bps_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the bed-TC win as an already-legal BPS run",
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
                    pop_budget("bps_go", 40, 0.45, 250.0, 0.28),
                    pop("bps_hold", 32, 0.90),
                    pop("bed_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r115-595",
        "Bpsreact-Thirsk BT-7 / Reactor R-1: bed 164 C beats SO3 1.12 t/h by 160 us; ACCEPT "
        "already-legal 4.1 t/h BPS",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal BPS sulfonation feed. total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
        ras,
        gate,
        "bisphenol-s-reactor",
        [
            "accept",
            "already-legal",
            "designed-bps-reactor",
            "bed-vs-so3",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches that a bed TC under trip can confirm an already-legal BPS feed "
        "without an SO3 hitch becoming a hold.",
        5,
    )
