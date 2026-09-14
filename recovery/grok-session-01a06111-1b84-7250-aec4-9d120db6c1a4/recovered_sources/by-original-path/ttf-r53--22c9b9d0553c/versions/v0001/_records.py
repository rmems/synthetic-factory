def lif_281_excerpt():
    n = 72
    dt_us = 100
    tau_m_ms = 18.5
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.90
    i_stim_peak = 2.50
    stim = (22000, 25200)
    seed = 53281
    window_us = 42000
    i_clamp_extra = 0.66
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
    burst = [(t, nid) for t, nid in spikes if 22000 <= t < 25200]
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
    take(burst, 8, label_times=(22600, 23400, 24400))
    clamp = [(t, nid) for t, nid in picked if t < 22000][:7]
    tear = [(t, nid) for t, nid in picked if t >= 22000][:8]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(f"LIF excerpt too short {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.cyclone" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 72),
            ("dt_us", 100),
            ("tau_m_ms", 18.5),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.90),
            ("i_stim_peak", 2.50),
            ("stim_t_us", [22000, 25200]),
            ("i_clamp_extra", 0.66),
            ("clamp_n", 14),
            ("seed", 53281),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.66 air-clamp bias; stim 22.0-25.2 ms is the cyclone dipleg collapse.",
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


