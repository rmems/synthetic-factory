def lif_241_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.46
    stim = (22000, 25200)
    seed = 45241
    window_us = 42000
    i_clamp_extra = 0.64
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
    take(burst, 8, label_times=(22800, 23400, 24400))
    clamp = [(t, nid) for t, nid in picked if t < 22000][:7]
    tear = [(t, nid) for t, nid in picked if t >= 22000][:8]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(f"LIF excerpt too short {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.coke" for t, _ in picked]
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
            ("i_stim_peak", 2.46),
            ("stim_t_us", [22000, 25200]),
            ("i_clamp_extra", 0.64),
            ("clamp_n", 14),
            ("seed", 45241),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.64 TMT-clamp bias; stim 22.0-25.2 ms is the coke-spall burst.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 840),
            ("delayed_surprise_s", 840),
        ]
    )
    return excerpt_items(picked, channels), extra


def record_241():
    excerpt, extra = lif_241_excerpt()
    ticks = [
        tick(2200, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5120, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(5280, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5900, 0.10, -0.06, -0.04, 0.02, -0.01),
        tick(22800, 0.04, -0.44, -0.03, -0.01, -0.01),
        tick(840000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Coil-C14 inside Pyro-Knap PK-7 is already running a 18.2 MW fuel latch while "
                "tube-metal TMT sits at 1084 C against a 1070 C license. Therm-first drops fuel "
                "18.2 -> 15.4 MW and holds TMT at 1064 C; encoder-first would keep 18.2 MW because "
                "the 0.9 percent leftover looks like a still-warming pass. A coke lens already "
                "seated on the radiant bend does not appear on TMT or fuel until the AE spall.",
            ),
            ("domain", "ethylene-cracker-coil"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep PK-7 Coil-C14 TMT <= 1070 C and finish the pass without spalling a coke "
                "lens onto the radiant bend.",
            ),
            ("t0_us", 1756860000000241),
            ("gate_latency_us", 780),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.12, 5.48]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "therm.tmt.C 1084 C",
                                "enc.fuel.mw 0.9 pct residual",
                            ],
                        ),
                        (
                            "semantics",
                            "TMT-first latches fuel 18.2 -> 15.4 MW (coil-metal clamp); fuel-first "
                            "keeps 18.2 MW on a 'still warming' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one TMT-thermocouple slot versus the fuel-flow encoder "
                            "publisher on this pyrolysis-coil bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 60 us (TMT 28 + fuel 32): 2.67x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 360 us window "
                            "would have kept 18.2 MW; predicted next-sample 1078 C > 1070 C cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "tube-metal thermocouple TMT, 2 kHz, 28 us jitter",
                    "fuel-flow encoder, 1 kHz, 32 us jitter",
                    "radiant-bend AE puck, 50 kHz (context)",
                    "coil-outlet pyrometer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("tmt_cap_C", 1070.0),
                        ("observed_tmt_C", 1084.0),
                        ("fuel_MW", 18.2),
                        ("fuel_residual_pct", 0.9),
                        ("fuel_cap_MW", 22.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Coil-C14 indexed in PK-7; fuel 18.2 MW; TMT 1084 C.",
                    "2. Fuel residual 0.9 percent under a 22 MW header; TMT already over 1070 C.",
                    "3. Coil-enc precursor at 1.140 ms.",
                    "4. Race window [5.120, 5.480] ms.",
                    "5. therm.tmt.C 1084 C at 5.120 ms (winner).",
                    "6. enc.fuel.mw 0.9 pct at 5.280 ms (loser by 160 us).",
                    "7. Gate at 5.900 ms: MODIFY fuel 18.2 -> 15.4 MW.",
                    "8. After clamp TMT 1064 C < 1070; fuel still 15.4 MW.",
                    "9. At 22.800 ms a coke lens spalls the radiant bend.",
                    "10. 14 min coil steam-air decoke (abort_s=840); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_coil_fuel"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("fuel_MW", 18.2),
                        ("tmt_C", 1084.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("tmt_C", 1084.0),
                        ("tmt_cap_C", 1070.0),
                        ("predicted_unclamped_next_C", 1078.0),
                        ("fuel_MW", 18.2),
                        ("fuel_cap_MW", 22.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 60),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes holding 18.2 MW because the 0.9 percent fuel leftover looks like "
                "a still-warming pass, not a TMT overshoot, and Coil-C14 is treated as still clean.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "TMT 1084 C won by 160 us, so the radiant tube is already over the 1070 C license, "
                "not still warming. Holding 18.2 MW predicts next-sample 1078 C > 1070 cap. MODIFY: "
                "fuel 18.2 -> 15.4 MW. Observed after clamp 1064 C < 1070. A full REJECT is not "
                "indicated: a clean pass accepts 15.4 MW.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tmt_C",
                            OrderedDict(
                                [
                                    ("cap", 1070.0),
                                    ("observed", 1084.0),
                                    ("predicted_unclamped_next", 1078.0),
                                    ("clamped_fuel_MW", 15.4),
                                    ("observed_after_clamp", 1064.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 160),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 2.67),
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
            ("name", "clamped_coil_fuel"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("fuel_MW", 15.4),
                        ("tmt_C", 1064.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: fuel 18.2 -> 15.4 MW. Process-correct vs the 1070 C TMT cap. Coke lens "
                "still spalls at 22.800 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held Coil-C14 TMT at 1064 C. At 22.800 ms a coke lens "
                "already seated on the radiant bend spalled. Clamp reduced dump energy; it did "
                "not prevent the spall. Partnered negative: process heads stay honest; world loss "
                "is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("coil", "clamp executed; peak 1064 C < 1070 C cap"),
                        ("coke_lens", "spalled at 22.800 ms onto Coil-C14 radiant bend"),
                        ("repair", "14 min steam-air decoke (abort_s=840)"),
                        ("mission", "PK-7 pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither TMT nor fuel residual predicted the seated coke lens; ae.coke.spall is a new channel at 22.800 ms, 16.900 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=840): 14 min steam-air decoke. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "14 min steam-air decoke after the coke-lens spall. Safety head -0.64 prices the "
                "dump; task_progress stays +0.32 because the fuel clamp completed under the 1070 C "
                "cap. World loss is named here, not subtracted from process heads.",
            ),
            ("abort_s", 840),
            ("delayed_surprise_s", 840),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "therm.tmt.C (5.120 ms, 1084 C)"),
                        ("loser", "enc.fuel.mw (5.280 ms, 0.9 pct)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Fuel-first by < 160 us inside the 360 us window would have kept "
                            "18.2 MW; predicted next-sample 1078 C would have exceeded the 1070 C "
                            "cap even without the coke spall. The MODIFY is still the correct "
                            "process. The spall is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22800),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.800 ms coke-lens spall (tick t_us=22800), inside the "
                "42 ms raster. The correct MODIFY at 5.900 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=840 decoke tick.",
            ),
        ]
    )
    spikes = [
        spike("enc.coil.ctx", 1.140, 0.41),
        spike("therm.tmt.C", 2.200, 0.58),
        spike("enc.fuel.mw", 3.400, 0.50),
        spike("therm.tmt.C", 5.120, 1.31),
        spike("enc.fuel.mw", 5.280, 1.12),
        spike("ctrl.gate", 5.900, 0.97),
        spike("therm.tmt.C", 8.200, 0.82),
        spike("enc.fuel.mw", 11.000, 0.64),
        spike("ctrl.gate", 14.400, 0.86),
        spike("ae.coke.spall", 22.800, 1.48),
        spike("ae.coke.spall", 24.600, 0.93),
        spike("enc.coil.ctx", 31.000, 0.40),
        spike("therm.tmt.C", 38.200, 0.55),
    ]
    dw = 0.36
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.coil-tmt",
            "spikenaut.policy.tmt-clamp",
            [
                ("relay.therm.tmt", "policy.tmt_clamp", 0.69),
                ("relay.enc.fuel", "policy.fuel_hold", 0.28),
                ("relay.ae.coke", "policy.tmt_clamp", -0.40),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at TMT win (5.120 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.800 ms coke spall",
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
                    pop_budget("tmt_clamp", 48, 0.50, 280.0, dw),
                    pop_budget("fuel_hold", 40, 0.80, 70.0, dw),
                    pop("coke_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r45-241"),
            (
                "title",
                "Pyro-Knap PK-7 / Coil-C14: TMT beats fuel-encoder by 160 us; correct MODIFY still "
                "eats an in-window coke-lens spall (partnered negative total -0.48)",
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
                    "42 ms raster. total -0.48 = 0.32 + -0.64 + -0.16 + 0.04 + -0.04. Named coil "
                    "decoke (abort_s=840) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "ethylene-cracker-coil",
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
                    "14 min steam-air decoke.",
                    1,
                ),
            ),
        ]
    )


def record_242():
    ticks = [
        tick(1680, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5480, -0.04, -0.03, -0.04, -0.02, 0.01),
        tick(5640, -0.03, -0.02, -0.03, -0.01, 0.01),
        tick(6180, -0.08, -0.05, -0.08, -0.05, 0.02),
        tick(8600, -0.03, -0.02, -0.04, -0.02, 0.01),
        tick(660000000, -0.02, -0.02, -0.03, -0.01, 0.00),
    ]
    spikes = [
        spike("pt.bed.ctx", 0.980, 0.39),
        spike("rtd.front.C", 1.680, 0.57),
        spike("dp.bed.kPa", 2.800, 0.51),
        spike("rtd.front.C", 5.480, 1.33),
        spike("dp.bed.kPa", 5.640, 1.16),
        spike("ctrl.gate", 6.180, 1.01),
        spike("rtd.front.C", 8.600, 0.74),
        spike("dp.bed.kPa", 11.200, 0.62),
        spike("ctrl.gate", 14.400, 0.83),
        spike("pt.bed.ctx", 18.000, 0.41),
        spike("rtd.front.C", 22.400, 0.52),
        spike("dp.bed.kPa", 26.200, 0.47),
    ]
    excerpt = independent_excerpt(45242, 88, 28000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Bed-B3 on Sieve-Holt SH-6 is still in adsorption: bed DP 18.2 kPa under a 28.0 kPa "
                "cap, N2-front RTD 41.0 C under a 58.0 C trip. Remaining adsorb is 420 s. A 0.92 C/s "
                "precursor on the quarter-bed thermocouple has not crossed either cap. A weak "
                "supervisor dumps feed 8.4 -> 2.0 t/h anyway, an early clamp on a still-legal bed.",
            ),
            ("domain", "hydrogen-PSA-bed"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the SH-6 adsorb with bed DP <= 28.0 kPa and front <= 58.0 C; do not dump "
                "feed while both remain under cap.",
            ),
            ("t0_us", 1756860000000242),
            ("gate_latency_us", 700),
            ("race_window_us", 340),
            ("race_window_rel_ms", [5.32, 5.66]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.front.C 41.0 C rising 0.92 C/s",
                                "dp.bed.kPa 18.2 under 28.0 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Front-first tempts a weak supervisor to treat a rising precursor as a "
                            "trip and dump feed. DP-first would ACCEPT: 18.2 kPa is still under 28.0.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one front-RTD sample minus bed-DP transmitter group delay on "
                            "this PSA skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 62 us (RTD 30 + DP 32): 2.58x over a "
                            "2.0x trust floor. Order is correctly front-first. The error is clamping "
                            "before either cap is crossed, not the race and not a wrong actuator.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "N2-front RTD, 2 kHz, 30 us jitter",
                    "bed DP transmitter, 1 kHz, 32 us jitter",
                    "feed coriolis (context)",
                    "product H2 GC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_dp_cap_kPa", 28.0),
                        ("observed_bed_dp_kPa", 18.2),
                        ("front_trip_C", 58.0),
                        ("observed_front_C", 41.0),
                        ("predicted_next_front_C", 44.8),
                        ("feed_tph", 8.4),
                        ("correct_feed_tph", 8.4),
                        ("executed_wrong_feed_tph", 2.0),
                        ("remaining_adsorb_s", 420),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. SH-6 Bed-B3 in adsorption; feed 8.4 t/h; remaining adsorb 420 s.",
                    "2. Bed DP 18.2 kPa < 28.0 cap; front 41.0 C < 58.0 trip.",
                    "3. Header precursor at 0.980 ms.",
                    "4. Race window [5.320, 5.660] ms.",
                    "5. rtd.front.C 41.0 C at 5.480 ms (winner, still under trip).",
                    "6. dp.bed.kPa 18.2 at 5.640 ms (loser by 160 us, still under cap).",
                    "7. Gate at 6.180 ms: WRONG-MODIFY dumps feed 8.4 -> 2.0 t/h.",
                    "8. Adsorb aborts 420 s early; predicted next front 44.8 C still < 58.0.",
                    "9. Product H2 stays 99.68 percent over a 99.50 spec; no cap was crossed.",
                    "10. Delayed (abort_s=660): 11 min unused adsorb plus extra regen.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_adsorb_84"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 8.4),
                        ("hold", False),
                        ("regen", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_dp_kPa", 18.2),
                        ("bed_dp_cap_kPa", 28.0),
                        ("front_C", 41.0),
                        ("front_trip_C", 58.0),
                        ("predicted_next_front_C", 44.8),
                        ("precursor_dT_dt_C_s", 0.92),
                        ("correct_feed_tph", 8.4),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 62),
                        ("abort_s", 660),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes holding feed 8.4 t/h because bed DP 18.2 kPa and front 41.0 C "
                "are both still under cap; the 0.92 C/s precursor is a slope, not a trip.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Front 41.0 C is rising at 0.92 C/s, so the supervisor dumps feed 8.4 -> 2.0 t/h "
                "to start regen early. Front-first is treated as a trip. Over-caution on a rising "
                "precursor is the stated doctrine.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "front_C",
                            OrderedDict(
                                [
                                    ("trip", 58.0),
                                    ("observed", 41.0),
                                    ("predicted_next", 44.8),
                                    ("crossed", False),
                                    ("executed_feed_tph", 2.0),
                                    ("correct_feed_tph", 8.4),
                                ]
                            ),
                        ),
                        (
                            "bed_dp_kPa",
                            OrderedDict(
                                [
                                    ("cap", 28.0),
                                    ("observed", 18.2),
                                    ("crossed", False),
                                    ("misbound_as", "regen_dump"),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 160),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 2.58),
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
            ("name", "feed_early_dump"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 2.0),
                        ("hold", False),
                        ("regen", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect): feed 8.4 -> 2.0 t/h. Routing relay.rtd.front -> "
                "policy.feed_dump; no positive weight to policy.feed_hold (8.4 t/h).",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY dumped SH-6 feed to 2.0 t/h. Bed DP 18.2 kPa and front 41.0 C were "
                "both still under cap; predicted next front 44.8 C still < 58.0. A timely gate is "
                "ACCEPT hold 8.4 t/h. 11 min unused adsorb (abort_s=660). Correct gate was ACCEPT.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "early-clamped 8.4 -> 2.0 t/h; caps uncrossed"),
                        ("adsorb", "aborted 420 s remaining"),
                        ("bed", "forced into regen"),
                        ("mission", "product window missed"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Front-first was the race order but 41.0 C had not crossed 58.0 C and DP 18.2 had not crossed 28.0 kPa; the MODIFY spent that win on an early dump.",
                    "Delayed (abort_s=660): SH-6 loses 11 min unused adsorb plus one extra regen.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT hold feed 8.4 t/h; leave regen false until DP or front actually crosses cap.",
                        ),
                        ("correct_feed_tph", 8.4),
                        ("wrong_subclass", "clamp-too-early"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("feed_tph", 2.0), ("regen", True)]),
                        ),
                        (
                            "cost",
                            "11 min unused adsorb + extra regen (task/efficiency); neither DP nor front ever crossed cap (safety near-miss of a false dump).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.front.C (5.480 ms, 41.0 C)"),
                        ("loser", "dp.bed.kPa (5.640 ms, 18.2 kPa)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "DP-first by < 160 us would still be under the 28.0 kPa cap; a correct "
                            "gate ACCEPTs 8.4 t/h either way. The wrong MODIFY spent the front win "
                            "on a clamp-too-early dump of the same feed actuator.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6180),
            (
                "reward_inflection_note",
                "Task, efficiency, and coherence drop at the wrong MODIFY (6.180 ms, tick 4). "
                "The 11 min unused adsorb is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 660),
        ]
    )
    dw = 0.34
    ras = raster_core(
        28,
        88,
        32,
        79,
        routing(
            "relay.rtd.front",
            "policy.feed_dump",
            [
                ("relay.rtd.front", "policy.feed_dump", 0.74),
                ("relay.dp.bed", "policy.feed_dump", 0.22),
            ],
            "acetylcholine",
            0.06,
            "earlyclamp_stdp; ACh tags the (wrong) feed_dump bind at the uncrossed precursor",
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
            ("decision_window_ms", dw),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("feed_dump", 48, 0.50, 300.0, dw),
                    pop_budget("feed_hold", 48, 0.80, 18.0, dw),
                    pop_budget("front_ctx", 32, 0.55, 140.0, dw),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r45-242"),
            (
                "title",
                "WRONG-MODIFY at Sieve-Holt SH-6 / Bed-B3: DP 18.2 kPa and front 41.0 C still under "
                "cap; supervisor dumps feed 8.4 -> 2.0 t/h (clamp-too-early)",
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
                    "Wrong-modify / clamp-too-early. Sidecar arithmetic 18.2 < 28.0 and 41.0 < 58.0 "
                    "is true; MODIFY bound to a 2.0 t/h dump instead of ACCEPT 8.4. total -0.68 = "
                    "-0.22 + -0.16 + -0.24 + -0.12 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "hydrogen-PSA-bed",
                    [
                        "modify",
                        "wrong-gate",
                        "clamp-too-early",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct front-first race can still be a wrong gate when "
                    "the MODIFY clamps a precursor that has not crossed cap. Convictable from "
                    "executed 2.0 vs correct 8.4 t/h without PSA physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_243():
    ticks = [
        tick(2400, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6840, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7020, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7680, 0.03, 0.12, 0.04, 0.04, 0.01),
        tick(9800, 0.02, 0.06, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.04, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.slew.ctx", 1.320, 0.43),
        spike("load.pin.kN", 2.400, 0.61),
        spike("enc.slew.deg", 3.800, 0.49),
        spike("load.pin.kN", 6.840, 1.36),
        spike("enc.slew.deg", 7.020, 1.11),
        spike("ctrl.gate", 7.680, 1.04),
        spike("load.pin.kN", 10.200, 0.78),
        spike("enc.slew.ctx", 14.800, 0.44),
        spike("enc.slew.deg", 19.400, 0.58),
        spike("ctrl.gate", 26.000, 0.81),
        spike("load.pin.kN", 34.200, 0.53),
        spike("enc.slew.deg", 42.000, 0.46),
    ]
    excerpt = independent_excerpt(45243, 124, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Boom-B2 on the Spoil-Spit SS-HIL yard pad is over-moment: load-pin 184 kN against "
                "a 160 kN slew license. Slew encoder 0.18 deg looks like a still-parked head. Freeze "
                "the slew on the pin win; treating the 0.18 deg leftover as a permit would fire a "
                "0.40 deg/s slew into an over-moment boom.",
            ),
            ("domain", "stacker-reclaimer-boom"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep Boom-B2 unslewed unless load-pin <= 160 kN; do not treat 0.18 deg encoder "
                "residual as a slew permit.",
            ),
            ("t0_us", 1756860000000243),
            ("gate_latency_us", 840),
            ("race_window_us", 400),
            ("race_window_rel_ms", [6.84, 7.24]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "load.pin.kN 184 kN",
                                "enc.slew.deg 0.18 deg residual",
                            ],
                        ),
                        (
                            "semantics",
                            "Pin-first REJECTs the 0.40 deg/s slew (184 > 160 kN cap). Encoder-first "
                            "would ACCEPT on a parked-head residual mistaken for a clear boom.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one load-pin sample minus slew-encoder group delay on this "
                            "HIL yard-machine bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 66 us (pin 32 + encoder 34): 2.73x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 400 us window "
                            "would have kept the 0.40 deg/s slew armed on 0.18 deg residual.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "boom load-pin, 5 kHz burst, 32 us jitter",
                    "slew encoder 0-360, 34 us jitter",
                    "luff inclinometer (context)",
                    "HIL counterweight-pressure monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("pin_cap_kN", 160.0),
                        ("observed_pin_kN", 184.0),
                        ("slew_residual_deg", 0.18),
                        ("proposed_slew_deg_s", 0.40),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("pad", "Spoil-Spit SS-HIL stacker-reclaimer bench"),
                        ("injected", "load-pin burst + parked-slew encoder packet"),
                        (
                            "note",
                            "Hardware-in-the-loop yard machine. Invented plant; not a live stockyard.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Boom-B2 on the SS-HIL bench; 0.40 deg/s slew armed.",
                    "2. Parked-encoder packet injected 120-160 us before the load-pin volume.",
                    "3. Slew-enc precursor at 1.320 ms.",
                    "4. Race window [6.840, 7.240] ms.",
                    "5. load.pin.kN 184 kN at 6.840 ms (winner).",
                    "6. enc.slew.deg 0.18 deg at 7.020 ms (loser by 180 us).",
                    "7. Gate at 7.680 ms: REJECT hold slew 0 deg/s; do not fire.",
                    "8. Pin remains over the 160 kN cap this cycle.",
                    "9. Encoder 0.18 deg stays a parked residual, not a slew permit.",
                    "10. Delayed (abort_s=480): 8 min counterweight dump and pin recert.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "slew_040"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("slew_deg_s", 0.40),
                        ("fire", True),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("pin_kN", 184.0),
                        ("pin_cap_kN", 160.0),
                        ("slew_residual_deg", 0.18),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 66),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 0.40 deg/s slew because encoder 0.18 deg looks parked; it has "
                "not yet bound load-pin 184 kN to the 160 kN slew cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Load-pin 184 kN won by 180 us, so the slew cap is already violated. Encoder 0.18 "
                "deg is a parked residual. REJECT: slew 0 deg/s, fire false. A MODIFY that keeps "
                "the boom armed is not indicated: next-sample pin is 186 kN.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "pin_kN",
                            OrderedDict(
                                [
                                    ("cap", 160.0),
                                    ("observed", 184.0),
                                    ("executed_slew_deg_s", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 2.73),
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
            ("name", "slew_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("slew_deg_s", 0.0),
                        ("fire", False),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: slew 0.40 -> 0 deg/s. Pin cap held. Encoder residual unused as a go signal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held Boom-B2 at 0 deg/s. Pin 184 kN was over the 160 kN cap; "
                "encoder 0.18 deg was a parked residual. 8 min pin recert (abort_s=480).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("slew", "held; 0 deg/s"),
                        ("pin", "still 184 kN > 160 cap"),
                        ("encoder", "0.18 deg unused"),
                        ("mission", "slew deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Parked-slew encoder arrived 180 us after load-pin; reversing that order would have kept the slew armed over the moment cap.",
                    "Delayed (abort_s=480): 8 min counterweight dump and load-pin recert.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "load.pin.kN (6.840 ms, 184 kN)"),
                        ("loser", "enc.slew.deg (7.020 ms, 0.18 deg)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 180 us inside the 400 us window would have kept "
                            "the 0.40 deg/s slew armed on 0.18 deg residual while pin stayed over "
                            "160 kN.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7680),
            (
                "reward_inflection_note",
                "Safety and coherence peak at the correct REJECT (7.680 ms, tick 4). The 8 min "
                "recert is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    dw = 0.40
    ras = raster_core(
        46,
        124,
        18,
        103,
        routing(
            "thalamic-relay.load-pin",
            "spikenaut.policy.slew-hold",
            [
                ("relay.load.pin", "policy.slew_hold", 0.72),
                ("relay.enc.slew", "policy.slew_go", 0.23),
            ],
            "dopamine",
            0.05,
            "cap_stdp; DA tags the pin-cap bind at the load win",
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
                    pop_budget("slew_hold", 56, 0.50, 250.0, dw),
                    pop_budget("slew_go", 56, 0.80, 20.0, dw),
                    pop_budget("pin_ctx", 32, 0.55, 150.0, dw),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r45-243"),
            (
                "title",
                "Spoil-Spit SS-HIL / Boom-B2: load-pin 184 kN beats slew encoder 0.18 deg; correct "
                "REJECT holds the slew",
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
                    "Correct REJECT. Pin 184 > 160 kN cap; encoder 0.18 deg is parked residual, "
                    "not a permit. total +0.78 = 0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "stacker-reclaimer-boom",
                    [
                        "reject",
                        "hil",
                        "pin-vs-encoder",
                        "parked-residual",
                    ],
                    "Teaches that a parked-slew encoder packet can lose to load-pin inside a 400 us "
                    "window; reversing 180 us would have kept the slew armed over the moment cap.",
                    3,
                ),
            ),
        ]
    )


def record_244():
    ticks = [
        tick(1600, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(5200, 0.10, 0.08, 0.04, 0.03, 0.02),
        tick(5360, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(6120, 0.12, 0.08, 0.04, 0.04, 0.02),
        tick(9000, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.winder.ctx", 1.100, 0.40),
        spike("ir.bush.C", 1.600, 0.56),
        spike("visc.film.kP", 3.200, 0.47),
        spike("ir.bush.C", 5.200, 1.27),
        spike("visc.film.kP", 5.360, 1.08),
        spike("ctrl.gate", 6.120, 0.99),
        spike("ir.bush.C", 9.000, 0.76),
        spike("enc.winder.ctx", 12.400, 0.43),
        spike("visc.film.kP", 16.800, 0.55),
        spike("ctrl.gate", 21.200, 0.82),
        spike("ir.bush.C", 26.400, 0.50),
        spike("enc.winder.ctx", 29.200, 0.36),
    ]
    excerpt = independent_excerpt(45244, 56, 30000, 13, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("draw_km_min", 1.82),
            ("hold", False),
            ("bush_kW", 48.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Bush-Fen BF-9 Tip T-11 is already in a 1.82 km/min E-glass draw. Bushing IR "
                "1184 C is 56 K shy of the 1240 C ceiling. Film viscometer 4.6 kP is leftover "
                "bead-down, not a drip flag. IR-led ACCEPT keeps the draw; a visc-led abort would "
                "scrap a legal forming cone.",
            ),
            ("domain", "glass-fiber-bushing"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold a 1.82 km/min draw while bushing IR stays <= 1240 C; do not abort on a "
                "4.6 kP film leftover.",
            ),
            ("t0_us", 1756860000000244),
            ("gate_latency_us", 920),
            ("race_window_us", 380),
            ("race_window_rel_ms", [5.20, 5.58]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.bush.C 1184 C",
                                "visc.film.kP 4.6 kP leftover",
                            ],
                        ),
                        (
                            "semantics",
                            "IR-first ACCEPTS the 1.82 km/min draw (already under 1240 C). Visc-first "
                            "would REJECT on a bead-down leftover.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one bushing-IR sample minus viscometer group delay on this "
                            "forming-cone bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 60 us (IR 28 + visc 32): 2.67x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 380 us window "
                            "would have REJECTED a legal 1.82 km/min draw.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bushing IR pyrometer, 2 kHz, 28 us jitter",
                    "film viscometer 0-20 kP, 32 us jitter",
                    "winder encoder (context)",
                    "tip RTD (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bush_cap_C", 1240.0),
                        ("observed_bush_C", 1184.0),
                        ("film_kP", 4.6),
                        ("film_abort_kP", 12.0),
                        ("proposed_draw_km_min", 1.82),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "lumped bushing energy + 1-D filament visc, seed 45244; 8 tip nodes, "
                            "6 min heat-up; NOT CFD, NOT a live bushing",
                        ),
                        (
                            "fidelity_limits",
                            "Linear visc; no drip nucleation. Raster is kernelized events, not an "
                            "independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Tip T-11 indexed on BF-9; 1.82 km/min draw armed.",
                    "2. Bushing IR 1184 C; film leftover 4.6 kP.",
                    "3. Winder-encoder precursor at 1.100 ms.",
                    "4. Race window [5.200, 5.580] ms.",
                    "5. ir.bush.C 1184 C at 5.200 ms (winner).",
                    "6. visc.film.kP 4.6 kP at 5.360 ms (loser by 160 us).",
                    "7. Gate at 6.120 ms: ACCEPT 1.82 km/min; executed identical to proposed.",
                    "8. Draw continues; peak bushing 1191 C < 1240 cap.",
                    "9. Film 4.6 kP remains a bead-down leftover, not a drip loop.",
                    "10. Delayed (survey_s=360): 6 min tex coupon on the next cake.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "draw_182"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bush_C", 1184.0),
                        ("bush_cap_C", 1240.0),
                        ("film_kP", 4.6),
                        ("film_abort_kP", 12.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 60),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 1.82 km/min draw because bushing 1184 C is under the 1240 C "
                "cap; film 4.6 kP is under the 12.0 abort and is treated as bead-down leftover.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bushing IR 1184 C won by 160 us and is under the 1240 C cap. Film 4.6 kP is under "
                "the 12.0 kP abort. ACCEPT the already-legal 1.82 km/min draw. A REJECT on bead-down "
                "leftover would stall a legal forming cone.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bush_C",
                            OrderedDict(
                                [
                                    ("cap", 1240.0),
                                    ("observed", 1184.0),
                                    ("executed_draw_km_min", 1.82),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 160),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 2.67),
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
            ("name", "draw_182"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: draw stays 1.82 km/min. Parameters identical to proposed.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept BF-9 at 1.82 km/min. Bushing 1184 C was under 1240 C; film "
                "4.6 kP was bead-down leftover. 6 min tex coupon (survey_s=360).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("draw", "held 1.82 km/min"),
                        ("bushing", "peak 1191 C < 1240 cap"),
                        ("film", "4.6 kP leftover unused"),
                        ("mission", "forming cone continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Viscometer leftover arrived 160 us after bushing IR; reversing that order would have REJECTED a legal draw.",
                    "Delayed (survey_s=360): 6 min tex coupon on the next cake.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.bush.C (5.200 ms, 1184 C)"),
                        ("loser", "visc.film.kP (5.360 ms, 4.6 kP)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Visc-first by < 160 us inside the 380 us window would have REJECTED "
                            "the already-legal 1.82 km/min draw on a 4.6 kP leftover.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6120),
            (
                "reward_inflection_note",
                "Task and safety peak at the correct ACCEPT (6.120 ms, tick 4). The 6 min coupon "
                "is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 360),
        ]
    )
    dw = 0.38
    ras = raster_core(
        30,
        56,
        38,
        64,
        routing(
            "thalamic-relay.bush-ir",
            "spikenaut.policy.draw-go",
            [
                ("relay.ir.bush", "policy.draw_go", 0.70),
                ("relay.visc.film", "policy.draw_abort", 0.24),
            ],
            "serotonin",
            0.05,
            "legal_stdp; 5-HT tags the under-cap IR bind at the pyrometer win",
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
                    pop_budget("draw_go", 48, 0.50, 260.0, dw),
                    pop_budget("draw_abort", 48, 0.80, 22.0, dw),
                    pop_budget("bush_ctx", 32, 0.55, 130.0, dw),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r45-244"),
            (
                "title",
                "Bush-Fen BF-9 / Tip T-11: bushing IR 1184 C beats film visc 4.6 kP by 160 us; "
                "correct ACCEPT keeps 1.82 km/min",
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
                    "Correct ACCEPT. Bushing 1184 < 1240 C; film 4.6 kP is leftover, not drip. "
                    "total +1.08 = 0.42 + 0.30 + 0.16 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "glass-fiber-bushing",
                    [
                        "accept",
                        "simulated",
                        "already-legal",
                        "ir-vs-visc",
                    ],
                    "Teaches that an already-legal draw confirmed by IR-first order should ACCEPT; "
                    "a visc leftover 160 us later is not a drip abort.",
                    4,
                ),
            ),
        ]
    )


def record_245():
    ticks = [
        tick(1400, 0.06, 0.05, 0.03, 0.02, 0.01),
        tick(4880, 0.10, 0.08, 0.04, 0.03, 0.02),
        tick(5040, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(5640, 0.12, 0.08, 0.04, 0.04, 0.02),
        tick(8200, 0.06, 0.05, 0.02, 0.01, 0.01),
        tick(300000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.trap.ctx", 0.880, 0.40),
        spike("pt.trap.bar", 1.400, 0.56),
        spike("tach.kick.mps", 2.600, 0.47),
        spike("pt.trap.bar", 4.880, 1.27),
        spike("tach.kick.mps", 5.040, 1.08),
        spike("ctrl.gate", 5.640, 0.99),
        spike("pt.trap.bar", 8.200, 0.76),
        spike("enc.trap.ctx", 12.000, 0.43),
        spike("tach.kick.mps", 16.400, 0.55),
        spike("ctrl.gate", 19.800, 0.82),
        spike("pt.trap.bar", 22.200, 0.50),
        spike("enc.trap.ctx", 23.600, 0.36),
    ]
    excerpt = independent_excerpt(45245, 80, 24000, 13, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("pig_m_s", 0.35),
            ("hold", False),
            ("kicker_open", True),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Scraper-Ness SN-2 Trap TR-4 is already launching a 0.35 m/s ILI tool. Trap PT "
                "64.2 bar is 7.8 bar shy of the 72.0 bar ceiling. Kicker tach 0.80 m/s is leftover "
                "bypass, not a slam flag. PT-led ACCEPT keeps the launch; a kicker-led abort would "
                "scrap a legal pig run.",
            ),
            ("domain", "oil-pipeline-pig-trap"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold a 0.35 m/s pig launch while trap PT stays <= 72.0 bar; do not abort on a "
                "0.80 m/s kicker leftover.",
            ),
            ("t0_us", 1756860000000245),
            ("gate_latency_us", 760),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.88, 5.20]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.trap.bar 64.2 bar",
                                "tach.kick.mps 0.80 m/s leftover",
                            ],
                        ),
                        (
                            "semantics",
                            "PT-first ACCEPTS the 0.35 m/s launch (already under 72.0 bar). "
                            "Kicker-first would REJECT on a bypass leftover.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one trap-PT sample minus kicker-tach group delay on this "
                            "launcher PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 56 us (PT 26 + tach 30): 2.86x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 320 us window "
                            "would have REJECTED a legal 0.35 m/s launch.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "trap PT, 2 kHz, 26 us jitter",
                    "kicker tachometer, 1 kHz, 30 us jitter",
                    "door encoder (context)",
                    "bypass ultrasonic (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("trap_cap_bar", 72.0),
                        ("observed_trap_bar", 64.2),
                        ("kicker_m_s", 0.80),
                        ("kicker_abort_m_s", 2.40),
                        ("proposed_pig_m_s", 0.35),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Trap TR-4 indexed on SN-2; 0.35 m/s pig launch armed.",
                    "2. Trap PT 64.2 bar; kicker leftover 0.80 m/s.",
                    "3. Door-encoder precursor at 0.880 ms.",
                    "4. Race window [4.880, 5.200] ms.",
                    "5. pt.trap.bar 64.2 bar at 4.880 ms (winner).",
                    "6. tach.kick.mps 0.80 m/s at 5.040 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 0.35 m/s; executed identical to proposed.",
                    "8. Launch continues; peak trap 65.1 bar < 72.0 cap.",
                    "9. Kicker 0.80 m/s remains a bypass leftover, not a slam loop.",
                    "10. Delayed (recycle_s=300): 5 min receiver-door recert on the next trap.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "launch_035"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("trap_bar", 64.2),
                        ("trap_cap_bar", 72.0),
                        ("kicker_m_s", 0.80),
                        ("kicker_abort_m_s", 2.40),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 56),
                        ("recycle_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 0.35 m/s launch because trap 64.2 bar is under the 72.0 bar "
                "cap; kicker 0.80 m/s is under the 2.40 abort and is treated as bypass leftover.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Trap PT 64.2 bar won by 160 us and is under the 72.0 bar cap. Kicker 0.80 m/s is "
                "under the 2.40 m/s abort. ACCEPT the already-legal 0.35 m/s launch. A REJECT on "
                "bypass leftover would stall a legal ILI run.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "trap_bar",
                            OrderedDict(
                                [
                                    ("cap", 72.0),
                                    ("observed", 64.2),
                                    ("executed_pig_m_s", 0.35),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 160),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 2.86),
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
            ("name", "launch_035"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: pig stays 0.35 m/s. Parameters identical to proposed.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept SN-2 at 0.35 m/s. Trap 64.2 bar was under 72.0; kicker "
                "0.80 m/s was bypass leftover. 5 min receiver recert (recycle_s=300).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("pig", "held 0.35 m/s"),
                        ("trap", "peak 65.1 bar < 72.0 cap"),
                        ("kicker", "0.80 m/s leftover unused"),
                        ("mission", "ILI launch continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Kicker leftover arrived 160 us after trap PT; reversing that order would have REJECTED a legal launch.",
                    "Delayed (recycle_s=300): 5 min receiver-door recert on the next trap.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.trap.bar (4.880 ms, 64.2 bar)"),
                        ("loser", "tach.kick.mps (5.040 ms, 0.80 m/s)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Kicker-first by < 160 us inside the 320 us window would have REJECTED "
                            "the already-legal 0.35 m/s launch on a 0.80 m/s leftover.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5640),
            (
                "reward_inflection_note",
                "Task and safety peak at the correct ACCEPT (5.640 ms, tick 4). The 5 min recert "
                "is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 300),
        ]
    )
    dw = 0.32
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.trap-pt",
            "spikenaut.policy.pig-go",
            [
                ("relay.pt.trap", "policy.pig_go", 0.71),
                ("relay.tach.kick", "policy.pig_abort", 0.25),
            ],
            "adenosine",
            0.045,
            "legal_stdp; adenosine tags the under-cap PT bind at the trap win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("recycle_s", 300),
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
                    pop_budget("pig_go", 48, 0.50, 270.0, dw),
                    pop_budget("pig_abort", 48, 0.80, 20.0, dw),
                    pop_budget("trap_ctx", 32, 0.55, 140.0, dw),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r45-245"),
            (
                "title",
                "Scraper-Ness SN-2 / Trap TR-4: trap PT 64.2 bar beats kicker 0.80 m/s by 160 us; "
                "correct ACCEPT keeps 0.35 m/s",
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
                    "Correct ACCEPT. Trap 64.2 < 72.0 bar; kicker 0.80 m/s is leftover, not slam. "
                    "total +1.16 = 0.44 + 0.34 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "oil-pipeline-pig-trap",
                    [
                        "accept",
                        "designed",
                        "already-legal",
                        "pt-vs-kicker",
                    ],
                    "Teaches that an already-legal pig launch confirmed by PT-first order should "
                    "ACCEPT; a kicker leftover 160 us later is not a slam abort.",
                    5,
                ),
            ),
        ]
    )
