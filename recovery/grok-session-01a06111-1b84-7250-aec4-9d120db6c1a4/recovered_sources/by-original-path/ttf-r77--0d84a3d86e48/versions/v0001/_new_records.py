def lif_401_excerpt():
    n = 78
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.42
    stim = (22000, 25000)
    seed = 77401
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
    leak = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + leak, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.retort" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 78),
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
            ("seed", 77401),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 kiln-RPM clamp bias; stim 22-25 ms is the retort-tube leak.",
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


def record_401():
    excerpt, extra = lif_401_excerpt()
    ticks = [
        tick(2144, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5360, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5540, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6080, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22600, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Steam-activation kiln SK-7 on Steamchar-Riggs SR-3 is dumping 194 ppm CO off-gas "
                "while kiln RPM still sits a legal 1.7 under 2.5. CO-first clamps RPM 1.7 -> 1.05; "
                "speed-first would keep cruise because brick 718 C is still under the 770 C shell "
                "cap. A retort-tube leak already seated on the steam chest does not appear on "
                "CO or RPM until the AE dump.",
            ),
            ("domain", "steam-activated-carbon-kiln"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep SK-7 off-gas CO <= 95 ppm and finish the steam activation without dumping "
                "char through a torn retort tube.",
            ),
            ("t0_us", 1756850400000401),
            ("gate_latency_us", 720),
            ("race_window_us", 380),
            ("race_window_rel_ms", [5.360, 5.740]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "co.offgas.ppm 194 over 95 cap",
                                "enc.kiln.rpm 1.7 with brick 718 under 770",
                            ],
                        ),
                        (
                            "semantics",
                            "CO-first latches RPM clamp 1.7 -> 1.05; speed-first keeps 1.7 on a "
                            "'still under brick-shell cap' model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one NDIR CO slot versus the kiln-encoder publisher on this "
                            "steam-activation kiln bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 64 us (CO 30 + RPM 34): 2.81x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 380 us "
                            "window would have kept 1.7 rpm; predicted next-sample 148 ppm "
                            "> 95 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "off-gas NDIR CO cell, 2 kHz, 30 us jitter",
                    "kiln encoder + brick TC, 1 kHz, 34 us jitter",
                    "steam-chest AE puck (context)",
                    "char screw tach (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("co_cap_ppm", 95.0),
                        ("observed_co_ppm", 194.0),
                        ("kiln_rpm", 1.7),
                        ("brick_C", 718.0),
                        ("brick_cap_C", 770.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. SK-7 indexed on Steamchar-Riggs SR-3; kiln 1.7 rpm; off-gas CO 194 ppm.",
                    "2. Brick 718 C under 770 C cap; activation armed.",
                    "3. Encoder precursor at 1.200 ms.",
                    "4. Race window [5.360, 5.740] ms.",
                    "5. co.offgas.ppm 194 at 5.360 ms (winner).",
                    "6. enc.kiln.rpm 1.7 at 5.540 ms (loser by 180 us).",
                    "7. Gate at 6.080 ms: MODIFY clamp 1.7 -> 1.05 rpm.",
                    "8. After clamp CO 71 ppm <= 95; brick still 718 C.",
                    "9. At 22.600 ms a retort-tube leak dumps 0.35 t char.",
                    "10. 15 min steam-chest isolate (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_kiln_rpm"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("kiln_rpm", 1.7),
                        ("co_ppm", 194.0),
                        ("brick_C", 718.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("co_ppm", 194.0),
                        ("co_cap_ppm", 95.0),
                        ("predicted_unclamped_next_ppm", 148.0),
                        ("kiln_rpm", 1.7),
                        ("brick_C", 718.0),
                        ("brick_cap_C", 770.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 64),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.7 rpm because brick 718 C is under 770, treating the "
                "194 ppm CO as a still-wet NDIR cell rather than an off-gas-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Off-gas CO 194 ppm won by 180 us, so the activation is off-spec, not still a "
                "brick-shell story. Holding 1.7 rpm predicts next-sample 148 ppm > 95 cap. "
                "MODIFY: kiln 1.7 -> 1.05 rpm. Observed after clamp 71 ppm <= 95. A full REJECT "
                "is not indicated: a clean activation accepts 1.05 rpm.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "co_ppm",
                            OrderedDict(
                                [
                                    ("cap", 95.0),
                                    ("observed", 194.0),
                                    ("predicted_unclamped_next", 148.0),
                                    ("clamped_kiln_rpm", 1.05),
                                    ("observed_after_clamp", 71.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 2.81),
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
            ("name", "clamped_kiln_rpm"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("kiln_rpm", 1.05),
                        ("co_ppm", 71.0),
                        ("brick_C", 718.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: kiln 1.7 -> 1.05 rpm. Process-correct vs the 95 ppm CO cap. "
                "Retort tube still leaks at 22.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held off-gas CO at 71 ppm. At 22.600 ms a retort-tube "
                "leak already seated on the steam chest dumped 0.35 t of char. Clamp "
                "reduced dump energy; it did not prevent the leak. Partnered negative: process "
                "heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("offgas", "clamp executed; peak 71 ppm <= 95 cap"),
                        ("retort_tube", "leaked at 22.600 ms; 0.35 t char"),
                        ("repair", "15 min steam-chest isolate (abort_s=900)"),
                        ("mission", "SR-3 activation incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither off-gas CO nor kiln encoder predicted the seated retort-tube leak; ae.retort.leak is a new channel at 22.600 ms, 16.520 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min steam-chest isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min steam-chest isolate after the retort-tube leak. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the RPM clamp completed under the 95 ppm "
                "cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "co.offgas.ppm (5.360 ms, 194 ppm)"),
                        ("loser", "enc.kiln.rpm (5.540 ms, 1.7 rpm)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Speed-first by < 180 us inside the 380 us window would have kept "
                            "1.7 rpm; predicted next-sample 148 ppm would have missed the 95 "
                            "cap even without the leak. The MODIFY is still the correct "
                            "process. The leak is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22600),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.600 ms retort-tube leak (tick t_us=22600), inside the 42 ms "
                "raster. The correct MODIFY at 6.080 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=900 isolation tick.",
            ),
            ("delayed_surprise_s", 900),
        ]
    )
    spikes = [
        spike("enc.kiln.rpm", 1.200, 0.41),
        spike("co.offgas.ppm", 2.144, 0.58),
        spike("enc.kiln.rpm", 3.500, 0.50),
        spike("co.offgas.ppm", 5.360, 1.31),
        spike("enc.kiln.rpm", 5.540, 1.12),
        spike("ctrl.gate", 6.080, 0.97),
        spike("co.offgas.ppm", 8.200, 0.82),
        spike("enc.kiln.rpm", 10.500, 0.64),
        spike("ctrl.gate", 14.400, 0.86),
        spike("ae.retort.leak", 22.600, 1.48),
        spike("ae.retort.leak", 24.200, 0.93),
        spike("enc.kiln.rpm", 30.400, 0.40),
        spike("co.offgas.ppm", 36.600, 0.55),
    ]
    dw = 0.38
    ras = raster_core(
        42,
        78,
        26,
        85,
        routing(
            "thalamic-relay.char-co",
            "spikenaut.policy.rpm-clamp",
            [
                ("relay.co.offgas", "policy.rpm_clamp", 0.68),
                ("relay.enc.kiln", "policy.speed_hold", 0.29),
                ("relay.ae.retort", "policy.rpm_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at CO win (5.360 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.600 ms retort-tube leak",
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
                    pop_budget("rpm_clamp", 50, 0.50, 220.0, dw),
                    pop_budget("speed_hold", 40, 0.80, 50.0, dw),
                    pop("leak_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r77-401"),
            (
                "title",
                "Steamchar-Riggs SR-3 / Kiln SK-7: off-gas CO beats kiln RPM by 180 us; "
                "correct MODIFY still eats an in-window retort-tube leak (partnered negative "
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
                    "steam-chest isolate (abort_s=900) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "steam-activated-carbon-kiln",
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
                    "15 min steam-chest isolate.",
                    1,
                ),
            ),
        ]
    )


def record_402():
    ticks = [
        tick(2192, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5480, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5660, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6020, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6360, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("ft.steam.tph", 1.100, 0.42),
        spike("ft.steam.klbh", 2.192, 0.57),
        spike("ft.steam.tph", 3.500, 0.49),
        spike("ft.steam.tph", 5.480, 1.29),
        spike("ft.steam.klbh", 5.660, 1.10),
        spike("ctrl.gate", 6.020, 0.96),
        spike("ft.steam.tph", 8.300, 0.80),
        spike("ft.steam.klbh", 10.400, 0.63),
        spike("ctrl.gate", 12.600, 0.84),
        spike("ft.steam.tph", 16.600, 0.41),
        spike("ft.steam.klbh", 22.200, 0.54),
        spike("ft.steam.tph", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(77402, 90, 30000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Catofin PDH reactor R-5 at Catofin-Veld CV-8 reads live dilution steam 24.0 t/h "
                "over a 22.0 t/h cap; a lagged historian still republishes the same steam as "
                "52.9 klb/h without an EU. Live-t/h-first should cut 24.0 -> 18.0 t/h; a weak "
                "supervisor treats 52.9 as t/h and over-cuts to 8.0.",
            ),
            ("domain", "propane-dehydrogenation-catofin"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the CV-8 dehydrogenation with live steam <= 22.0 t/h, leave propane at "
                "the planned 11.0 t/h, and bind the metric t/h EU only.",
            ),
            ("t0_us", 1756850400000402),
            ("gate_latency_us", 540),
            ("race_window_us", 340),
            ("race_window_rel_ms", [5.480, 5.820]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.steam.tph 24.0 t/h live metric EU",
                                "ft.steam.klbh 52.9 klb/h lagged historian EU",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-t/h-first should latch a timely steam cut 24.0 -> 18.0 t/h; "
                            "klb/h-first is a false 'same number, wrong unit' over-clamp.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live Coriolis t/h slot versus the lagged klb/h "
                            "historian publisher on this Catofin steam bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (live 28 + lagged 34). Order is "
                            "correctly live-t/h-first. The error is the engineering unit bound, not "
                            "the race winner: 52.9 klb/h converts to 24.0 t/h.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live steam Coriolis, 2 kHz, 28 us jitter, EU=t/h, tag=ST_LIVE.TPH",
                    "lagged historian steam, 1 kHz, 34 us jitter, EU=klb/h, tag=ST_HIST.KLBH tag_age_us=2840",
                    "bed TC (context)",
                    "propane FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("steam_cap_tph", 22.0),
                        ("live_steam_tph", 24.0),
                        ("lagged_steam_klbh", 52.9),
                        ("live_unit", "t/h"),
                        ("lagged_unit", "klb/h"),
                        ("tag_age_us", 2840),
                        ("max_legal_tag_age_us", 800),
                        ("propane_tph", 11.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. R-5 LIVE already dehydrogenating; steam 24.0 t/h; propane 11.0 t/h.",
                    "2. Historian ST_HIST.KLBH still 52.9 klb/h; tag_age_us=2840 > 800.",
                    "3. Steam precursor at 1.100 ms.",
                    "4. Race window [5.480, 5.820] ms.",
                    "5. ft.steam.tph 24.0 at 5.480 ms (winner).",
                    "6. ft.steam.klbh 52.9 at 5.660 ms (loser by 180 us).",
                    "7. Gate at 6.020 ms: WRONG-MODIFY binds 52.9 as t/h.",
                    "8. Steam 24.0 -> 8.0 t/h; conversion stalls; bed 498 C.",
                    "9. Propane slip; correct cut was 24.0 -> 18.0 t/h.",
                    "10. Delayed (abort_s=720): 12 min bed quench while steam is restored.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_steam_24"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_tph", 24.0),
                        ("bind_lagged_unit", False),
                        ("bound_unit", "t/h"),
                        ("propane_tph", 11.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_steam_tph", 24.0),
                        ("steam_cap_tph", 22.0),
                        ("lagged_steam_klbh", 52.9),
                        ("live_unit", "t/h"),
                        ("lagged_unit", "klb/h"),
                        ("bound_unit", "t/h"),
                        ("unit_scale_klb_per_t", 2.2046),
                        ("lagged_equals_live_after_convert", True),
                        ("tag_age_us", 2840),
                        ("max_legal_tag_age_us", 800),
                        ("propane_tph", 11.0),
                        ("t_gate_us", 6020),
                        ("correct_steam_tph", 18.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 24.0 t/h because the historian 52.9 still looks "
                "like a healthy steam number if the EU is ignored, so the 24.0 t/h live miss "
                "is treated as a shadow of the lagged bus.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Steam 52.9 exceeds the 22.0 cap (true if the number is t/h). Apply an 8.0 t/h "
                "steam cut on the highlighted historian tag ST_HIST.KLBH. Leave the live "
                "Coriolis t/h unbound.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "steam_flow",
                            OrderedDict(
                                [
                                    ("cap_tph", 22.0),
                                    ("live_tph", 24.0),
                                    ("lagged_klbh", 52.9),
                                    ("executed_steam_tph", 8.0),
                                    ("correct_steam_tph", 18.0),
                                    ("bound_unit", "t/h"),
                                    ("lagged_unit", "klb/h"),
                                ]
                            ),
                        ),
                        (
                            "unit_bind",
                            OrderedDict(
                                [
                                    ("t_gate_us", 6020),
                                    ("bind_lagged_unit", True),
                                    ("tag_age_us", 2840),
                                    ("wrong_unit", True),
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
            ("name", "steam_cut_wrong_unit"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_tph", 8.0),
                        ("bind_lagged_unit", True),
                        ("bound_unit", "t/h"),
                        ("propane_tph", 11.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / wrong-unit lagged-bus): 8.0 t/h steam cut from treating "
                "52.9 klb/h as t/h. Routing relay.ft.klbh -> policy.unit_clamp; no positive "
                "weight to policy.live_hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY over-cut Catofin steam. Live 24.0 t/h was over the 22.0 cap at "
                "t_gate; 52.9 klb/h was the same steam on a lagged bus. Bed fell to 498 C. "
                "12 min quench (abort_s=720). Correct gate was MODIFY steam 24.0 -> 18.0 t/h "
                "on the live t/h EU at t_gate_us=6020.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live_steam", "cut 24.0 -> 8.0 t/h; conversion stall"),
                        ("lagged_bus", "52.9 klb/h bound as t/h"),
                        ("quench", "12 min bed quench"),
                        ("mission", "dehydrogenation deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-t/h-first was the correct order and 24.0 t/h was over cap; the MODIFY scaled the lagged klb/h number as if it were t/h.",
                    "Delayed (abort_s=720): CV-8 holds 12 min while steam is restored and the bed is re-soaked; next cycle 11 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY steam 24.0 -> 18.0 t/h on live t/h EU at t_gate_us=6020; bind_lagged_unit=false; leave propane at 11.0 t/h.",
                        ),
                        ("correct_actuator", "R5_steam_tph"),
                        ("wrong_unit", "ST_HIST.KLBH treated as t/h"),
                        ("t_gate_us", 6020),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("steam_tph", 8.0),
                                    ("bind_lagged_unit", True),
                                    ("bound_unit", "t/h"),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min bed quench (task/efficiency); conversion stalled at 8.0 t/h while the live Coriolis only needed 18.0 (safety near-miss of a unit-scaled over-clamp).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.steam.tph (5.480 ms, 24.0 t/h live)"),
                        ("loser", "ft.steam.klbh (5.660 ms, 52.9 klb/h lagged)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Klb/h-first by < 180 us would still be 52.9 klb/h = 24.0 t/h after "
                            "convert; a correct gate binds ft.steam.tph to policy.live_hold at "
                            "t_gate either way. The wrong MODIFY spent the live win on the lagged unit.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6020),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong-unit bind (6.020 ms, tick 4). "
                "The 12 min bed quench is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 720),
        ]
    )
    dw = 0.34
    ras = raster_core(
        30,
        90,
        32,
        86,
        routing(
            "thalamic-relay.pdh-klbh",
            "spikenaut.policy.unit-clamp",
            [
                ("relay.ft.klbh", "policy.unit_clamp", 0.74),
                ("relay.ft.tph", "policy.unit_clamp", 0.21),
            ],
            "acetylcholine",
            0.08,
            "unit_cap_stdp; ACh tags the (wrong) unit_clamp bind at the live t/h win",
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
                    pop_budget("unit_clamp", 48, 0.45, 300.0, dw),
                    pop("live_hold", 48, 0.90),
                    pop("unit_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r77-402"),
            (
                "title",
                "WRONG-MODIFY at Catofin-Veld CV-8 / Reactor R-5: live 24.0 t/h read correctly; "
                "52.9 klb/h lagged bus treated as t/h and steam cut to 8.0 (wrong-unit / lagged-bus)",
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
                    "Wrong-modify / wrong-unit lagged-bus. Sidecar arithmetic 24.0 > 22.0 on live "
                    "t/h is true; 52.9 klb/h converts to 24.0 t/h; MODIFY bound to unit_clamp. "
                    "total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "propane-dehydrogenation-catofin",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-unit",
                        "lagged-bus",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live-t/h race can still be a wrong gate "
                    "when the MODIFY scales a lagged klb/h tag as t/h. Convictable from unit "
                    "fields, tag_age_us, and routing without Catofin physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_403():
    ticks = [
        tick(2768, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6920, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7100, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7700, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(8000, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("pt.phos.bar", 1.400, 0.40),
        spike("ae.md.pps", 2.768, 0.56),
        spike("pt.phos.bar", 4.200, 0.48),
        spike("ae.md.pps", 6.920, 1.34),
        spike("pt.phos.bar", 7.100, 1.11),
        spike("ctrl.gate", 7.700, 0.98),
        spike("ae.md.pps", 10.500, 0.81),
        spike("pt.phos.bar", 15.000, 0.62),
        spike("ctrl.gate", 18.400, 0.84),
        spike("ae.md.pps", 28.600, 0.52),
        spike("pt.phos.bar", 36.200, 0.39),
        spike("ae.md.pps", 42.000, 0.44),
    ]
    excerpt = independent_excerpt(77403, 116, 44000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "HIL phosgenation P-4 at Isocyanate-Staith IS-HIL hears mixer AE at 58 pps while "
                "the phosgene header remains 7.6 bar under a 9.5 bar cap. AE-first holds MDA; "
                "header-first would dispatch 16 t/h because the COCl2 ram looks legal. The HIL "
                "mixer mockup is the authority, not the MDI floor.",
            ),
            ("domain", "mdi-phosgenation-reactor"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep P-4 from dispatching a growling mixer while phosgene header pressure remains "
                "under its own cap.",
            ),
            ("t0_us", 1756850400000403),
            ("gate_latency_us", 780),
            ("race_window_us", 300),
            ("race_window_rel_ms", [6.920, 7.220]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.md.pps 58 over 16 cap",
                                "pt.phos.bar 7.6 under 9.5 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; header-first dispatches 16 t/h MDA on a "
                            "'phosgene still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one AE puck slot versus the phosgene-PT publisher on this "
                            "HIL phosgenation bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 56 us (AE 24 + PT 32): 3.21x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 300 us "
                            "window would have dispatched 16 t/h into a growling mixer.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "mixer AE puck, 50 kHz, 24 us jitter",
                    "phosgene header PT, 1 kHz, 32 us jitter",
                    "MDA Coriolis (context)",
                    "vent IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 16.0),
                        ("observed_ae_pps", 58.0),
                        ("phos_bar", 7.6),
                        ("phos_cap_bar", 9.5),
                        ("proposed_mda_tph", 16.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. P-4 HIL indexed; 16 t/h MDA armed.",
                    "2. Phosgene 7.6 bar under 9.5; AE 58 pps over 16.",
                    "3. PT precursor at 1.400 ms.",
                    "4. Race window [6.920, 7.220] ms.",
                    "5. ae.md.pps 58 at 6.920 ms (winner).",
                    "6. pt.phos.bar 7.6 at 7.100 ms (loser by 180 us).",
                    "7. Gate at 7.700 ms: REJECT hold, do not dispatch.",
                    "8. Feed 0 t/h; phosgene left at 7.6 bar.",
                    "9. Mixer inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min phosgene reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_mda"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("mda_tph", 16.0),
                        ("hold", False),
                        ("phos_bar", 7.6),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 58.0),
                        ("ae_cap_pps", 16.0),
                        ("phos_bar", 7.6),
                        ("phos_cap_bar", 9.5),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 56),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 16 t/h MDA because phosgene 7.6 bar is under 9.5, treating the "
                "58 pps AE as agitator hash rather than a growling mixer.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Mixer AE 58 pps won by 180 us, so the phosgenator is growling, not still a "
                "phosgene-header story. Header 7.6 bar is under 9.5 and does not authorize dispatch. "
                "REJECT: hold feed 16 -> 0 t/h. A MODIFY that only trims COCl2 would leave the growl.",
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
                                    ("observed", 58.0),
                                    ("executed_mda_tph", 0.0),
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
            ("name", "hold_phosgenator"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("mda_tph", 0.0),
                        ("hold", True),
                        ("phos_bar", 7.6),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: MDA 16 -> 0 t/h. Phosgene left at 7.6 bar under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held P-4. AE 58 pps beat phosgene 7.6 bar by 180 us. Header was "
                "legal; the mixer was not. 8 min phosgene reset (abort_s=480) is delayed survey, "
                "not a process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held at 0 t/h"),
                        ("phosgene", "left 7.6 bar < 9.5 cap"),
                        ("mixer", "8 min phosgene reset (abort_s=480)"),
                        ("mission", "HIL MDA not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Phosgene PT never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min phosgene reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.md.pps (6.920 ms, 58 pps)"),
                        ("loser", "pt.phos.bar (7.100 ms, 7.6 bar)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Header-first by < 180 us inside the 300 us window would have dispatched "
                            "16 t/h into a growling mixer. The REJECT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7700),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.700 ms, tick 4). The 8 min phosgene "
                "reset is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    dw = 0.30
    ras = raster_core(
        44,
        116,
        22,
        112,
        routing(
            "thalamic-relay.md-ae",
            "spikenaut.policy.md-hold",
            [
                ("relay.ae.md", "policy.md_hold", 0.70),
                ("relay.pt.phos", "policy.phos_go", 0.24),
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
                    pop_budget("md_hold", 56, 0.45, 280.0, dw),
                    pop("phos_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r77-403"),
            (
                "title",
                "Isocyanate-Staith IS-HIL / Phosgenator P-4: mixer AE 58 pps beats phosgene 7.6 bar "
                "by 180 us; correct REJECT holds MDA",
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
                    "Correct REJECT. AE 58 > 16 cap beats legal phosgene header. "
                    "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "mdi-phosgenation-reactor",
                    [
                        "reject",
                        "hil",
                        "ae-vs-phosgene",
                        "growling-mixer",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal phosgene header can lose to mixer AE inside a 300 us "
                    "window; reversing 180 us would have dispatched a growling phosgenator.",
                    3,
                ),
            ),
        ]
    )


def record_404():
    ticks = [
        tick(2912, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7280, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7460, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7900, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8240, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.ox.C", 1.240, 0.40),
        spike("dens.ka.frac", 2.912, 0.55),
        spike("tc.ox.C", 4.500, 0.48),
        spike("dens.ka.frac", 7.280, 1.26),
        spike("tc.ox.C", 7.460, 1.08),
        spike("ctrl.gate", 7.900, 0.95),
        spike("dens.ka.frac", 11.300, 0.78),
        spike("tc.ox.C", 15.000, 0.60),
        spike("ctrl.gate", 18.500, 0.82),
        spike("dens.ka.frac", 22.800, 0.50),
        spike("tc.ox.C", 25.400, 0.38),
    ]
    excerpt = independent_excerpt(77404, 52, 26000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("air_tph", 4.2),
            ("ka_frac", 0.58),
            ("ox_C", 164.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "KA-oil oxidizer OX-2 at Adipate-Hurst AH-5 already holds cyclohexanone-alcohol "
                "at 0.58 mass fraction under a 0.74 trip, with oxidate 164 C under 188. Holdup-first "
                "accepts the 4.2 t/h air; jacket-first would have rejected a legal oxidation on a "
                "'still climbing' model.",
            ),
            ("domain", "adipic-ka-air-oxidizer"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the AH-5 air pass with KA holdup <= 0.74 and oxidate <= 188 C.",
            ),
            ("t0_us", 1756850400000404),
            ("gate_latency_us", 620),
            ("race_window_us", 340),
            ("race_window_rel_ms", [7.280, 7.620]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "dens.ka.frac 0.58 under 0.74 trip",
                                "tc.ox.C 164 under 188 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Holdup-first confirms the already-legal 4.2 t/h air; jacket-first "
                            "would have treated the densitometer as a climb echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one nuclear-density slot versus the oxidate-TC publisher "
                            "on this simulated KA-oil air-oxidizer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (dens 26 + TC 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed air illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "nuclear densitometer on KA loop, 26 us jitter",
                    "oxidate TC well, 32 us jitter",
                    "air FT (context)",
                    "off-gas O2 (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ka_cap_frac", 0.74),
                        ("observed_ka_frac", 0.58),
                        ("ox_cap_C", 188.0),
                        ("observed_ox_C", 164.0),
                        ("o2_offgas_pct", 4.1),
                        ("o2_cap_pct", 8.0),
                        ("proposed_air_tph", 4.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. OX-2 indexed on Adipate-Hurst AH-5; 4.2 t/h air armed.",
                    "2. Caps: KA 0.74, oxidate 188 C, off-gas O2 8.0 pct.",
                    "3. Jacket-TC precursor at 1.240 ms.",
                    "4. Race window [7.280, 7.620] ms.",
                    "5. dens.ka.frac 0.58 at 7.280 ms (winner).",
                    "6. tc.ox.C 164 at 7.460 ms (loser by 180 us).",
                    "7. Gate at 7.900 ms: ACCEPT 4.2 t/h already legal.",
                    "8. Air continues; no extra hold.",
                    "9. 6 min survey confirms KA still under 0.74.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "air_4p2"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ka_frac", 0.58),
                        ("ka_cap_frac", 0.74),
                        ("ox_C", 164.0),
                        ("ox_cap_C", 188.0),
                        ("o2_offgas_pct", 4.1),
                        ("o2_cap_pct", 8.0),
                        ("air_tph", 4.2),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 4.2 t/h air pass because KA 0.58 is under 0.74 and oxidate "
                "164 C is under 188 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "KA holdup 0.58 won by 180 us and is under 0.74. Oxidate 164 C is under "
                "188 C. Off-gas O2 4.1 pct is under 8.0. ACCEPT the already-legal air.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ka_frac",
                            OrderedDict(
                                [
                                    ("cap", 0.74),
                                    ("observed", 0.58),
                                    ("executed_air_tph", 4.2),
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
            ("name", "air_4p2"),
            ("parameters", OrderedDict(params.items())),
            (
                "gate_effect",
                "ACCEPT: 4.2 t/h air and 0.58 KA holdup unchanged. Routing relay.dens.ka -> "
                "policy.air_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left OX-2 on a 4.2 t/h / 0.58 KA air pass. Jacket hitch did not "
                "justify a hold. 6 min survey confirmed KA still under 0.74.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("air", "still 4.2 t/h"),
                        ("holdup", "0.58 under 0.74 trip"),
                        ("oxidate", "164 C under 188"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Oxidate TC 164 C hitch is residual, not a runaway trip.",
                    "Delayed (survey_s=360): 6 min survey restacks OX-2 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "dens.ka.frac (7.280 ms, 0.58)"),
                        ("loser", "tc.ox.C (7.460 ms, 164 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Jacket-first by < 180 us would only delay confirmation. The air stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7900),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (7.900 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 360),
        ]
    )
    dw = 0.34
    ras = raster_core(
        26,
        52,
        40,
        54,
        routing(
            "thalamic-relay.ka-dens",
            "spikenaut.policy.air-go",
            [
                ("relay.dens.ka", "policy.air_go", 0.68),
                ("relay.tc.ox", "policy.ox_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_air_stdp; 5-HT tags the air_go bind at the densitometer win",
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
                    pop_budget("air_go", 40, 0.45, 250.0, dw),
                    pop("ox_hold", 32, 0.90),
                    pop("ka_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r77-404"),
            (
                "title",
                "Adipate-Hurst AH-5 / Oxidizer OX-2: KA holdup 0.58 beats oxidate 164 C "
                "by 180 us; ACCEPT already-legal 4.2 t/h air",
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
                    "Correct ACCEPT of an already-legal KA-oil air pass. total +1.06 = "
                    "0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "adipic-ka-air-oxidizer",
                    [
                        "accept",
                        "already-legal",
                        "simulated-ka-loop",
                        "dens-vs-tc",
                        "sidecar-convictable",
                        "simulated",
                    ],
                    "Teaches that a KA densitometer under trip can confirm an already-legal "
                    "air pass without a jacket hitch becoming a hold.",
                    4,
                ),
            ),
        ]
    )


def record_405():
    ticks = [
        tick(2048, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5120, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5280, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5680, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5960, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(240000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.elec.mw", 1.000, 0.41),
        spike("gc.si.wt", 2.048, 0.60),
        spike("ft.elec.mw", 3.300, 0.51),
        spike("gc.si.wt", 5.120, 1.30),
        spike("ft.elec.mw", 5.280, 1.12),
        spike("ctrl.gate", 5.680, 0.97),
        spike("gc.si.wt", 8.200, 0.78),
        spike("ft.elec.mw", 12.500, 0.62),
        spike("ctrl.gate", 16.300, 0.85),
        spike("gc.si.wt", 20.400, 0.54),
        spike("ft.elec.mw", 22.700, 0.43),
    ]
    excerpt = independent_excerpt(77405, 82, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("electrode_mw", 36.0),
            ("si_wt_pct", 98.6),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Submerged-arc furnace F-2 at Metalloid-Sill MS-9 is already at 98.6 wt percent "
                "silicon under a 99.4 cap, electrode power 36.0 MW under 41.0. Assay-first accepts "
                "the 36.0 MW hold; power-first would have rejected a legal metal on a 'still "
                "ramping' model.",
            ),
            ("domain", "silicon-metal-submerged-arc"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run F-2 at 36.0 MW, keep Si <= 99.4 wt percent and electrode MW <= 41.0, and "
                "leave the tap on schedule.",
            ),
            ("t0_us", 1756850400000405),
            ("gate_latency_us", 560),
            ("race_window_us", 280),
            ("race_window_rel_ms", [5.120, 5.400]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "gc.si.wt 98.6 under 99.4 cap",
                                "ft.elec.mw 36.0 under 41.0 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Assay-first confirms the already-legal 36.0 MW hold; power-first "
                            "would have treated the GC as a hitch echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one tap-sample GC slot versus the electrode-MW publisher on this "
                            "silicon-metal furnace bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (GC 22 + MW 30): 3.08x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal 36.0 MW hold.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "tap-sample silicon GC, 2 kHz, 22 us jitter",
                    "electrode MW transducer, 1 kHz, 30 us jitter",
                    "hearth TC (context)",
                    "stinger height encoder (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("si_cap_wt_pct", 99.4),
                        ("observed_si_wt_pct", 98.6),
                        ("electrode_mw", 36.0),
                        ("mw_cap", 41.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Furnace F-2 indexed on Metalloid-Sill MS-9; 36.0 MW armed.",
                    "2. Si 98.6 wt percent under 99.4; electrode 36.0 MW under 41.0.",
                    "3. MW precursor at 1.000 ms.",
                    "4. Race window [5.120, 5.400] ms.",
                    "5. gc.si.wt 98.6 at 5.120 ms (winner).",
                    "6. ft.elec.mw 36.0 at 5.280 ms (loser by 160 us).",
                    "7. Gate at 5.680 ms: ACCEPT 36.0 MW.",
                    "8. Si stays 98.6; MW stays 36.0.",
                    "9. Heat taps on-spec.",
                    "10. Delayed (dwell_s=240): 4 min ladle reseq.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_electrode_mw"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("si_wt_pct", 98.6),
                        ("si_cap_wt_pct", 99.4),
                        ("electrode_mw", 36.0),
                        ("mw_cap", 41.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 36.0 MW because Si 98.6 is under 99.4 and electrode power "
                "36.0 MW is under 41.0.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Silicon GC 98.6 wt percent won by 160 us, so the furnace is already legal, not still "
                "ramping. Electrode 36.0 MW is under 41.0. ACCEPT the 36.0 MW hold. A REJECT "
                "would idle a legal silicon-metal furnace.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "si_wt_pct",
                            OrderedDict(
                                [
                                    ("cap", 99.4),
                                    ("observed", 98.6),
                                    ("executed_electrode_mw", 36.0),
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
            ("name", "hold_electrode_mw"),
            ("parameters", OrderedDict(params.items())),
            ("gate_effect", "ACCEPT: leave 36.0 MW; Si 98.6; electrode legal."),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 36.0 MW hold. Silicon 98.6 beat electrode MW "
                "36.0 by 160 us. 4 min ladle reseq (dwell_s=240) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("power", "36.0 MW held"),
                        ("silicon", "98.6 < 99.4 cap"),
                        ("furnace", "F-2 on-spec"),
                        ("reseq", "4 min ladle reseq (dwell_s=240)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Electrode MW never approached 41.0; silicon was already under cap.",
                    "Delayed (dwell_s=240): 4 min ladle reseq after tap.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "gc.si.wt (5.120 ms, 98.6 wt percent)"),
                        ("loser", "ft.elec.mw (5.280 ms, 36.0 MW)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Power-first by < 160 us inside the 280 us window would have REJECTED "
                            "an already-legal 36.0 MW hold. The ACCEPT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5680),
            (
                "reward_inflection_note",
                "Task and safety rise at the correct ACCEPT (5.680 ms, tick 4). The 4 min reseq "
                "is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 240),
        ]
    )
    dw = 0.28
    ras = raster_core(
        24,
        82,
        28,
        55,
        routing(
            "thalamic-relay.si-gc",
            "spikenaut.policy.mw-go",
            [
                ("relay.gc.si", "policy.mw_go", 0.67),
                ("relay.ft.mw", "policy.mw_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the silicon-GC win as an already-legal MW hold",
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
                    pop_budget("mw_go", 40, 0.45, 250.0, dw),
                    pop("mw_hold", 32, 0.90),
                    pop("si_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r77-405"),
            (
                "title",
                "Metalloid-Sill MS-9 / Furnace F-2: silicon 98.6 wt percent beats electrode 36.0 MW by "
                "160 us; correct ACCEPT of an already-legal 36.0 MW hold",
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
                    "Correct ACCEPT. Si 98.6 < 99.4; electrode 36.0 MW < 41.0. "
                    "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "silicon-metal-submerged-arc",
                    [
                        "accept",
                        "designed",
                        "si-vs-mw",
                        "already-legal-hold",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal electrode MW can lose to silicon GC inside a 280 us "
                    "window; reversing 160 us would have REJECTED an already-legal furnace hold.",
                    5,
                ),
            ),
        ]
    )