def record_281():
    excerpt, extra = lif_281_excerpt()
    ticks = [
        tick(2180, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(5340, 0.07, -0.04, -0.03, 0.01, -0.01),
        tick(5520, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6120, 0.08, -0.06, -0.03, 0.02, -0.01),
        tick(22600, 0.04, -0.42, -0.04, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Roaster R-4 inside Gossan-Weald GW-8 is already running a 14.2 kNm3/h air latch while "
                "bed IR sits at 912 C against a 890 C license. Therm-first drops air 14.2 -> 11.6 "
                "kNm3/h and holds bed at 878 C; encoder-first would keep 14.2 because the 0.8 percent "
                "leftover looks like a still-warming pass. A cyclone dipleg already packed with "
                "calcine does not appear on bed IR or air until the AE collapse.",
            ),
            ("domain", "fluid-bed-roaster"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep GW-8 Roaster R-4 bed IR <= 890 C and finish the pass without collapsing "
                "the cyclone dipleg onto the bed.",
            ),
            ("t0_us", 1756867200000281),
            ("gate_latency_us", 780),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.34, 5.70]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.bed.C 912 C over 890 C license",
                                "enc.air.knm3h 14.2 with 0.8 pct residual",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first latches air 14.2 -> 11.6 kNm3/h (roast-bed clamp); air-first "
                            "keeps 14.2 kNm3/h on a 'still warming' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one bed-IR pyrometer slot versus the air-flow encoder "
                            "publisher on this fluid-bed roast bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (IR 28 + air 32): 3.00x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us window "
                            "would have kept 14.2 kNm3/h; predicted next-sample 904 C > 890 C cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed IR pyrometer, 2 kHz, 28 us jitter",
                    "air-flow encoder, 1 kHz, 32 us jitter",
                    "cyclone AE puck (context)",
                    "freeboard PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 890.0),
                        ("observed_bed_C", 912.0),
                        ("air_knm3h", 14.2),
                        ("freeboard_kPa", 18.4),
                        ("freeboard_cap_kPa", 24.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. R-4 indexed; air 14.2 kNm3/h; bed IR 912 C.",
                    "2. Freeboard 18.4 kPa under 24.0; roast armed.",
                    "3. Air precursor at 1.220 ms.",
                    "4. Race window [5.340, 5.700] ms.",
                    "5. ir.bed.C 912 at 5.340 ms (winner).",
                    "6. enc.air.knm3h 14.2 at 5.520 ms (loser by 180 us).",
                    "7. Gate at 6.120 ms: MODIFY clamp 14.2 -> 11.6 kNm3/h.",
                    "8. After clamp bed 878 C <= 890; freeboard still 18.4 kPa.",
                    "9. At 22.600 ms a cyclone dipleg collapse dumps 0.6 t calcine.",
                    "10. 15 min dipleg isolate (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_roast_air"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_knm3h", 14.2),
                        ("bed_C", 912.0),
                        ("freeboard_kPa", 18.4),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 912.0),
                        ("bed_cap_C", 890.0),
                        ("predicted_unclamped_next_C", 904.0),
                        ("air_knm3h", 14.2),
                        ("freeboard_kPa", 18.4),
                        ("freeboard_cap_kPa", 24.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 14.2 kNm3/h because freeboard 18.4 kPa is under 24.0, treating "
                "the 912 C bed as a still-warming IR rather than a license miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed IR 912 C won by 180 us, so the roast is over license, not still a freeboard "
                "story. Holding 14.2 kNm3/h predicts next-sample 904 C > 890 C cap. MODIFY: air "
                "14.2 -> 11.6 kNm3/h. Observed after clamp 878 C <= 890. A full REJECT is not "
                "indicated: a clean roast accepts 11.6.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 890.0),
                                    ("observed", 912.0),
                                    ("predicted_unclamped_next", 904.0),
                                    ("clamped_air_knm3h", 11.6),
                                    ("observed_after_clamp", 878.0),
                                ]
                            ),
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
            ("name", "clamped_roast_air"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_knm3h", 11.6),
                        ("bed_C", 878.0),
                        ("freeboard_kPa", 18.4),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: air 14.2 -> 11.6 kNm3/h. Process-correct vs the 890 C bed license. "
                "Cyclone dipleg still collapses at 22.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held bed IR at 878 C. At 22.600 ms a cyclone dipleg "
                "already packed with calcine dumped 0.6 t onto the bed. Clamp reduced dump "
                "energy; it did not prevent the collapse. Partnered negative: process heads stay "
                "honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bed", "clamp executed; peak 878 C <= 890 cap"),
                        ("cyclone", "dipleg collapsed at 22.600 ms; 0.6 t calcine"),
                        ("repair", "15 min dipleg isolate (abort_s=900)"),
                        ("mission", "GW-8 roast incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither bed IR nor air encoder predicted the packed cyclone dipleg; ae.cyclone.dip is a new channel at 22.600 ms, 16.480 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min dipleg isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min dipleg isolate after the cyclone collapse. Safety head -0.62 prices the "
                "dump; task_progress stays +0.30 because the air clamp completed under the 890 C "
                "cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.bed.C (5.340 ms, 912 C)"),
                        ("loser", "enc.air.knm3h (5.520 ms, 14.2 kNm3/h)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Air-first by < 180 us inside the 360 us window would have kept "
                            "14.2 kNm3/h; predicted next-sample 904 C would have missed the 890 C "
                            "cap even without the dipleg collapse. The MODIFY is still the correct "
                            "process. The collapse is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22600),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.600 ms cyclone dump (tick t_us=22600), inside the 42 ms "
                "raster. The correct MODIFY at 6.120 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=900 isolation tick.",
            ),
            ("delayed_surprise_s", 900),
        ]
    )
    spikes = [
        spike("enc.air.knm3h", 1.220, 0.41),
        spike("ir.bed.C", 2.180, 0.58),
        spike("enc.air.knm3h", 3.460, 0.50),
        spike("ir.bed.C", 5.340, 1.31),
        spike("enc.air.knm3h", 5.520, 1.12),
        spike("ctrl.gate", 6.120, 0.97),
        spike("ir.bed.C", 8.200, 0.82),
        spike("enc.air.knm3h", 10.600, 0.64),
        spike("ctrl.gate", 14.400, 0.86),
        spike("ae.cyclone.dip", 22.600, 1.48),
        spike("ae.cyclone.dip", 24.200, 0.93),
        spike("enc.air.knm3h", 30.400, 0.40),
        spike("ir.bed.C", 36.800, 0.55),
    ]
    dw = 0.36
    ras = raster_core(
        42,
        72,
        28,
        85,
        routing(
            "thalamic-relay.roast-bed",
            "spikenaut.policy.air-clamp",
            [
                ("relay.ir.bed", "policy.air_clamp", 0.69),
                ("relay.air.knm3h", "policy.air_hold", 0.28),
                ("relay.ae.cyclone", "policy.air_clamp", -0.44),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at bed-IR win (5.340 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.600 ms cyclone collapse",
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
                    pop_budget("air_clamp", 50, 0.50, 220.0, dw),
                    pop_budget("air_hold", 40, 0.80, 50.0, dw),
                    pop("cyclone_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r53-281"),
            (
                "title",
                "Gossan-Weald GW-8 / Roaster R-4: bed IR 912 C beats air 14.2 kNm3/h by 180 us; "
                "correct MODIFY still eats an in-window cyclone dipleg collapse (partnered negative total -0.48)",
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
                    "42 ms raster. total -0.48 = 0.30 + -0.62 + -0.16 + 0.04 + -0.04. Named "
                    "dipleg isolate (abort_s=900) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "fluid-bed-roaster",
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
                    "15 min dipleg isolate.",
                    1,
                ),
            ),
        ]
    )


def record_282():
    ticks = [
        tick(2100, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5480, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5660, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6280, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6640, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("an.acid.lag", 1.080, 0.42),
        spike("an.acid.live", 2.100, 0.57),
        spike("an.acid.lag", 3.420, 0.49),
        spike("an.acid.live", 5.480, 1.29),
        spike("an.acid.lag", 5.660, 1.10),
        spike("ctrl.gate", 6.280, 0.96),
        spike("enc.olefin.tph", 8.400, 0.80),
        spike("an.acid.live", 10.600, 0.63),
        spike("ctrl.gate", 14.200, 0.84),
        spike("an.acid.lag", 18.800, 0.41),
        spike("an.acid.live", 22.400, 0.54),
        spike("enc.olefin.tph", 25.600, 0.38),
    ]
    excerpt = independent_excerpt(53282, 96, 26000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Contactor C-7 at Raffinate-Holt RH-3 is already on the sulfuric alkylation hold "
                "with live acid at 86.8 wt percent against a 90.0 wt percent floor. A lagged DCS "
                "tag still shows 92.4 wt percent from the previous regen, age 48 s over an 8 s "
                "freshness cap. Live-first should cut olefin 18.0 -> 9.0 t/h; a weak supervisor "
                "treats the lagged 92.4 as live and bumps olefin 18.0 -> 22.0 t/h.",
            ),
            ("domain", "alkylation-contactor"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the RH-3 hold with live acid >= 90.0 wt percent, leave the lagged tag on "
                "its own bus, and keep olefin at a legal 9.0 t/h cut.",
            ),
            ("t0_us", 1756867200000282),
            ("gate_latency_us", 560),
            ("race_window_us", 340),
            ("race_window_rel_ms", [5.48, 5.82]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "an.acid.live 86.8 wt pct under 90.0 floor",
                                "an.acid.lag 92.4 wt pct age 48 s over 8 s cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-first should latch olefin cut 18.0 -> 9.0 t/h at t_gate; "
                            "lag-first is a false 'regen complete' bump 18.0 -> 22.0 t/h.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live acid-titration slot versus the lagged DCS tag "
                            "publisher on this alkylation PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (live 28 + lag 32). Order is "
                            "correctly live-first. The error is which sample the MODIFY binds, "
                            "not which actuator exists.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live acid titrator, 2 kHz, 28 us jitter, phase=hold",
                    "lagged DCS acid tag, 1 kHz, 32 us jitter, age_s=48",
                    "olefin Coriolis (context)",
                    "contactor DT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("acid_floor_wt_pct", 90.0),
                        ("observed_acid_live_wt_pct", 86.8),
                        ("observed_acid_lag_wt_pct", 92.4),
                        ("tag_age_s", 48.0),
                        ("max_legal_tag_age_s", 8.0),
                        ("cycle_phase", "hold"),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. C-7 already in alkylation hold; live acid 86.8 wt percent.",
                    "2. Lagged DCS tag 92.4 wt percent, age 48 s > 8 s freshness.",
                    "3. Lag precursor at 1.080 ms.",
                    "4. Race window [5.480, 5.820] ms.",
                    "5. an.acid.live 86.8 at 5.480 ms (winner).",
                    "6. an.acid.lag 92.4 at 5.660 ms (loser by 180 us).",
                    "7. Gate at 6.280 ms: WRONG-MODIFY binds lagged tag (stale-sample).",
                    "8. Olefin bumped 18.0 -> 22.0 t/h; live acid falls to 84.1 wt percent.",
                    "9. Acid dump / isobutane recycle.",
                    "10. Delayed (abort_s=720): 12 min acid dump while C-7 is reseeded.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_olefin_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("olefin_tph", 18.0),
                        ("acid_live_wt_pct", 86.8),
                        ("acid_lag_wt_pct", 92.4),
                        ("bind_lagged_tag", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("acid_live_wt_pct", 86.8),
                        ("acid_lag_wt_pct", 92.4),
                        ("acid_floor_wt_pct", 90.0),
                        ("tag_age_s", 48.0),
                        ("max_legal_tag_age_s", 8.0),
                        ("cycle_phase", "hold"),
                        ("t_gate_us", 6280),
                        ("correct_olefin_tph", 9.0),
                        ("executed_olefin_tph", 22.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 18.0 t/h olefin: lagged DCS 92.4 wt percent looks "
                "over the 90.0 floor, so the 86.8 live titrator is treated as a still-wet cell.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Lagged acid 92.4 wt percent is over the 90.0 floor (true on the shadow tag). "
                "Regen looks complete, so bump olefin 18.0 -> 22.0 t/h to recover rate. Leave "
                "the live 86.8 reading as a wet-cell transient.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "acid_wt_pct",
                            OrderedDict(
                                [
                                    ("floor", 90.0),
                                    ("observed_live", 86.8),
                                    ("observed_lag", 92.4),
                                    ("tag_age_s", 48.0),
                                    ("max_legal_tag_age_s", 8.0),
                                    ("correct_olefin_tph", 9.0),
                                    ("executed_olefin_tph", 22.0),
                                ]
                            ),
                        ),
                        (
                            "sample",
                            OrderedDict(
                                [
                                    ("bind_lagged_tag", True),
                                    ("stale", True),
                                    ("live_under_floor", True),
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
            ("name", "olefin_bump_on_lagged_tag"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("olefin_tph", 22.0),
                        ("acid_live_wt_pct", 84.1),
                        ("acid_lag_wt_pct", 92.4),
                        ("bind_lagged_tag", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / stale-sample): olefin bumped 18.0 -> 22.0 t/h on lagged "
                "92.4 wt percent while live 86.8 is under the 90.0 floor. Routing "
                "relay.an.acid.lag -> policy.olefin_bump; no positive weight to policy.olefin_cut.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY bound the lagged 92.4 wt percent tag and bumped olefin 18.0 -> "
                "22.0 t/h. Live acid 86.8 was under the 90.0 floor at t_gate; tag age 48 s > 8 s. "
                "Live acid fell to 84.1 wt percent. 12 min acid dump (abort_s=720). Correct gate "
                "was MODIFY olefin 18.0 -> 9.0 t/h on the live titrator.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("olefin", "bumped 22.0 t/h on lagged tag; live acid 84.1 < 90.0 floor"),
                        ("acid", "dump / isobutane recycle"),
                        ("recycle", "12 min acid dump, C-7 reseed"),
                        ("mission", "hold deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-first was the correct order and the live number was under floor; the MODIFY spent that win on a lagged regen-complete bump.",
                    "Delayed (abort_s=720): RH-3 holds 12 min while C-7 is dumped and reseeded; next alkylate 14 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY olefin 18.0 -> 9.0 t/h on live 86.8 wt percent; bind_lagged_tag=false; leave lagged 92.4 on its own bus.",
                        ),
                        ("correct_actuator", "olefin_feed"),
                        ("wrong_sample", "lagged_dcs_tag"),
                        ("tag_age_s", 48.0),
                        ("max_legal_tag_age_s", 8.0),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("olefin_tph", 22.0),
                                    ("bind_lagged_tag", True),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min acid dump (task/efficiency); live acid fell to 84.1 wt percent on a stale-tag olefin bump (safety near-miss of a live-under-floor cut).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "an.acid.live (5.480 ms, 86.8 wt percent)"),
                        ("loser", "an.acid.lag (5.660 ms, 92.4 wt percent, age 48 s)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Lag-first by < 180 us would still be a stale 92.4 reading; "
                            "a correct gate binds an.acid.live to policy.olefin_cut at t_gate "
                            "either way. The wrong MODIFY spent the live win on a lagged bump.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6280),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the lagged-tag bind (6.280 ms, tick 4). "
                "The 12 min acid dump is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 720),
        ]
    )
    dw = 0.34
    ras = raster_core(
        26,
        96,
        32,
        80,
        routing(
            "thalamic-relay.acid-lag",
            "spikenaut.policy.olefin-bump",
            [
                ("relay.an.acid.lag", "policy.olefin_bump", 0.75),
                ("relay.an.acid.live", "policy.olefin_bump", 0.18),
            ],
            "acetylcholine",
            0.08,
            "sample_cap_stdp; ACh tags the (wrong) olefin_bump bind at the live win",
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
                    pop_budget("olefin_bump", 48, 0.45, 300.0, dw),
                    pop("olefin_cut", 48, 0.90),
                    pop("lag_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r53-282"),
            (
                "title",
                "WRONG-MODIFY at Raffinate-Holt RH-3 / Contactor C-7: live acid 86.8 wt percent "
                "read correctly; olefin bumped 18->22 t/h on a lagged 92.4 tag (stale-sample)",
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
                    "Wrong-modify / stale-sample. Sidecar arithmetic 86.8 < 90.0 live and "
                    "tag_age 48 > 8 is true; MODIFY bound to olefin_bump. "
                    "total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "alkylation-contactor",
                    [
                        "modify",
                        "wrong-gate",
                        "stale-sample",
                        "lagged-tag",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live-first race can still be a wrong gate "
                    "when the MODIFY binds a lagged DCS tag past max_legal_tag_age_s. "
                    "Convictable from tag ages and routing to without alkylation physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_283():
    ticks = [
        tick(2680, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6840, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7020, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7620, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(7940, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.flue.o2", 1.360, 0.40),
        spike("ae.pitch.pps", 2.680, 0.56),
        spike("enc.flue.o2", 4.100, 0.48),
        spike("ae.pitch.pps", 6.840, 1.34),
        spike("enc.flue.o2", 7.020, 1.11),
        spike("ctrl.gate", 7.620, 0.98),
        spike("ae.pitch.pps", 10.200, 0.81),
        spike("enc.flue.o2", 14.600, 0.62),
        spike("ctrl.gate", 18.000, 0.84),
        spike("ae.pitch.pps", 28.200, 0.52),
        spike("enc.flue.o2", 35.800, 0.39),
        spike("ae.pitch.pps", 38.400, 0.44),
    ]
    excerpt = independent_excerpt(53283, 104, 40000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Furnace F-11 on the Butts-Howe BH-HIL pit sees pitch-fire AE at 36 pps while "
                "flue oxygen sits at 3.1 percent under a 5.0 percent cap. AE-first holds the ram; "
                "flue-first would push the next green anode because the O2 header looks legal. "
                "The HIL bake-pit mockup is the authority, not the carbon plant floor.",
            ),
            ("domain", "anode-bake-furnace"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep F-11 from pushing a pitch-fired pit while flue oxygen remains under its own cap.",
            ),
            ("t0_us", 1756867200000283),
            ("gate_latency_us", 780),
            ("race_window_us", 320),
            ("race_window_rel_ms", [6.84, 7.16]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.pitch.pps 36 over 10 cap",
                                "enc.flue.o2 3.1 under 5.0 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; flue-first pushes the next green anode on a "
                            "'header still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one AE puck slot versus the flue-O2 publisher on this HIL "
                            "bake-pit bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + flue 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have pushed a pitch-fired pit.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "pitch-fire AE puck, 50 kHz, 26 us jitter",
                    "flue zirconia O2, 1 kHz, 32 us jitter",
                    "ram LVDT (context)",
                    "pit TC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 10.0),
                        ("observed_ae_pps", 36.0),
                        ("flue_o2_pct", 3.1),
                        ("flue_o2_cap_pct", 5.0),
                        ("proposed_push", True),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. F-11 HIL indexed; next green anode armed.",
                    "2. Flue O2 3.1 percent under 5.0; AE 36 pps over 10.",
                    "3. Flue precursor at 1.360 ms.",
                    "4. Race window [6.840, 7.160] ms.",
                    "5. ae.pitch.pps 36 at 6.840 ms (winner).",
                    "6. enc.flue.o2 3.1 at 7.020 ms (loser by 180 us).",
                    "7. Gate at 7.620 ms: REJECT hold, do not push.",
                    "8. Ram 0 mm; flue left at 3.1 percent.",
                    "9. Pitch-fire inspected on the HIL pit.",
                    "10. Delayed (abort_s=480): 8 min pit cooldown.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "push_green_anode"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("push", True),
                        ("hold", False),
                        ("flue_o2_pct", 3.1),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 36.0),
                        ("ae_cap_pps", 10.0),
                        ("flue_o2_pct", 3.1),
                        ("flue_o2_cap_pct", 5.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes pushing the next green anode because flue O2 3.1 percent is "
                "under 5.0, treating the 36 pps AE as packing noise rather than a pitch fire.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Pitch-fire AE 36 pps won by 180 us, so the pit is on fire, not still a flue-O2 "
                "story. Flue 3.1 percent is under 5.0 and does not authorize a push. REJECT: hold "
                "ram, do not push. A MODIFY that only trims draught would leave the pitch fire.",
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
                                    ("observed", 36.0),
                                    ("executed_push", False),
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
            ("name", "hold_bake_ram"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("push", False),
                        ("hold", True),
                        ("flue_o2_pct", 3.1),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: ram held, no green-anode push. Flue left at 3.1 percent under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held F-11. AE 36 pps beat flue O2 3.1 percent by 180 us. Flue was "
                "legal; the pit was not. 8 min pit cooldown (abort_s=480) is delayed survey, "
                "not a process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("ram", "held; no push"),
                        ("flue", "left 3.1 percent < 5.0 cap"),
                        ("pit", "8 min cooldown (abort_s=480)"),
                        ("mission", "HIL green anode not pushed"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Flue-O2 never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min pit cooldown on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.pitch.pps (6.840 ms, 36 pps)"),
                        ("loser", "enc.flue.o2 (7.020 ms, 3.1 percent)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Flue-first by < 180 us inside the 320 us window would have pushed "
                            "the next green anode into a pitch-fired pit. The REJECT is still "
                            "the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7620),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.620 ms, tick 4). The 8 min pit "
                "cooldown is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    dw = 0.32
    ras = raster_core(
        40,
        104,
        22,
        92,
        routing(
            "thalamic-relay.pitch-ae",
            "spikenaut.policy.ram-hold",
            [
                ("relay.ae.pitch", "policy.ram_hold", 0.71),
                ("relay.enc.flue", "policy.flue_go", 0.23),
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
                    pop_budget("ram_hold", 56, 0.45, 280.0, dw),
                    pop("flue_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r53-283"),
            (
                "title",
                "Butts-Howe BH-HIL / Furnace F-11: pitch AE 36 pps beats flue O2 3.1 percent by 180 us; "
                "correct REJECT holds the ram",
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
                    "Correct REJECT. AE 36 > 10 cap beats legal flue O2. "
                    "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "anode-bake-furnace",
                    [
                        "reject",
                        "hil",
                        "ae-vs-flue",
                        "pitch-fire",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal flue-O2 header can lose to pitch-fire AE inside a 320 us "
                    "window; reversing 180 us would have pushed a pitch-fired pit.",
                    3,
                ),
            ),
        ]
    )


def record_284():
    ticks = [
        tick(2880, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7200, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7360, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7840, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8140, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.haul.mpm", 1.160, 0.40),
        spike("ir.frost.m", 2.880, 0.55),
        spike("enc.haul.mpm", 4.280, 0.48),
        spike("ir.frost.m", 7.200, 1.26),
        spike("enc.haul.mpm", 7.360, 1.08),
        spike("ctrl.gate", 7.840, 0.95),
        spike("ir.frost.m", 11.000, 0.78),
        spike("enc.haul.mpm", 14.600, 0.60),
        spike("ctrl.gate", 18.200, 0.82),
        spike("ir.frost.m", 22.400, 0.50),
        spike("enc.haul.mpm", 25.800, 0.38),
    ]
    excerpt = independent_excerpt(53284, 60, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Tower T-6 of the Frostline-Kame FK-2 blown-film line is already at a 1.92 m frost "
                "line inside a 1.40-2.40 m band. Haul leftover is 38 m/min under a 52 m/min cap. "
                "Frost-first accepts the 38 m/min sendout; haul-first would have rejected a legal "
                "bubble on a 'still climbing' model.",
            ),
            ("domain", "blown-film-tower"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the FK-2 sendout with frost line inside 1.40-2.40 m and haul <= 52 m/min.",
            ),
            ("t0_us", 1756867200000284),
            ("gate_latency_us", 640),
            ("race_window_us", 300),
            ("race_window_rel_ms", [7.20, 7.50]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.frost.m 1.92 inside 1.40-2.40 band",
                                "enc.haul.mpm 38 under 52 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Frost-first accepts 38 m/min; haul-first would REJECT a legal bubble "
                            "as still climbing.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one frost-line IR slot versus the haul-encoder publisher "
                            "on this blown-film sim bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 54 us (frost 24 + haul 30): 2.96x "
                            "over a 2.0x trust floor. Reversing order by < 160 us inside the 300 us "
                            "window would have REJECTED an already-legal sendout.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "frost-line IR, 2 kHz, 24 us jitter",
                    "haul encoder, 1 kHz, 30 us jitter",
                    "BUR laser (context)",
                    "die PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("frost_lo_m", 1.40),
                        ("frost_hi_m", 2.40),
                        ("observed_frost_m", 1.92),
                        ("haul_m_min", 38.0),
                        ("haul_cap_m_min", 52.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Tower T-6 simulated; haul 38 m/min armed.",
                    "2. Frost 1.92 m inside band; haul 38 under 52.",
                    "3. Haul precursor at 1.160 ms.",
                    "4. Race window [7.200, 7.500] ms.",
                    "5. ir.frost.m 1.92 at 7.200 ms (winner).",
                    "6. enc.haul.mpm 38 at 7.360 ms (loser by 160 us).",
                    "7. Gate at 7.840 ms: ACCEPT 38 m/min.",
                    "8. Frost stays 1.92 m; haul stays 38 m/min.",
                    "9. Simulated lighting holds the IR.",
                    "10. Delayed (survey_s=360): 6 min gauge survey.",
                ],
            ),
        ]
    )
    params = OrderedDict(
        [
            ("haul_m_min", 38.0),
            ("frost_m", 1.92),
            ("hold", False),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_haul_sendout"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("frost_m", 1.92),
                        ("frost_lo_m", 1.40),
                        ("frost_hi_m", 2.40),
                        ("haul_m_min", 38.0),
                        ("haul_cap_m_min", 52.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 54),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 38 m/min because frost 1.92 m is inside 1.40-2.40 and haul 38 "
                "is under 52.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Frost line 1.92 m won by 160 us, so the bubble is already legal, not still "
                "climbing. Haul 38 m/min is under 52. ACCEPT the 38 m/min sendout. A REJECT "
                "would idle a legal blown-film tower.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "frost_m",
                            OrderedDict(
                                [
                                    ("lo", 1.40),
                                    ("hi", 2.40),
                                    ("observed", 1.92),
                                    ("executed_haul_m_min", 38.0),
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
            ("name", "hold_haul_sendout"),
            ("parameters", OrderedDict(params.items())),
            ("gate_effect", "ACCEPT: leave 38 m/min; frost 1.92 m; haul legal."),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 38 m/min sendout. Frost 1.92 m beat haul 38 "
                "m/min by 160 us. 6 min gauge survey (survey_s=360) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("haul", "38 m/min held"),
                        ("frost", "1.92 m inside 1.40-2.40 band"),
                        ("bubble", "on-spec"),
                        ("survey", "6 min gauge survey (survey_s=360)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Haul encoder never approached 52 m/min; frost was already inside band.",
                    "Delayed (survey_s=360): 6 min gauge survey on the simulated tower.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.frost.m (7.200 ms, 1.92 m)"),
                        ("loser", "enc.haul.mpm (7.360 ms, 38 m/min)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Haul-first by < 160 us inside the 300 us window would have REJECTED "
                            "an already-legal sendout. The ACCEPT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7840),
            (
                "reward_inflection_note",
                "Task and safety rise at the correct ACCEPT (7.840 ms, tick 4). The 6 min survey "
                "is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 360),
        ]
    )
    dw = 0.30
    ras = raster_core(
        26,
        60,
        40,
        62,
        routing(
            "thalamic-relay.frost-ir",
            "spikenaut.policy.haul-go",
            [
                ("relay.ir.frost", "policy.haul_go", 0.68),
                ("relay.enc.haul", "policy.haul_hold", 0.26),
            ],
            "serotonin",
            0.06,
            "accept_stdp; 5-HT tags the frost-line win as an already-legal hold",
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
                    pop_budget("haul_go", 44, 0.45, 260.0, dw),
                    pop("haul_hold", 36, 0.90),
                    pop("frost_veto", 18, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r53-284"),
            (
                "title",
                "Frostline-Kame FK-2 / Tower T-6: frost 1.92 m beats haul 38 m/min by 160 us; "
                "correct ACCEPT of an already-legal 38 m/min sendout",
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
                    "Correct ACCEPT. Frost 1.92 inside 1.40-2.40; haul 38 < 52. "
                    "total +1.04 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "blown-film-tower",
                    [
                        "accept",
                        "simulated",
                        "frost-vs-haul",
                        "already-legal-hold",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal haul encoder can lose to frost-line IR inside a 300 us "
                    "window; reversing 160 us would have REJECTED an already-legal sendout.",
                    4,
                ),
            ),
        ]
    )


def record_285():
    ticks = [
        tick(1960, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5160, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5320, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5760, 0.14, 0.10, 0.06, 0.04, 0.02),
        tick(6040, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(240000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.mixer.rpm", 0.940, 0.40),
        spike("ft.organic.frac", 1.960, 0.55),
        spike("enc.mixer.rpm", 3.280, 0.48),
        spike("ft.organic.frac", 5.160, 1.24),
        spike("enc.mixer.rpm", 5.320, 1.06),
        spike("ctrl.gate", 5.760, 0.94),
        spike("ft.organic.frac", 8.600, 0.76),
        spike("enc.mixer.rpm", 12.000, 0.58),
        spike("ctrl.gate", 15.200, 0.80),
        spike("ft.organic.frac", 18.800, 0.50),
        spike("enc.mixer.rpm", 21.400, 0.37),
    ]
    excerpt = independent_excerpt(53285, 84, 22000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Settler S-2 at Pregnant-Lea PL-5 is already holding organic continuity at 0.94 "
                "against a 0.88 floor. Mixer leftover is 165 rpm under a 190 rpm cap. Continuity-"
                "first accepts the 165 rpm dwell; mixer-first would have rejected a legal settler "
                "on a 'still accelerating' model.",
            ),
            ("domain", "SX-mixer-settler"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the PL-5 dwell with organic continuity >= 0.88 and mixer <= 190 rpm.",
            ),
            ("t0_us", 1756867200000285),
            ("gate_latency_us", 600),
            ("race_window_us", 280),
            ("race_window_rel_ms", [5.16, 5.44]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.organic.frac 0.94 over 0.88 floor",
                                "enc.mixer.rpm 165 under 190 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Continuity-first accepts 165 rpm; mixer-first would REJECT a legal "
                            "dwell as still accelerating.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one organic-continuity slot versus the mixer-encoder "
                            "publisher on this SX bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (organic 22 + mixer 30): 3.08x "
                            "over a 2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal dwell.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "organic continuity probe, 2 kHz, 22 us jitter",
                    "mixer encoder, 1 kHz, 30 us jitter",
                    "interface DP (context)",
                    "pregnant pH (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("organic_floor", 0.88),
                        ("observed_organic", 0.94),
                        ("mixer_rpm", 165.0),
                        ("mixer_cap_rpm", 190.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Settler S-2 indexed; mixer 165 rpm armed.",
                    "2. Organic 0.94 over 0.88; mixer under 190.",
                    "3. Mixer precursor at 0.940 ms.",
                    "4. Race window [5.160, 5.440] ms.",
                    "5. ft.organic.frac 0.94 at 5.160 ms (winner).",
                    "6. enc.mixer.rpm 165 at 5.320 ms (loser by 160 us).",
                    "7. Gate at 5.760 ms: ACCEPT 165 rpm.",
                    "8. Organic stays 0.94; mixer stays 165 rpm.",
                    "9. Interface holds on-spec.",
                    "10. Delayed (dwell_s=240): 4 min crud reseq.",
                ],
            ),
        ]
    )
    params = OrderedDict(
        [
            ("mixer_rpm", 165.0),
            ("organic_frac", 0.94),
            ("hold", False),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_mixer_dwell"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("organic_frac", 0.94),
                        ("organic_floor", 0.88),
                        ("mixer_rpm", 165.0),
                        ("mixer_cap_rpm", 190.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 165 rpm because organic 0.94 is over 0.88 and mixer 165 is "
                "under 190.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Organic continuity 0.94 won by 160 us, so the settler is already legal, not still "
                "accelerating. Mixer 165 rpm is under 190. ACCEPT the 165 rpm dwell. A REJECT "
                "would idle a legal SX train.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "organic_frac",
                            OrderedDict(
                                [
                                    ("floor", 0.88),
                                    ("observed", 0.94),
                                    ("executed_mixer_rpm", 165.0),
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
            ("name", "hold_mixer_dwell"),
            ("parameters", OrderedDict(params.items())),
            ("gate_effect", "ACCEPT: leave 165 rpm; organic 0.94; mixer legal."),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 165 rpm dwell. Organic 0.94 beat mixer 165 "
                "rpm by 160 us. 4 min crud reseq (dwell_s=240) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("mixer", "165 rpm held"),
                        ("organic", "0.94 >= 0.88 floor"),
                        ("interface", "on-spec"),
                        ("reseq", "4 min crud reseq (dwell_s=240)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Mixer encoder never approached 190 rpm; organic was already over floor.",
                    "Delayed (dwell_s=240): 4 min crud reseq after S-2.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.organic.frac (5.160 ms, 0.94)"),
                        ("loser", "enc.mixer.rpm (5.320 ms, 165 rpm)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Mixer-first by < 160 us inside the 280 us window would have REJECTED "
                            "an already-legal dwell. The ACCEPT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5760),
            (
                "reward_inflection_note",
                "Task and safety rise at the correct ACCEPT (5.760 ms, tick 4). The 4 min reseq "
                "is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 240),
        ]
    )
    dw = 0.28
    ras = raster_core(
        22,
        84,
        30,
        55,
        routing(
            "thalamic-relay.organic-ft",
            "spikenaut.policy.mixer-go",
            [
                ("relay.ft.organic", "policy.mixer_go", 0.67),
                ("relay.enc.mixer", "policy.mixer_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the organic-continuity win as an already-legal dwell",
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
                    pop_budget("mixer_go", 40, 0.45, 250.0, dw),
                    pop("mixer_hold", 32, 0.90),
                    pop("organic_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r53-285"),
            (
                "title",
                "Pregnant-Lea PL-5 / Settler S-2: organic 0.94 beats mixer 165 rpm by 160 us; "
                "correct ACCEPT of an already-legal 165 rpm dwell",
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
                    "Correct ACCEPT. Organic 0.94 >= 0.88; mixer 165 < 190. "
                    "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "SX-mixer-settler",
                    [
                        "accept",
                        "designed",
                        "organic-vs-mixer",
                        "already-legal-dwell",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal mixer encoder can lose to organic continuity inside a "
                    "280 us window; reversing 160 us would have REJECTED an already-legal dwell.",
                    5,
                ),
            ),
        ]
    )
