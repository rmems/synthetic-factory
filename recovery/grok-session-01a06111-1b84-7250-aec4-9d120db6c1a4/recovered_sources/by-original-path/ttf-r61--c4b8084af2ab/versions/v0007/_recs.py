def lif_321_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.42
    stim = (22000, 25000)
    seed = 61321
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
    blow = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + blow, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.blow" for t, _ in picked]
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
            ("seed", 61321),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 electrode-current clamp bias; stim 22-25 ms is the tap-hole clay blow.",
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


def record_321():
    excerpt, extra = lif_321_excerpt()
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
                "Slag furnace F-4 at Ilmenite-Fen IF-6 is already at 18.2 wt percent FeO against a "
                "12.0 cap while electrode current still reads a legal 42.0 kA. FeO-first clamps "
                "current 42.0 -> 31.0 kA; kiloamp-first would keep cruise because shell PT 0.86 bar "
                "is still under the 1.20 bar roof cap. A tap-hole clay plug already seated on the "
                "east taphole does not appear on FeO or current until the AE dump.",
            ),
            ("domain", "ilmenite-slag-furnace"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep F-4 slag FeO <= 12.0 wt percent and finish the heat without dumping slag "
                "through a blown tap-hole clay plug.",
            ),
            ("t0_us", 1756850400000321),
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
                                "gc.feo.pct 18.2 over 12.0 cap",
                                "enc.elec.kA 42.0 with shell 0.86 under 1.20",
                            ],
                        ),
                        (
                            "semantics",
                            "FeO-first latches electrode clamp 42.0 -> 31.0 kA; kiloamp-first keeps "
                            "42.0 on a 'still under roof-pressure cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one XRF FeO slot versus the electrode-current publisher on this "
                            "ilmenite-furnace bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (FeO 28 + kA 34): 2.90x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 42.0 kA; predicted next-sample 15.4 wt percent "
                            "> 12.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "slag XRF FeO cell, 2 kHz, 28 us jitter",
                    "electrode current CT + shell PT, 1 kHz, 34 us jitter",
                    "tap-hole AE puck (context)",
                    "roof IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("feo_cap_wt_pct", 12.0),
                        ("observed_feo_wt_pct", 18.2),
                        ("elec_kA", 42.0),
                        ("shell_bar", 0.86),
                        ("shell_cap_bar", 1.20),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. F-4 indexed on Ilmenite-Fen IF-6; electrode 42.0 kA; slag FeO 18.2 wt percent.",
                    "2. Shell 0.86 bar under 1.20 bar cap; heat armed.",
                    "3. Current precursor at 1.180 ms.",
                    "4. Race window [5.280, 5.640] ms.",
                    "5. gc.feo.pct 18.2 at 5.280 ms (winner).",
                    "6. enc.elec.kA 42.0 at 5.460 ms (loser by 180 us).",
                    "7. Gate at 5.980 ms: MODIFY clamp 42.0 -> 31.0 kA.",
                    "8. After clamp FeO 10.8 wt percent <= 12.0; shell still 0.86 bar.",
                    "9. At 22.600 ms a tap-hole clay plug blows and dumps 0.4 t slag.",
                    "10. 15 min taphole re-mud (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_electrode_kA"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("elec_kA", 42.0),
                        ("feo_wt_pct", 18.2),
                        ("shell_bar", 0.86),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("feo_wt_pct", 18.2),
                        ("feo_cap_wt_pct", 12.0),
                        ("predicted_unclamped_next_wt_pct", 15.4),
                        ("elec_kA", 42.0),
                        ("shell_bar", 0.86),
                        ("shell_cap_bar", 1.20),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 42.0 kA because shell 0.86 bar is under 1.20, treating the "
                "18.2 wt percent FeO as a still-wet XRF cup rather than a slag-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Slag FeO 18.2 wt percent won by 180 us, so the furnace is off-spec, not still a "
                "roof-pressure story. Holding 42.0 kA predicts next-sample 15.4 wt percent > 12.0 cap. "
                "MODIFY: electrode 42.0 -> 31.0 kA. Observed after clamp 10.8 wt percent <= 12.0. A full "
                "REJECT is not indicated: a clean heat accepts 31.0 kA.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "feo_wt_pct",
                            OrderedDict(
                                [
                                    ("cap", 12.0),
                                    ("observed", 18.2),
                                    ("predicted_unclamped_next", 15.4),
                                    ("clamped_elec_kA", 31.0),
                                    ("observed_after_clamp", 10.8),
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
            ("name", "clamped_electrode_kA"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("elec_kA", 31.0),
                        ("feo_wt_pct", 10.8),
                        ("shell_bar", 0.86),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: electrode 42.0 -> 31.0 kA. Process-correct vs the 12.0 wt percent FeO cap. "
                "Tap-hole clay still blows at 22.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held slag FeO at 10.8 wt percent. At 22.600 ms a tap-hole "
                "clay plug already seated on the east taphole dumped 0.4 t of slag. Clamp reduced "
                "dump energy; it did not prevent the blow. Partnered negative: process heads stay "
                "honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("slag", "clamp executed; peak 10.8 wt percent <= 12.0 cap"),
                        ("taphole", "blew at 22.600 ms; 0.4 t slag"),
                        ("repair", "15 min taphole re-mud (abort_s=900)"),
                        ("mission", "IF-6 heat incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither slag FeO nor electrode CT predicted the seated tap-hole clay blow; ae.taphole.blow is a new channel at 22.600 ms, 16.620 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min taphole re-mud. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min taphole re-mud after the clay blow. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the electrode clamp completed under the 12.0 wt "
                "percent cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "gc.feo.pct (5.280 ms, 18.2 wt percent)"),
                        ("loser", "enc.elec.kA (5.460 ms, 42.0 kA)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Kiloamp-first by < 180 us inside the 360 us window would have kept "
                            "42.0 kA; predicted next-sample 15.4 wt percent would have missed the "
                            "12.0 cap even without the clay blow. The MODIFY is still the correct "
                            "process. The blow is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22600),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.600 ms tap-hole clay blow (tick t_us=22600), inside the "
                "42 ms raster. The correct MODIFY at 5.980 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=900 re-mud tick.",
            ),
            ("delayed_surprise_s", 900),
        ]
    )
    spikes = [
        spike("enc.elec.kA", 1.180, 0.41),
        spike("gc.feo.pct", 2.112, 0.58),
        spike("enc.elec.kA", 3.400, 0.50),
        spike("gc.feo.pct", 5.280, 1.31),
        spike("enc.elec.kA", 5.460, 1.12),
        spike("ctrl.gate", 5.980, 0.97),
        spike("gc.feo.pct", 8.100, 0.82),
        spike("enc.elec.kA", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.taphole.blow", 22.600, 1.48),
        spike("ae.taphole.blow", 24.100, 0.93),
        spike("enc.elec.kA", 30.200, 0.40),
        spike("gc.feo.pct", 36.400, 0.55),
    ]
    dw = 0.36
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.ilmenite-feo",
            "spikenaut.policy.ka-clamp",
            [
                ("relay.gc.feo", "policy.ka_clamp", 0.68),
                ("relay.enc.elec", "policy.ka_hold", 0.29),
                ("relay.ae.taphole", "policy.ka_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at FeO win (5.280 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.600 ms tap-hole clay blow",
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
                    pop_budget("ka_clamp", 50, 0.50, 220.0, dw),
                    pop_budget("ka_hold", 40, 0.80, 50.0, dw),
                    pop("blow_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r61-321"),
            (
                "title",
                "Ilmenite-Fen IF-6 / Furnace F-4: slag FeO beats electrode current by 180 us; "
                "correct MODIFY still eats an in-window tap-hole clay blow (partnered negative "
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
                    "taphole re-mud (abort_s=900) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "ilmenite-slag-furnace",
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
                    "15 min taphole re-mud.",
                    1,
                ),
            ),
        ]
    )


def record_322():
    ticks = [
        tick(2160, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5400, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5580, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5920, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6260, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(840000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("ct.bus.kA", 1.080, 0.42),
        spike("ct.live.kA", 2.160, 0.57),
        spike("ct.bus.kA", 3.400, 0.49),
        spike("ct.live.kA", 5.400, 1.29),
        spike("sp.shadow.kA", 5.580, 1.10),
        spike("ctrl.gate", 5.920, 0.96),
        spike("ct.live.kA", 8.200, 0.80),
        spike("ct.bus.kA", 10.200, 0.63),
        spike("ctrl.gate", 12.400, 0.84),
        spike("ct.live.kA", 16.400, 0.41),
        spike("sp.shadow.kA", 22.100, 0.54),
        spike("ct.live.kA", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(61322, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "APT autoclave string A at Scheelite-Howe SH-3 reads live 18.4 bar against a 16.0 bar "
                "cap while idle string B still prints 2.1 bar after a rinse. Live-first should cut "
                "steam 4.8 -> 1.6 t/h on string A at t_gate; a weak supervisor writes the same 1.6 t/h "
                "cut onto idle string B because STM.CUT.BANK still aliases the last-selected rinse bank.",
            ),
            ("domain", "tungsten-apt-autoclave"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the SH-3 digest with live string A PT <= 16.0 bar, leave slurry at the planned "
                "6.4 t/h, and keep steam legal on the live bank.",
            ),
            ("t0_us", 1756850400000322),
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
                                "ct.live.kA 4.62 kA on bank 4 header",
                                "sp.shadow.kA 3.40 kA parked on SP.SHADOW",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-first should write 3.40 kA onto SP.LIVE at t_gate; "
                            "shadow-first is a false 'setpoint already legal' bind onto the non-live tag.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live-CT slot versus the shadow-SP publisher on this "
                            "cell-room PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (live 28 + shadow 32). Order is "
                            "correctly live-first. The error is which tag receives the clamp, not "
                            "when or how far: SP.SHADOW is not the live loop.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live header CT, 2 kHz, 28 us jitter, tag=CT.LIVE",
                    "shadow setpoint, 1 kHz, 32 us jitter, tag=SP.SHADOW",
                    "brine FT (context)",
                    "cell-room H2 (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("I_cap_kA", 4.20),
                        ("live_kA", 4.62),
                        ("shadow_kA", 3.40),
                        ("written_tag", "SP.SHADOW"),
                        ("live_sp_kA", 4.62),
                        ("brine_m3h", 18.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Bank 4 already on load; live header 4.62 kA; brine 18.0 m3/h.",
                    "2. SP.SHADOW already holds 3.40 kA from the last recipe download.",
                    "3. Bus precursor at 1.080 ms.",
                    "4. Race window [5.400, 5.740] ms.",
                    "5. ct.live.kA 4.62 at 5.400 ms (winner).",
                    "6. sp.shadow.kA 3.40 at 5.580 ms (loser by 180 us).",
                    "7. Gate at 5.920 ms: WRONG-MODIFY writes 3.40 kA to SP.SHADOW.",
                    "8. SP.LIVE stays 4.62 kA; header peaks 4.88 kA; cell-room trips.",
                    "9. Bank 4 dumped and reseated.",
                    "10. Delayed (abort_s=840): 14 min dump/reseat while SP.LIVE was never written.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_live_sp"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("live_sp_kA", 4.62),
                        ("written_tag", "SP.LIVE"),
                        ("extra_shadow_write", False),
                        ("brine_m3h", 18.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_kA", 4.62),
                        ("I_cap_kA", 4.20),
                        ("shadow_kA", 3.40),
                        ("written_tag", "SP.SHADOW"),
                        ("live_sp_kA", 4.62),
                        ("correct_written_tag", "SP.LIVE"),
                        ("correct_sp_kA", 3.40),
                        ("brine_m3h", 18.0),
                        ("t_gate_us", 5920),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 4.62 kA on SP.LIVE: SP.SHADOW already holds 3.40 kA "
                "under the 4.20 kA cap, so the 4.62 kA live header is treated as an unvalidated "
                "crosstalk spike rather than an over-cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Live header 4.62 kA exceeds the 4.20 kA cap (true). Apply the 3.40 kA clamp "
                "on SP.SHADOW, which already holds the legal recipe. Magnitude is the legal 3.40 kA; "
                "the tag is not the live loop.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "live_kA",
                            OrderedDict(
                                [
                                    ("cap", 4.20),
                                    ("observed", 4.62),
                                    ("shadow", 3.40),
                                    ("written_tag", "SP.SHADOW"),
                                    ("correct_at_t_gate_kA", 3.40),
                                    ("correct_tag", "SP.LIVE"),
                                    ("live_sp_untouched", True),
                                ]
                            ),
                        ),
                        (
                            "tag_bind",
                            OrderedDict(
                                [
                                    ("t_gate_us", 5920),
                                    ("extra_shadow_write", True),
                                    ("live_untouched", True),
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
            ("name", "shadow_sp_write"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("clamp_kA", 3.40),
                        ("written_tag", "SP.SHADOW"),
                        ("extra_shadow_write", True),
                        ("live_sp_kA", 4.62),
                        ("brine_m3h", 18.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / shadow-setpoint): correct 3.40 kA clamp written to SP.SHADOW. "
                "SP.LIVE stays 4.62 kA. Routing relay.ct.live -> policy.shadow_sp; no "
                "positive weight to policy.live_sp.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY applied the correct 1.6 t/h steam cut to idle string B. Live 18.4 bar "
                "was over the 16.0 bar cap at t_gate; idle 2.1 bar was already IDLE. Peak 20.2 bar "
                "lifted the PSV. 14 min dump/reseal (abort_s=840). Correct gate was MODIFY steam "
                "4.8 -> 1.6 t/h on string A at t_gate_us=5920.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live_A", "untouched 4.8 t/h steam; peak 20.2 > 16.0 cap"),
                        ("idle_B", "cut to 1.6 t/h on an already IDLE rinse bank"),
                        ("reseal", "14 min dump/reseal, string A reseed"),
                        ("mission", "digest deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-first was the correct order and the pressure number was over cap; the MODIFY spent that win on the idle parallel bank.",
                    "Delayed (abort_s=840): SH-3 holds 14 min while string A is dumped and resealed; next digest 16 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY steam 4.8 -> 1.6 t/h on string A at t_gate_us=5920; wrong_string=false; leave slurry at 6.4 t/h.",
                        ),
                        ("correct_actuator", "steam_cut_string_A"),
                        ("wrong_bind", "idle_string_B"),
                        ("live_string", "A"),
                        ("acted_string", "B"),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("steam_tph", 1.6),
                                    ("acted_string", "B"),
                                    ("wrong_string", True),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "14 min dump/reseal (task/efficiency); live A peaked 20.2 bar during the idle-string bind (safety near-miss of a correct-magnitude clamp on the wrong bank).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.live.A.bar (5.400 ms, 18.4 bar)"),
                        ("loser", "pt.idle.B.bar (5.580 ms, 2.1 bar IDLE)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Idle-first by < 180 us would still be a 2.1 bar IDLE string under the "
                            "16.0 bar cap; a correct gate binds pt.live.A.bar to policy.live_clamp at "
                            "t_gate either way. The wrong MODIFY spent the live win on string B.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5920),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the idle-string bind (5.920 ms, tick 4). "
                "The 14 min dump/reseal is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 840),
        ]
    )
    dw = 0.34
    ras = raster_core(
        28,
        88,
        34,
        84,
        routing(
            "thalamic-relay.apt-string",
            "spikenaut.policy.idle-clamp",
            [
                ("relay.pt.live", "policy.idle_clamp", 0.74),
                ("relay.pt.idle", "policy.idle_clamp", 0.21),
            ],
            "acetylcholine",
            0.08,
            "timing_cap_stdp; ACh tags the (wrong) idle_clamp bind at the live win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 840),
                ("delayed_surprise_s", 840),
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
                    pop_budget("idle_clamp", 48, 0.45, 300.0, dw),
                    pop("live_clamp", 48, 0.90),
                    pop("idle_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r61-322"),
            (
                "title",
                "WRONG-MODIFY at Scheelite-Howe SH-3 / Autoclave A-2: live 18.4 bar read correctly; "
                "correct 1.6 t/h steam cut applied to idle string B (wrong-string / live-vs-idle)",
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
                    "Wrong-modify / wrong-string live-vs-idle. Sidecar arithmetic 18.4 > 16.0 on live "
                    "is true; MODIFY bound to idle_clamp. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "tungsten-apt-autoclave",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-string",
                        "live-vs-idle",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live-first race can still be a wrong gate "
                    "when the MODIFY writes a correct-magnitude clamp onto an IDLE parallel bank. "
                    "Convictable from string ids, idle status, and routing without autoclave physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_323():
    ticks = [
        tick(2736, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6840, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7020, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7640, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(7960, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.ram.bar", 1.360, 0.40),
        spike("ae.neck.pps", 2.736, 0.56),
        spike("enc.ram.bar", 4.100, 0.48),
        spike("ae.neck.pps", 6.840, 1.34),
        spike("enc.ram.bar", 7.020, 1.11),
        spike("ctrl.gate", 7.640, 0.98),
        spike("ae.neck.pps", 10.400, 0.81),
        spike("enc.ram.bar", 14.800, 0.62),
        spike("ctrl.gate", 18.200, 0.84),
        spike("ae.neck.pps", 28.400, 0.52),
        spike("enc.ram.bar", 36.100, 0.39),
        spike("ae.neck.pps", 42.200, 0.44),
    ]
    excerpt = independent_excerpt(61323, 120, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Necker N-6 on the Celestine-Brae CB-HIL can-stand sees AE at 52 pps while ram "
                "hydraulics sit at 4.8 bar under a 7.0 bar cap. AE-first holds the can; ram-first "
                "would dispatch 180 cpm because the ram looks legal. The HIL necker mockup is the "
                "authority, not the filler floor.",
            ),
            ("domain", "can-necker-flanger"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep N-6 from dispatching a split-neck can while ram pressure remains under "
                "its own cap.",
            ),
            ("t0_us", 1756850400000323),
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
                                "ae.neck.pps 52 over 15 cap",
                                "enc.ram.bar 4.8 under 7.0 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; ram-first dispatches 180 cpm on a "
                            "'ram still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one AE puck slot versus the ram-PT publisher on this "
                            "HIL necker-flanger bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + ram 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have dispatched 180 cpm into a split neck.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "necker AE puck, 50 kHz, 26 us jitter",
                    "ram hydraulic PT, 1 kHz, 32 us jitter",
                    "starwheel tach (context)",
                    "infeed IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 15.0),
                        ("observed_ae_pps", 52.0),
                        ("ram_bar", 4.8),
                        ("ram_cap_bar", 7.0),
                        ("proposed_cpm", 180.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. N-6 HIL indexed; 180 cpm armed.",
                    "2. Ram 4.8 bar under 7.0; AE 52 pps over 15.",
                    "3. Ram precursor at 1.360 ms.",
                    "4. Race window [6.840, 7.160] ms.",
                    "5. ae.neck.pps 52 at 6.840 ms (winner).",
                    "6. enc.ram.bar 4.8 at 7.020 ms (loser by 180 us).",
                    "7. Gate at 7.640 ms: REJECT hold, do not dispatch.",
                    "8. Cycle 0 cpm; ram left at 4.8 bar.",
                    "9. Neck inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min tool reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_neck"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cpm", 180.0),
                        ("hold", False),
                        ("ram_bar", 4.8),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 52.0),
                        ("ae_cap_pps", 15.0),
                        ("ram_bar", 4.8),
                        ("ram_cap_bar", 7.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 180 cpm because ram 4.8 bar is under 7.0, treating the "
                "52 pps AE as starwheel chatter rather than a split neck.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Necker AE 52 pps won by 180 us, so the can is split, not still a ram-pressure "
                "story. Ram 4.8 bar is under 7.0 and does not authorize dispatch. REJECT: hold "
                "cycle 180 -> 0 cpm. A MODIFY that only trims ram would leave the split neck.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ae_pps",
                            OrderedDict(
                                [
                                    ("cap", 15.0),
                                    ("observed", 52.0),
                                    ("executed_cpm", 0.0),
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
            ("name", "hold_necker"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cpm", 0.0),
                        ("hold", True),
                        ("ram_bar", 4.8),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: cycle 180 -> 0 cpm. Ram left at 4.8 bar under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held N-6. AE 52 pps beat ram 4.8 bar by 180 us. Ram was "
                "legal; the neck was not. 8 min tool reset (abort_s=480) is delayed survey, "
                "not a process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("cycle", "held at 0 cpm"),
                        ("ram", "left 4.8 bar < 7.0 cap"),
                        ("tool", "8 min tool reset (abort_s=480)"),
                        ("mission", "HIL can not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Ram PT never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min tool reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.neck.pps (6.840 ms, 52 pps)"),
                        ("loser", "enc.ram.bar (7.020 ms, 4.8 bar)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Ram-first by < 180 us inside the 320 us window would have dispatched "
                            "180 cpm into a split neck. The REJECT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7640),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.640 ms, tick 4). The 8 min tool "
                "reset is delayed surprise, not the inflection.",
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
            "thalamic-relay.neck-ae",
            "spikenaut.policy.neck-hold",
            [
                ("relay.ae.neck", "policy.neck_hold", 0.70),
                ("relay.enc.ram", "policy.ram_go", 0.24),
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
                    pop_budget("neck_hold", 56, 0.45, 280.0, dw),
                    pop("ram_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r61-323"),
            (
                "title",
                "Celestine-Brae CB-HIL / Necker N-6: neck AE 52 pps beats ram 4.8 bar by "
                "180 us; correct REJECT holds the can",
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
                    "Correct REJECT. AE 52 > 15 cap beats legal ram. "
                    "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "can-necker-flanger",
                    [
                        "reject",
                        "hil",
                        "ae-vs-ram",
                        "split-neck",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal ram header can lose to necker AE inside a 320 us "
                    "window; reversing 180 us would have dispatched a split neck.",
                    3,
                ),
            ),
        ]
    )


def record_324():
    ticks = [
        tick(2880, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7200, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7380, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7840, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8200, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("ir.kiln.C", 1.200, 0.40),
        spike("gc.so2.ppm", 2.880, 0.55),
        spike("ir.kiln.C", 4.400, 0.48),
        spike("gc.so2.ppm", 7.200, 1.26),
        spike("ir.kiln.C", 7.380, 1.08),
        spike("ctrl.gate", 7.840, 0.95),
        spike("gc.so2.ppm", 11.200, 0.78),
        spike("ir.kiln.C", 14.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("gc.so2.ppm", 22.600, 0.50),
        spike("ir.kiln.C", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(61324, 48, 28000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("kiln_rph", 1.4),
            ("so2_ppm", 42.0),
            ("shell_C", 980.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Cracking kiln K-9 at Bastnasite-Holt BH-5 is already at 1.4 rph with stack SO2 "
                "42 ppm against an 80 ppm cap. Shell IR leftover is 980 C under a 1050 C cap. "
                "SO2-first accepts the 1.4 rph rotate; IR-first would have rejected a legal crack "
                "on a 'still climbing' model.",
            ),
            ("domain", "rare-earth-cracking-kiln"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the BH-5 rotate with stack SO2 <= 80 ppm and shell IR <= 1050 C.",
            ),
            ("t0_us", 1756850400000324),
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
                                "gc.so2.ppm 42 under 80 cap",
                                "ir.kiln.C 980 under 1050 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "SO2-first confirms the already-legal 1.4 rph rotate; IR-first "
                            "would have treated the GC as a climb echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one stack-SO2 GC slot versus the shell-IR publisher "
                            "on this simulated cracking-kiln bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (GC 26 + IR 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed rotate illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "stack-SO2 GC, 26 us jitter",
                    "shell IR pyrometer, 32 us jitter",
                    "kiln tach (context)",
                    "draft PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("so2_cap_ppm", 80.0),
                        ("observed_so2_ppm", 42.0),
                        ("shell_cap_C", 1050.0),
                        ("observed_shell_C", 980.0),
                        ("hf_cap_ppm", 4.0),
                        ("observed_hf_ppm", 1.6),
                        ("proposed_kiln_rph", 1.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. K-9 indexed on Bastnasite-Holt BH-5; 1.4 rph rotate armed.",
                    "2. Caps: SO2 80 ppm, HF 4.0 ppm, shell 1050 C.",
                    "3. IR precursor at 1.200 ms.",
                    "4. Race window [7.200, 7.560] ms.",
                    "5. gc.so2.ppm 42 at 7.200 ms (winner).",
                    "6. ir.kiln.C 980 at 7.380 ms (loser by 180 us).",
                    "7. Gate at 7.840 ms: ACCEPT 1.4 rph already legal.",
                    "8. Rotate continues; no extra hold.",
                    "9. 6 min survey confirms SO2 still under 80 ppm.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "rotate_1p4"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("so2_ppm", 42.0),
                        ("so2_cap_ppm", 80.0),
                        ("shell_C", 980.0),
                        ("shell_cap_C", 1050.0),
                        ("hf_ppm", 1.6),
                        ("hf_cap_ppm", 4.0),
                        ("kiln_rph", 1.4),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 1.4 rph rotate because SO2 42 ppm is under 80 and shell "
                "980 C is under 1050 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Stack SO2 42 ppm won by 180 us and is under 80 ppm. Shell 980 C is under "
                "1050 C. HF 1.6 ppm is under 4.0. ACCEPT the already-legal rotate.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "so2_ppm",
                            OrderedDict(
                                [
                                    ("cap", 80.0),
                                    ("observed", 42.0),
                                    ("executed_kiln_rph", 1.4),
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
            ("name", "rotate_1p4"),
            ("parameters", OrderedDict(params.items())),
            (
                "gate_effect",
                "ACCEPT: 1.4 rph rotate and 42 ppm SO2 unchanged. Routing relay.gc.so2 -> "
                "policy.kiln_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left K-9 on a 1.4 rph / 42 ppm rotate. Shell IR hitch did not "
                "justify a hold. 6 min survey confirmed SO2 still under 80 ppm.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("kiln", "still 1.4 rph"),
                        ("so2", "42 ppm under 80 cap"),
                        ("shell", "980 C under 1050"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Shell IR 980 C hitch is residual, not a superheat trip.",
                    "Delayed (survey_s=360): 6 min survey restacks K-9 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "gc.so2.ppm (7.200 ms, 42 ppm)"),
                        ("loser", "ir.kiln.C (7.380 ms, 980 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 180 us would only delay confirmation. The rotate stays "
                            "legal either way; ACCEPT is still required.",
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
            "thalamic-relay.so2-gc",
            "spikenaut.policy.kiln-go",
            [
                ("relay.gc.so2", "policy.kiln_go", 0.68),
                ("relay.ir.kiln", "policy.ir_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_kiln_stdp; 5-HT tags the kiln_go bind at the GC win",
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
                    pop_budget("kiln_go", 40, 0.45, 250.0, dw),
                    pop("ir_hold", 32, 0.90),
                    pop("so2_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r61-324"),
            (
                "title",
                "Bastnasite-Holt BH-5 / Kiln K-9: stack SO2 42 ppm beats shell IR 980 C "
                "by 180 us; ACCEPT already-legal 1.4 rph rotate",
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
                    "Correct ACCEPT of an already-legal cracking-kiln rotate. total +1.06 = "
                    "0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "rare-earth-cracking-kiln",
                    [
                        "accept",
                        "already-legal",
                        "simulated-kiln-loop",
                        "gc-vs-ir",
                        "sidecar-convictable",
                        "simulated",
                    ],
                    "Teaches that a stack-SO2 GC under cap can confirm an already-legal "
                    "rotate without a shell-IR hitch becoming a hold.",
                    4,
                ),
            ),
        ]
    )


def record_325():
    ticks = [
        tick(2016, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5040, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5920, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(300000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("ph.leach", 0.980, 0.41),
        spike("gc.li.pct", 2.016, 0.60),
        spike("ph.leach", 3.200, 0.51),
        spike("gc.li.pct", 5.040, 1.30),
        spike("ph.leach", 5.200, 1.12),
        spike("ctrl.gate", 5.640, 0.97),
        spike("gc.li.pct", 8.100, 0.78),
        spike("ph.leach", 12.400, 0.62),
        spike("ctrl.gate", 16.200, 0.85),
        spike("gc.li.pct", 20.400, 0.54),
        spike("ph.leach", 22.800, 0.43),
    ]
    excerpt = independent_excerpt(61325, 80, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("leach_m3h", 3.2),
            ("li_wt_pct", 0.08),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Leach tank L-3 at Spodumene-Noll SN-8 is already at 3.2 m3/h with residual lithium "
                "0.08 wt percent against a 0.20 cap and pH 1.8 under 2.5. Lithium-first accepts the "
                "flow; pH-first would have rejected a legal leach on a 'still acidifying' model.",
            ),
            ("domain", "lithium-sulfate-leach"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run L-3 at 3.2 m3/h, keep residual Li <= 0.20 wt percent and pH <= 2.5, and "
                "leave the circuit on schedule.",
            ),
            ("t0_us", 1756850400000325),
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
                                "gc.li.pct 0.08 under 0.20 cap",
                                "ph.leach 1.8 under 2.5 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Lithium-first confirms the already-legal 3.2 m3/h flow; pH-first "
                            "would have treated the GC as a hitch echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one residual-Li XRF slot versus the pH-probe publisher on this "
                            "sulfate-leach bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (Li 22 + pH 30): 3.08x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal flow.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "residual-Li XRF, 2 kHz, 22 us jitter",
                    "leach pH probe, 1 kHz, 30 us jitter",
                    "acid FT (context)",
                    "agitator tach (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("li_cap_wt_pct", 0.20),
                        ("observed_li_wt_pct", 0.08),
                        ("leach_m3h", 3.2),
                        ("leach_cap_m3h", 4.0),
                        ("ph", 1.8),
                        ("ph_cap", 2.5),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Tank L-3 indexed on Spodumene-Noll SN-8; leach 3.2 m3/h armed.",
                    "2. Residual Li 0.08 under 0.20; pH 1.8 under 2.5.",
                    "3. pH precursor at 0.980 ms.",
                    "4. Race window [5.040, 5.320] ms.",
                    "5. gc.li.pct 0.08 at 5.040 ms (winner).",
                    "6. ph.leach 1.8 at 5.200 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 3.2 m3/h.",
                    "8. Li stays 0.08; flow stays 3.2 m3/h.",
                    "9. Residue exits L-3 on-spec.",
                    "10. Delayed (dwell_s=300): 5 min filter reseq.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_leach_flow"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("li_wt_pct", 0.08),
                        ("li_cap_wt_pct", 0.20),
                        ("leach_m3h", 3.2),
                        ("leach_cap_m3h", 4.0),
                        ("ph", 1.8),
                        ("ph_cap", 2.5),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 3.2 m3/h because residual Li 0.08 wt percent is under 0.20 and "
                "pH 1.8 is under 2.5.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Residual Li 0.08 wt percent won by 160 us, so the flow is already legal, not still "
                "acidifying. pH 1.8 is under 2.5. ACCEPT the 3.2 m3/h flow. A REJECT would idle a "
                "legal leach tank.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "li_wt_pct",
                            OrderedDict(
                                [
                                    ("cap", 0.20),
                                    ("observed", 0.08),
                                    ("executed_leach_m3h", 3.2),
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
            ("name", "hold_leach_flow"),
            ("parameters", OrderedDict(params.items())),
            ("gate_effect", "ACCEPT: leave 3.2 m3/h; residual Li 0.08; pH legal."),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 3.2 m3/h flow. Residual Li 0.08 beat pH 1.8 "
                "by 160 us. 5 min filter reseq (dwell_s=300) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("flow", "3.2 m3/h held"),
                        ("lithium", "0.08 wt percent < 0.20 cap"),
                        ("tank", "L-3 on-spec"),
                        ("reseq", "5 min filter reseq (dwell_s=300)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "pH probe never approached 2.5; residual Li was already under cap.",
                    "Delayed (dwell_s=300): 5 min filter reseq after L-3.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "gc.li.pct (5.040 ms, 0.08 wt percent)"),
                        ("loser", "ph.leach (5.200 ms, 1.8)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "pH-first by < 160 us inside the 280 us window would have REJECTED "
                            "an already-legal flow. The ACCEPT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5640),
            (
                "reward_inflection_note",
                "Task and safety rise at the correct ACCEPT (5.640 ms, tick 4). The 5 min reseq "
                "is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 300),
        ]
    )
    dw = 0.28
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.li-xrf",
            "spikenaut.policy.leach-go",
            [
                ("relay.gc.li", "policy.leach_go", 0.67),
                ("relay.ph.leach", "policy.leach_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the residual-Li win as an already-legal flow",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("dwell_s", 300),
                ("delayed_surprise_s", 300),
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
                    pop_budget("leach_go", 40, 0.45, 250.0, dw),
                    pop("leach_hold", 32, 0.90),
                    pop("li_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r61-325"),
            (
                "title",
                "Spodumene-Noll SN-8 / Tank L-3: residual Li 0.08 wt percent beats pH 1.8 by 160 us; "
                "correct ACCEPT of an already-legal 3.2 m3/h flow",
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
                    "Correct ACCEPT of an already-legal sulfate-leach flow. total +1.14 = "
                    "0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "lithium-sulfate-leach",
                    [
                        "accept",
                        "already-legal",
                        "li-vs-ph",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches that residual-Li under cap can confirm an already-legal leach "
                    "flow without a pH hitch becoming a hold.",
                    5,
                ),
            ),
        ]
    )
