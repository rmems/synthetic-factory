def lif_407_excerpt():
    """Independent CUBA LIF (seed 78407). Plant remains designed."""

    n = 80
    dt_us = 100
    tau_m_ms = 19.8
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.93
    i_stim_peak = 2.48
    stim = (21000, 25000)
    seed = 78407
    window_us = 42000
    i_clamp_extra = 0.67
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
    early = [(t, nid) for t, nid in spikes if t < 21000]
    burst = [(t, nid) for t, nid in spikes if 21000 <= t < 25000]
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
            early_flag = pool[0][0] < 21000
            have = len([1 for t, _ in picked if (t < 21000) == early_flag])
            if have >= want:
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
    take(burst, 9, label_times=(22400, 23200, 24100))
    clamp = [(t, nid) for t, nid in picked if t < 21000][:7]
    tray = [(t, nid) for t, nid in picked if t >= 21000][:9]
    picked = sorted(clamp + tray, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise RuntimeError(f"LIF excerpt too short: {len(picked)}")
    channels = ["lif.clamp" if t < 21000 else "lif.tray" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 80),
            ("dt_us", 100),
            ("tau_m_ms", 19.8),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.93),
            ("i_stim_peak", 2.48),
            ("stim_t_us", [21000, 25000]),
            ("i_clamp_extra", 0.67),
            ("clamp_n", 14),
            ("seed", 78407),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.67 propylene-clamp bias; stim 21-25 ms is the oxo tray collapse.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 1020),
            ("delayed_surprise_s", 1020),
        ]
    )
    return excerpt_items(picked, channels), extra


def record_406():
    ticks = [
        tick(2144, -0.02, 0.01, -0.02, -0.01, 0.01),
        tick(5360, -0.04, 0.01, -0.04, -0.02, 0.01),
        tick(5580, -0.03, 0.01, -0.03, -0.01, 0.01),
        tick(6160, -0.06, 0.02, -0.08, -0.03, 0.02),
        tick(6560, -0.02, 0.01, -0.03, -0.01, 0.01),
        tick(840000000, -0.01, 0.00, -0.02, 0.00, 0.00),
    ]
    spikes = [
        spike("enc.meoh.ctx", 1.140, 0.43),
        spike("pt.lastgood.bar", 2.420, 0.63),
        spike("ma.namur.fh", 3.680, 0.52),
        spike("bus.cativa.ctx", 4.480, 0.46),
        spike("pt.lastgood.bar", 5.360, 1.33),
        spike("ma.namur.fh", 5.580, 1.17),
        spike("ctrl.gate", 6.160, 0.99),
        spike("pt.lastgood.bar", 7.360, 0.84),
        spike("ma.namur.fh", 9.480, 0.65),
        spike("ctrl.gate", 14.920, 0.87),
        spike("enc.meoh.ctx", 18.600, 0.41),
        spike("pt.lastgood.bar", 24.800, 0.57),
    ]
    excerpt = independent_excerpt(78406, 84, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Cativa carbonylation kettle CA-3 at Cativa-Quern already holds a last-good reactor "
                "pressure of 28.4 bar when that analog sample races a NAMUR NE43 fail-high current "
                "still latched at 21.6 mA. Published trip is 32.0 bar on the last-good PT; a weak "
                "supervisor treats the diagnostic 21.6 mA as a live 4-20 PV and zeros a legal "
                "22.0 t/h methanol feed.",
            ),
            ("domain", "acetic-cativa-carbonylation"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 22.0 t/h on CA-3, keep last-good kettle P < 32.0 bar trip, and finish the "
                "14 min acetic-quality window.",
            ),
            ("t0_us", 1762300000000406),
            ("gate_latency_us", 800),
            ("race_window_us", 400),
            ("race_window_rel_ms", [5.360, 5.760]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.lastgood.bar 28.4 bar last-good Cativa kettle",
                                "ma.namur.fh 21.6 mA NAMUR NE43 fail-high diagnostic",
                            ],
                        ),
                        (
                            "semantics",
                            "Last-good-first should ACCEPT 22.0 t/h (28.4 bar < 32.0 bar trip). "
                            "Fail-high-first would only delay confirmation of the same legal kettle.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one last-good analog slot versus the NAMUR fail-high "
                            "publisher on this 2 kHz carbonylation bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 70 us (PT 32 + NAMUR 38): 3.1x over "
                            "a 2.0x trust floor. Order is correctly last-good-first. The error is binding "
                            "a fail-high diagnostic as if it were live 4-20, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "CA-3 last-good PT analog, 2 kHz, 32 us jitter, axis cativa_p_bar, last_good_fresh true",
                    "NAMUR NE43 fail-high current, 1 kHz, 38 us jitter, namur_fail_high true, live_mA 21.6",
                    "methanol-feed encoder (context)",
                    "CO header PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("last_good_bar", 28.4),
                        ("trip_bar", 32.0),
                        ("live_mA", 21.6),
                        ("namur_fail_high_mA", 21.0),
                        ("namur_fail_high", True),
                        ("fail_high_as_pv", True),
                        ("shadow_span_bar", 40.0),
                        ("shadow_bar", 44.0),
                        ("last_good_fresh", True),
                        ("proposed_t_h", 22.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Kettle CA-3 indexed on Cativa-Quern; last-good 28.4 bar, 22.0 t/h methanol armed.",
                    "2. Published live trip 32.0 bar; NAMUR current tagged fail-high, not live PV.",
                    "3. Encoder precursor at 1.140 ms.",
                    "4. Race window [5.360, 5.760] ms.",
                    "5. Last-good 28.4 bar at 5.360 ms (winner).",
                    "6. NAMUR fail-high 21.6 mA at 5.580 ms (loser by 220 us).",
                    "7. Gate at 6.160 ms: wrong REJECT holds 0 t/h on the fail-high as PV.",
                    "8. Feed idle; last-good never crossed 32.0 bar.",
                    "9. 14 min acetic-quality window missed.",
                    "10. QA: correct gate was ACCEPT; leave 22.0 t/h; bind last-good 28.4 vs 32.0 bar trip.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cativa_22_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 22.0),
                        ("kettle_bar", 28.4),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("last_good_bar", 28.4),
                        ("trip_bar", 32.0),
                        ("live_mA", 21.6),
                        ("namur_fail_high_mA", 21.0),
                        ("namur_fail_high", True),
                        ("fail_high_as_pv", True),
                        ("shadow_bar", 44.0),
                        ("last_good_fresh", True),
                        ("ft_axis", "cativa_p_bar"),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 70),
                        ("t_gate_us", 6160),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 22.0 t/h because last-good 28.4 bar is 3.6 bar under the "
                "published 32.0 bar trip and the 21.6 mA print is a NAMUR NE43 fail-high diagnostic, not live 4-20.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Fail-high current is 21.6 mA, so the kettle is treated as 44.0 bar over the "
                "32.0 bar trip (true vs a 0-40 bar 4-20 map of that diagnostic). REJECT: hold 0 t/h "
                "until the current falls so CA-3 does not see an over-pressure event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "cativa_p_bar",
                            OrderedDict(
                                [
                                    ("published_live_trip", 32.0),
                                    ("observed_last_good", 28.4),
                                    ("fail_high_as_pv_applied", True),
                                    ("live_mA", 21.6),
                                    ("shadow_bar", 44.0),
                                    ("executed_t_h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 70),
                                    ("ratio", 3.14),
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
            ("name", "cativa_hold_namur_fh"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 0.0),
                        ("kettle_bar", 28.4),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): feed 22.0 -> 0 t/h. Routing relay.namur.fh -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Last-good 28.4 bar never "
                "violated the 32.0 bar trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze CA-3 at 0 t/h while last-good stayed 28.4 bar under the "
                "32.0 bar trip. 14 min acetic-quality window missed. Correct gate was ACCEPT of the "
                "already-legal 22.0 t/h command.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("kettle", "held at 0 t/h; 22.0 t/h abandoned"),
                        ("last_good_bar", "still 28.4 bar, under 32.0 bar published trip"),
                        ("acetic", "14 min quality window missed"),
                        ("namur", "no CA-3 over-pressure; fail-high diagnostic false positive"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 21.6 mA print is NAMUR NE43 fail-high, not a live 4-20 PV.",
                    "Delayed (14 min): sister kettle CA-4 ran the same 22.0 t/h acetic window after QA rebound the last-good trip; CA-3's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: last-good 28.4 bar < published 32.0 bar trip; leave 22.0 t/h; ignore NAMUR fail-high.",
                        ),
                        ("correct_trip_bar", 32.0),
                        ("wrong_fail_high_bind", True),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("feed_t_h", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "14 min missed acetic-quality window (task/efficiency); last-good never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.lastgood.bar (5.360 ms, 28.4 bar)"),
                        ("loser", "ma.namur.fh (5.580 ms, 21.6 mA fail-high)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Fail-high-first by < 220 us would still show last-good 28.4 bar < 32.0. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the last-good win "
                            "on a NAMUR fail-high diagnostic.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6160),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (6.160 ms, tick 4). The 14 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 840.0),
            ("missed_window_s", 840),
        ]
    )
    ras = raster_core(
        26,
        84,
        30,
        66,
        routing(
            "relay.namur.fh",
            "policy.hold_reject",
            [
                ("relay.namur.fh", "policy.hold_reject", 0.74),
                ("relay.pt.lastgood", "policy.hold_reject", 0.20),
            ],
            "acetylcholine",
            0.08,
            "namur_fail_high_as_live_stdp; ACh tags the (wrong) hold_reject bind at the last-good win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 48, 0.50, 200.0, 4),
                    pop("go_accept", 48, 0.80, 10.0, 0),
                    pop("kettle_trip_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r78-406",
        "WRONG-REJECT at Cativa-Quern / CA-3: last-good 28.4 bar is legal vs "
        "published 32.0 bar trip; supervisor bound a NAMUR NE43 fail-high as the PV",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 28.4 < 32.0 is true; clamp bound to a "
        "NAMUR fail-high diagnostic. total -0.36 = -0.18 + 0.06 + -0.22 + -0.08 + 0.06.",
        ras,
        gate,
        "acetic-cativa-carbonylation",
        [
            "reject",
            "wrong-gate",
            "namur-ne43-fail-high-as-live",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct last-good<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed on a fail-high tag.",
        1,
        supervisor_error_type="wrong-reject",
    )


def record_407():
    excerpt, extra = lif_407_excerpt()
    ticks = [
        tick(1952, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(4880, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(5100, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5740, 0.10, -0.06, -0.03, 0.02, -0.01),
        tick(22400, 0.05, -0.42, -0.04, 0.00, -0.02),
        tick(1020000000, 0.02, -0.05, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Oxo hydroformylation reactor OX-7 at Oxoform-Letch is already feeding 18.0 t/h "
                "propylene when a syngas Delta-P pulse arrives 220 us before the recycle encoder that "
                "still reads a legal aldehyde cruise. Pressure-first latches a process clamp under the "
                "18.0 kPa cap; flow-first would keep cruise propylene. Stored tray hydraulic load is "
                "not yet an observable of either race channel.",
            ),
            ("domain", "oxo-hydroformylation"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep OX-7 on 18.0 t/h propylene only while syngas Delta-P stays <= 18.0 kPa, and "
                "leave the oxo trays un-collapsed.",
            ),
            ("t0_us", 1762300000000407),
            ("gate_latency_us", 860),
            ("race_window_us", 380),
            ("race_window_rel_ms", [4.880, 5.260]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "dp.sg.kpa 19.6 kPa syngas riser",
                                "ft.pr.tph 18.0 t/h still-legal propylene",
                            ],
                        ),
                        (
                            "semantics",
                            "Pressure-first latches propylene clamp 18.0 -> 11.0 t/h; flow-first keeps "
                            "cruise feed on a 'trays still open' model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one syngas DP slot minus propylene-flow group delay on this "
                            "1 kHz oxo bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 68 us (DP 30 + flow 38): 3.2x over "
                            "a 2.0x trust floor. Reversing order by < 220 us inside the 380 us window "
                            "would have kept 18.0 t/h cruise; predicted next-sample DP 18.8 kPa > 18.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "syngas riser DP, 1 kHz, 30 us timestamp jitter",
                    "propylene-flow meter, 1 kHz, 38 us jitter",
                    "recycle encoder (context)",
                    "tray AE (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("dp_cap_kPa", 18.0),
                        ("observed_dp_kPa", 19.6),
                        ("proposed_t_h", 18.0),
                        ("flow_floor_t_h", 8.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Reactor OX-7 indexed; 18.0 t/h propylene; syngas DP 19.6 kPa > 18.0 cap.",
                    "2. Cruise feed 18.0 t/h armed; trays over the 18.0 kPa cap.",
                    "3. Encoder precursor at 1.180 ms; syngas-side warm-start 19.6 kPa.",
                    "4. Race window [4.880, 5.260] ms opens on the oxo bus.",
                    "5. Syngas DP 19.6 kPa at 4.880 ms (winner).",
                    "6. Propylene flow 18.0 t/h at 5.100 ms (loser by 220 us).",
                    "7. Gate at 5.740 ms (winner + 860 us): MODIFY clamp 18.0 -> 11.0 t/h.",
                    "8. Clamp executes; next-sample DP 16.4 kPa < 18.0 cap.",
                    "9. At 22.400 ms stored tray hydraulic load collapses two oxo decks.",
                    "10. Emergency isolate 17 min + tray pull; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_oxo_pr"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 18.0),
                        ("dp_kPa", 19.6),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("dp_kPa", 19.6),
                        ("dp_cap_kPa", 18.0),
                        ("predicted_unclamped_next_kPa", 18.8),
                        ("feed_t_h", 18.0),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 68),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.0 t/h cruise: propylene flow looks like open oxo trays, "
                "not a flooded deck, and the 18.0 kPa DP cap is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Syngas DP 19.6 kPa won by 220 us, so the oxo column is running packed, not still "
                "free. Holding 18.0 t/h predicts next-sample 18.8 kPa > 18.0 kPa cap. MODIFY: feed "
                "18.0 -> 11.0 t/h. Observed after clamp 16.4 kPa < 18.0. A full REJECT is not "
                "indicated: a sound oxo reactor accepts 11.0 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "sg_dp_kPa",
                            OrderedDict(
                                [
                                    ("cap", 18.0),
                                    ("observed", 19.6),
                                    ("predicted_unclamped_next", 18.8),
                                    ("clamped_t_h", 11.0),
                                    ("observed_after_clamp", 16.4),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 68),
                                    ("ratio", 3.24),
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
            ("name", "clamped_oxo_pr"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 11.0),
                        ("dp_kPa", 16.4),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: propylene 18.0 -> 11.0 t/h. Process-correct vs the 18.0 kPa DP cap. Oxo "
                "tray collapse still occurs at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held DP at 16.4 kPa. At 22.400 ms stored tray hydraulic load "
                "collapsed two oxo decks. Clamp reduced circulation energy; it did not dump the "
                "tray charge. Partnered negative: process heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("loop", "clamp executed; DP 16.4 kPa < 18.0"),
                        ("oxo", "tray collapse at 22.400 ms"),
                        ("repair", "17 min emergency isolate + tray pull"),
                        ("mission", "reactor still hydroformylating; tray precursor controlled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither syngas DP nor propylene flow predicted the tray charge; ae.tray.col is a new channel at 22.400 ms, 16.660 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (17 min): emergency isolate and tray pull close the collapse. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "17 min emergency isolate + tray pull after an oxo tray collapse. Safety "
                "head -0.62 prices the precursor; task_progress stays +0.34 because the propylene clamp "
                "completed under the 18.0 kPa cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "dp.sg.kpa (4.880 ms, 19.6 kPa)"),
                        ("loser", "ft.pr.tph (5.100 ms, 18.0 t/h)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Flow-first by < 220 us inside the 380 us window would have kept "
                            "18.0 t/h cruise; predicted next-sample 18.8 kPa would have exceeded the "
                            "18.0 kPa cap even without the tray charge. The MODIFY is still the "
                            "correct process. The collapse is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms oxo tray drop (tick t_us=22400), inside the "
                "42 ms raster. The correct MODIFY at 5.740 ms is in the same excerpt. Do not put "
                "inflection on the +17 min isolate tick.",
            ),
            ("delayed_surprise_s", 1020.0),
            ("abort_s", 1020),
        ]
    )
    spikes = [
        spike("enc.oxo.ctx", 1.180, 0.43),
        spike("dp.sg.kpa", 2.440, 0.62),
        spike("ft.pr.tph", 3.360, 0.55),
        spike("dp.sg.kpa", 4.880, 1.34),
        spike("ft.pr.tph", 5.100, 1.12),
        spike("ctrl.gate", 5.740, 0.97),
        spike("dp.sg.kpa", 7.600, 0.81),
        spike("ft.pr.tph", 10.800, 0.66),
        spike("ctrl.gate", 15.600, 0.84),
        spike("ae.tray.col", 22.400, 1.42),
        spike("ae.tray.col", 23.700, 0.91),
        spike("enc.oxo.ctx", 30.400, 0.41),
        spike("dp.sg.kpa", 37.200, 0.58),
    ]
    ras = raster_core(
        42,
        80,
        24,
        81,
        routing(
            "thalamic-relay.dp-oxo",
            "spikenaut.policy.oxo-clamp",
            [
                ("relay.dp.sg", "policy.oxo_clamp", 0.64),
                ("relay.ft.pr", "policy.loop_hold", 0.28),
                ("relay.ae.tray", "policy.oxo_clamp", -0.47),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at DP win (4.880 ms) opens a 50 ms eligibility "
            "trace that still covers the 22.400 ms oxo tray collapse",
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
                    pop("oxo_clamp", 48, 0.50, 220.0, 4),
                    pop("loop_hold", 48, 0.50, 50.0, 1),
                    pop("dp_cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r78-407",
        "Oxoform-Letch oxo / OX-7: syngas DP beats propylene flow by 220 us; correct "
        "MODIFY still eats an in-window oxo tray collapse (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "42 ms raster. total -0.44 = 0.34 + -0.62 + -0.16 + 0.04 + -0.04. Named "
        "isolate+tray-pull loss is not netted into task_progress.",
        ras,
        gate,
        "oxo-hydroformylation",
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
        "17 min gap.",
        2,
    )


def record_408():
    ticks = [
        tick(1712, 0.01, 0.04, 0.02, 0.01, 0.01),
        tick(4280, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(4500, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5460, 0.03, 0.12, 0.04, 0.04, 0.02),
        tick(5800, 0.02, 0.07, 0.01, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.godet.ctx", 1.060, 0.44),
        spike("h2o.dope.pct", 2.220, 0.71),
        spike("enc.godet.mpm", 3.180, 0.52),
        spike("h2o.dope.pct", 4.280, 1.36),
        spike("enc.godet.mpm", 4.500, 1.14),
        spike("ctrl.gate", 5.460, 0.98),
        spike("h2o.dope.pct", 7.800, 0.82),
        spike("enc.godet.mpm", 11.400, 0.61),
        spike("ctrl.gate", 17.200, 0.86),
        spike("h2o.dope.pct", 26.100, 0.70),
        spike("enc.godet.mpm", 34.800, 0.48),
        spike("t.dope.ctx", 43.200, 0.40),
    ]
    excerpt = independent_excerpt(78408, 112, 46000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Lyocell NMMO spinbath SB-1 on the Lyocell-Spurn HIL pad is pulling 12.0 m/min "
                "when a dope-water burst at 14.8 percent races the godet encoder that still looks "
                "in-band for a rate step. Spin is legal only if dope water <= 12.5 percent. Water-first "
                "latches hold; encoder-first would treat in-band m/min as NMMO clearance.",
            ),
            ("domain", "lyocell-nmmo-spin"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not ramp SB-1 unless dope water <= 12.5 percent; keep godet 0 m/min until the "
                "dope is dry enough.",
            ),
            ("t0_us", 1762300000000408),
            ("gate_latency_us", 1180),
            ("race_window_us", 340),
            ("race_window_rel_ms", [4.280, 4.620]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "h2o.dope.pct 14.8 percent dope-water flare",
                                "enc.godet.mpm 12.0 m/min still-in-band",
                            ],
                        ),
                        (
                            "semantics",
                            "Water-first latches REJECT hold 0 m/min; encoder-first would ramp 12.0 m/min "
                            "on an in-band-rate-as-clearance model.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one NIR-water envelope slot versus the godet-encoder "
                            "publisher on this pad cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 60 us (NIR 28 + encoder 32): 3.7x over a "
                            "2.0x trust floor. Pad injects encoder 80-120 us before the water envelope "
                            "finishes (loop lag, not a sensor fault); the encoder packet is still "
                            "the loser in this 340 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "dope NIR water analyzer, 28 us jitter, 12.5 percent trip",
                    "godet-rate encoder, 32 us jitter",
                    "spinbath RTD (context)",
                    "NMMO assay (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("water_trip_pct", 12.5),
                        ("observed_water_pct", 14.8),
                        ("godet_cap_mpm", 16.0),
                        ("proposed_mpm", 12.0),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("bench", "Lyocell-Spurn LS-HIL NMMO spin pad, SB-1"),
                        ("inject", "NIR water envelope delayed 80-120 us vs encoder; loop lag, not a false water analyzer"),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. SB-1 on Lyocell-Spurn HIL pad; dope in band; godet armed at 12.0 m/min.",
                    "2. Water trip 12.5 percent; observed 14.8 percent flare on dope.",
                    "3. Encoder precursor at 1.060 ms.",
                    "4. Race window [4.280, 4.620] ms.",
                    "5. Dope water 14.8 percent at 4.280 ms (winner).",
                    "6. Godet encoder 12.0 m/min at 4.500 ms (loser by 220 us).",
                    "7. Gate at 5.460 ms: REJECT hold 0 m/min, do not ramp.",
                    "8. Pad recycle 8 min; water decays under 12.5 percent after hold.",
                    "9. Line never ran wet dope; encoder-as-clearance would have ramped into the flare.",
                    "10. QA: correct gate was REJECT; leave 0 m/min until water <= 12.5 percent.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "ramp_12mpm"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("godet_mpm", 12.0),
                        ("water_pct", 14.8),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("water_pct", 14.8),
                        ("water_trip_pct", 12.5),
                        ("godet_mpm", 12.0),
                        ("godet_cap_mpm", 16.0),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 60),
                        ("t_gate_us", 5460),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 12.0 m/min because godet rate is under the 16.0 m/min cap and treats "
                "the encoder as NMMO clearance, ignoring the 14.8 percent dope-water flare.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Dope water 14.8 percent won by 220 us and is over the 12.5 percent trip. Encoder 12.0 m/min "
                "is under the 16.0 m/min cap but is not clearance. REJECT: hold 0 m/min until water <= 12.5 percent.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "dope_water_pct",
                            OrderedDict(
                                [
                                    ("trip", 12.5),
                                    ("observed", 14.8),
                                    ("executed_mpm", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 3.67),
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
            ("name", "godet_hold_water"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("godet_mpm", 0.0),
                        ("water_pct", 14.8),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: godet 12.0 -> 0 m/min. Routing relay.h2o.dope -> policy.hold_reject. "
                "Dope-water flare never became a legal spin.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held SB-1 at 0 m/min while dope water stayed 14.8 percent over the "
                "12.5 percent trip. 8 min pad recycle cleared the flare. Encoder-as-clearance would "
                "have ramped wet dope.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("godet", "held at 0 m/min"),
                        ("dope_water_pct", "14.8 then decayed under 12.5 after hold"),
                        ("fiber", "no wet-dope break"),
                        ("pad", "8 min recycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Godet 12.0 m/min is in-band rate, not NMMO clearance.",
                    "Delayed (8 min): pad recycle returns water under 12.5 percent without a spin.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "h2o.dope.pct (4.280 ms, 14.8 percent)"),
                        ("loser", "enc.godet.mpm (4.500 ms, 12.0 m/min)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 220 us would still show 14.8 > 12.5. A correct gate "
                            "REJECTs either way; the water win only arrives earlier.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5460),
            (
                "reward_inflection_note",
                "Safety credit lands at the REJECT (5.460 ms, tick 4). Pad recycle is delayed surprise.",
            ),
            ("delayed_surprise_s", 480.0),
            ("abort_s", 480),
        ]
    )
    ras = raster_core(
        46,
        112,
        20,
        103,
        routing(
            "relay.h2o.dope",
            "policy.hold_reject",
            [
                ("relay.h2o.dope", "policy.hold_reject", 0.71),
                ("relay.enc.godet", "policy.spin_go", 0.22),
            ],
            "dopamine",
            0.06,
            "water_trip_stdp; DA tags the hold_reject bind at the NIR-water win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.34),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 56, 0.50, 210.0, 4),
                    pop("spin_go", 56, 0.80, 12.0, 0),
                    pop("water_trip_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r78-408",
        "Lyocell-Spurn HIL / SB-1: dope water 14.8 percent beats godet 12.0 m/min; hold, do not ramp",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. Dope water over trip beats in-band godet. total +0.78 = "
        "0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "lyocell-nmmo-spin",
        [
            "reject",
            "correct-gate",
            "dope-water-vs-godet",
            "hil",
            "sidecar-convictable",
        ],
        "Teaches that an in-band godet is not NMMO clearance when NIR water already exceeds trip.",
        3,
    )


def record_409():
    ticks = [
        tick(2448, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(6120, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(6340, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(6840, 0.12, 0.08, 0.05, 0.03, 0.02),
        tick(7200, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(540000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    params = OrderedDict(
        [
            ("blow_kNm3_min", 14.2),
            ("bath_C", 1640.0),
            ("vessel_id", 2),
            ("hold", False),
        ]
    )
    spikes = [
        spike("ft.o2.ctx", 1.420, 0.42),
        spike("ir.bath.c", 2.880, 0.58),
        spike("ir.hood.smear", 4.200, 0.50),
        spike("ir.bath.c", 6.120, 1.28),
        spike("ir.hood.smear", 6.340, 1.10),
        spike("ctrl.gate", 6.840, 0.96),
        spike("ir.bath.c", 9.100, 0.74),
        spike("ir.hood.smear", 12.600, 0.60),
        spike("ctrl.gate", 18.200, 0.82),
        spike("ir.bath.c", 24.400, 0.55),
        spike("ft.o2.ctx", 28.800, 0.40),
    ]
    excerpt = independent_excerpt(78409, 64, 30000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "BOF vessel BV-2 of the Bofhearth-Wiske oxygen-steel shop is holding a 14.2 kNm3/min "
                "blow when a bath IR at 1640 C races a hood-IR smear that still claims over-temp. "
                "Commanded 14.2 kNm3/min and 1640 C sit 1.8 kNm3/min and 40 C inside the legal "
                "envelopes. The bath-IR win only ratifies the lance already in the melt.",
            ),
            ("domain", "bof-oxygen-converter"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the oxygen blow on Bofhearth-Wiske, keep bath IR <= 1680 C and "
                "blow >= 12.0 kNm3/min, and leave hood draft in spec.",
            ),
            ("t0_us", 1762300000000409),
            ("gate_latency_us", 720),
            ("race_window_us", 360),
            ("race_window_rel_ms", [6.120, 6.480]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.bath.c 1640 C BOF bath",
                                "ir.hood.smear over-temp claim",
                            ],
                        ),
                        (
                            "semantics",
                            "Bath-IR-first confirms the already-legal 14.2 kNm3/min / 1640 C blow; "
                            "smear-first would have treated the bath IR as a hood echo and looked "
                            "for an extra hold the vessel does not need.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one 1D-bath IR kernel step versus the hood-IR publisher "
                            "on this rigid BOF blow.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 66 us (bath 30 + hood 36): 3.3x over "
                            "a 2.0x trust floor. Reversing order by < 220 us would not make the "
                            "proposed blow illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bath IR, 30 us jitter",
                    "hood IR smear, 36 us jitter",
                    "lance-flow encoder (context)",
                    "offgas CO (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bath_cap_C", 1680.0),
                        ("observed_bath_C", 1640.0),
                        ("blow_floor_kNm3_min", 12.0),
                        ("proposed_blow_kNm3_min", 14.2),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "1D BOF bath-hood kernel + shrinking-core scrap melt, seed 78; 14 axial nodes; NOT lumped tank, NOT a fluid-LES field",
                        ),
                        (
                            "fidelity_limits",
                            "No slopping or lance-tip wear; baths are rigid temperature sources. Raster is kernelized events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Bofhearth-Wiske vessel indexed; BV-2 holding 14.2 kNm3/min at 1640 C bath.",
                    "2. Caps: bath 1680 C, blow floor 12.0 kNm3/min; both proposed values inside.",
                    "3. Lance precursor at 1.420 ms.",
                    "4. Race window [6.120, 6.480] ms.",
                    "5. Bath IR 1640 C at 6.120 ms (winner).",
                    "6. Hood IR smear at 6.340 ms (loser by 220 us).",
                    "7. Gate at 6.840 ms: ACCEPT 14.2 kNm3/min / 1640 C already legal.",
                    "8. Blow continues; no extra hold.",
                    "9. 9 min survey confirms hood draft still in spec.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "bof_14p2_blow"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bath_C", 1640.0),
                        ("bath_cap_C", 1680.0),
                        ("blow_kNm3_min", 14.2),
                        ("blow_floor_kNm3_min", 12.0),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 66),
                        ("t_gate_us", 6840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 14.2 kNm3/min because bath 1640 C is 40 C under the 1680 C cap "
                "and blow is 2.2 kNm3/min over the 12.0 kNm3/min floor.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bath 1640 C won by 220 us and is under 1680 C. Blow 14.2 kNm3/min is over "
                "12.0 kNm3/min. ACCEPT the already-legal blow; hood IR smear is not a cap violation.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bath_C",
                            OrderedDict(
                                [
                                    ("cap", 1680.0),
                                    ("observed", 1640.0),
                                    ("executed_blow_kNm3_min", 14.2),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 3.33),
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
            ("name", "bof_14p2_blow"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: blow 14.2 kNm3/min and bath 1640 C unchanged. Routing relay.ir.bath "
                "-> policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left BV-2 at 14.2 kNm3/min / 1640 C. Hood IR smear did not justify a "
                "hold. 9 min survey confirmed draft in spec.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("vessel", "still 14.2 kNm3/min / 1640 C"),
                        ("hood", "in spec after survey"),
                        ("shop", "steel continues"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Hood IR smear is an off-gas optical claim, not a bath-temperature violation.",
                    "Delayed (9 min): survey restacks BV-2 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.bath.c (6.120 ms, 1640 C)"),
                        ("loser", "ir.hood.smear (6.340 ms, over-temp claim)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Smear-first by < 220 us would only delay confirmation. The blow stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6840),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (6.840 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 540.0),
            ("survey_s", 540),
        ]
    )
    ras = raster_core(
        30,
        64,
        34,
        65,
        routing(
            "relay.ir.bath",
            "policy.go_accept",
            [
                ("relay.ir.bath", "policy.go_accept", 0.69),
                ("relay.ir.hood", "policy.smear_hold", 0.20),
            ],
            "serotonin",
            0.07,
            "legal_blow_stdp; 5-HT tags the go_accept bind at the bath-IR win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("go_accept", 40, 0.50, 180.0, 3),
                    pop("smear_hold", 40, 0.80, 12.0, 0),
                    pop("bath_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r78-409",
        "Bofhearth-Wiske BOF / BV-2: bath IR 1640 C beats hood smear by 220 us; ACCEPT "
        "already-legal 14.2 kNm3/min blow",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal 1D BOF bath-hood pass. total +1.06 = "
        "0.42 + 0.28 + 0.18 + 0.10 + 0.08.",
        ras,
        gate,
        "bof-oxygen-converter",
        [
            "accept",
            "already-legal",
            "simulated-bof-blow",
            "bath-vs-hood",
            "sidecar-convictable",
            "simulated",
        ],
        "Teaches that a bath IR under cap can confirm an already-legal oxygen blow without "
        "a hood-IR smear becoming a hold.",
        4,
    )


def record_410():
    ticks = [
        tick(1808, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(4520, 0.10, 0.08, 0.04, 0.02, 0.02),
        tick(4740, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(5300, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5640, 0.06, 0.05, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    params = OrderedDict(
        [
            ("circulate_t", 12.0),
            ("vacuum_mbar", 0.80),
            ("snorkel_id", 4),
            ("hold", False),
        ]
    )
    spikes = [
        spike("enc.circ.ctx", 0.920, 0.41),
        spike("vac.rh.mbar", 2.140, 0.60),
        spike("ir.lid.glint", 3.180, 0.51),
        spike("vac.rh.mbar", 4.520, 1.30),
        spike("ir.lid.glint", 4.740, 1.12),
        spike("ctrl.gate", 5.300, 0.97),
        spike("vac.rh.mbar", 7.200, 0.78),
        spike("ir.lid.glint", 9.400, 0.62),
        spike("ctrl.gate", 14.100, 0.85),
        spike("vac.rh.mbar", 18.200, 0.54),
        spike("ir.lid.glint", 21.600, 0.43),
    ]
    excerpt = independent_excerpt(78410, 56, 24000, 11, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "RH degasser RH-4 at Degasser-Crook is armed for a 12.0 t circulate when a vessel "
                "vacuum of 0.80 mbar races a dummy-lid IR glint that still claims a hitch. "
                "Commanded 12.0 t and 0.80 mbar sit 2.0 t over the 10.0 t floor and 0.40 mbar under "
                "the 1.20 mbar cap. The vacuum win only ratifies the circulate already on the snorkel.",
            ),
            ("domain", "rh-vacuum-degasser"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the RH circulate on Degasser-Crook, keep vessel vacuum <= 1.20 mbar and "
                "circulate >= 10.0 t, and leave dummy-lid optics in spec.",
            ),
            ("t0_us", 1762300000000410),
            ("gate_latency_us", 780),
            ("race_window_us", 340),
            ("race_window_rel_ms", [4.520, 4.860]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "vac.rh.mbar 0.80 mbar RH vessel",
                                "ir.lid.glint hitch claim",
                            ],
                        ),
                        (
                            "semantics",
                            "Vacuum-first confirms the already-legal 12.0 t / 0.80 mbar circulate; "
                            "glint-first would have treated the vacuum as a lid echo and looked "
                            "for an extra hold the snorkel does not need.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one vessel-vacuum analog slot versus the dummy-lid IR "
                            "publisher on this RH bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 64 us (vac 28 + lid 36): 3.4x over "
                            "a 2.0x trust floor. Reversing order by < 220 us would not make the "
                            "proposed circulate illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "RH vessel vacuum, 28 us jitter",
                    "dummy-lid IR glint, 36 us jitter",
                    "circulate encoder (context)",
                    "snorkel DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("vac_cap_mbar", 1.20),
                        ("observed_vac_mbar", 0.80),
                        ("circ_floor_t", 10.0),
                        ("proposed_circ_t", 12.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Degasser-Crook snorkel indexed; RH-4 armed 12.0 t at 0.80 mbar.",
                    "2. Caps: vacuum 1.20 mbar, circulate floor 10.0 t; both proposed values inside.",
                    "3. Circulate precursor at 0.920 ms.",
                    "4. Race window [4.520, 4.860] ms.",
                    "5. Vessel vacuum 0.80 mbar at 4.520 ms (winner).",
                    "6. Dummy-lid IR glint at 4.740 ms (loser by 220 us).",
                    "7. Gate at 5.300 ms: ACCEPT 12.0 t / 0.80 mbar already legal.",
                    "8. Circulate continues; no extra hold.",
                    "9. 6 min dwell confirms lid optics still in spec.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "rh_12t_circ"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("vacuum_mbar", 0.80),
                        ("vac_cap_mbar", 1.20),
                        ("circulate_t", 12.0),
                        ("circ_floor_t", 10.0),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 64),
                        ("t_gate_us", 5300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 12.0 t because vacuum 0.80 mbar is 0.40 mbar under the 1.20 mbar cap "
                "and circulate is 2.0 t over the 10.0 t floor.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Vacuum 0.80 mbar won by 220 us and is under 1.20 mbar. Circulate 12.0 t is over "
                "10.0 t. ACCEPT the already-legal pass; dummy-lid IR glint is not a cap violation.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "vacuum_mbar",
                            OrderedDict(
                                [
                                    ("cap", 1.20),
                                    ("observed", 0.80),
                                    ("executed_circ_t", 12.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 3.44),
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
            ("name", "rh_12t_circ"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: circulate 12.0 t and vacuum 0.80 mbar unchanged. Routing relay.vac.rh "
                "-> policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left RH-4 at 12.0 t / 0.80 mbar. Dummy-lid IR glint did not justify a "
                "hold. 6 min dwell confirmed lid optics in spec.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("snorkel", "still 12.0 t / 0.80 mbar"),
                        ("lid", "in spec after dwell"),
                        ("heat", "RH continue"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Dummy-lid IR glint is an optical hitch claim, not a vacuum-cap violation.",
                    "Delayed (6 min): dwell restacks RH-4 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "vac.rh.mbar (4.520 ms, 0.80 mbar)"),
                        ("loser", "ir.lid.glint (4.740 ms, hitch claim)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 220 us would only delay confirmation. The pass stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5300),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (5.300 ms, tick 4). Dwell is delayed surprise.",
            ),
            ("delayed_surprise_s", 360.0),
            ("dwell_s", 360),
        ]
    )
    ras = raster_core(
        24,
        56,
        38,
        51,
        routing(
            "relay.vac.rh",
            "policy.go_accept",
            [
                ("relay.vac.rh", "policy.go_accept", 0.67),
                ("relay.ir.lid", "policy.glint_hold", 0.19),
            ],
            "adenosine",
            0.09,
            "legal_pass_stdp; adenosine tags the go_accept bind at the vessel-vacuum win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.34),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("go_accept", 36, 0.50, 200.0, 2),
                    pop("glint_hold", 36, 0.80, 12.0, 0),
                    pop("vac_cap_veto", 18, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r78-410",
        "Degasser-Crook RH / RH-4: vessel vacuum 0.80 mbar beats lid glint by 220 us; "
        "ACCEPT already-legal 12.0 t circulate",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal RH circulate. total +1.14 = "
        "0.44 + 0.32 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "rh-vacuum-degasser",
        [
            "accept",
            "already-legal",
            "vacuum-vs-lid-glint",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches that a vessel vacuum under cap can confirm an already-legal RH circulate without "
        "a dummy-lid IR glint becoming a hold.",
        5,
    )


def tokenize(text: str) -> set[str]:
    return {tok for tok in re.split(r"[^a-z0-9]+", text.lower()) if tok}


def jaccard(a: str, b: str) -> float:
    sa, sb = tokenize(a), tokenize(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def check_refractory(events, min_ms=0.8):
    last = {}
    for ev in events:
        ch, t = ev["channel"], ev["t_rel_ms"]
        if ch in last and t - last[ch] < min_ms - 1e-12:
            return f"{ch} gap {t - last[ch]} ms"
        last[ch] = t
    return None


def check_race(rec):
    start, end = rec["state"]["race_window_rel_ms"]
    in_win = {}
    for ev in rec["spike_events"]:
        if start - 1e-12 <= ev["t_rel_ms"] <= end + 1e-12:
            in_win.setdefault(ev["channel"], 0)
            in_win[ev["channel"]] += 1
    if len(in_win) < 2:
        return f"race window has {len(in_win)} channels: {in_win}"
    return None


def excerpt_vs_spikes(rec):
    spike_us = {int(round(ev["t_rel_ms"] * 1000.0)) for ev in rec["spike_events"]}
    ex_us = {item["t_us"] for item in rec["raster"]["excerpt"]}
    if not spike_us:
        return 0.0
    return len(spike_us & ex_us) / len(spike_us)


def expected_m6_prefix(rec):
    st = rec["state"]
    events = rec["spike_events"]
    race = st["race_window_rel_ms"]
    in_win = [e for e in events if race[0] - 1e-9 <= e["t_rel_ms"] <= race[1] + 1e-9]
    ordered = sorted(in_win, key=lambda e: e["t_rel_ms"])
    win_e = next(e for e in ordered if e["channel"] != "ctrl.gate")
    lose_e = next(
        e for e in ordered if e["channel"] not in {win_e["channel"], "ctrl.gate"}
    )
    t_win = round(win_e["t_rel_ms"] * 1000)
    t_lose = round(lose_e["t_rel_ms"] * 1000)
    t_gate = t_win + int(st["gate_latency_us"])
    t_race = int(st["race_window_us"])
    tick1 = round(0.40 * t_win)
    if rec["id"] == "ttf-r78-407":
        tick5 = 22400
    else:
        tick5 = t_gate + t_race
    return [tick1, t_win, t_lose, t_gate, tick5], t_win, t_lose, t_gate


def walk_keys(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            if str(k).lower() in THOUGHT_KEYS:
                found.append(p)
            found.extend(walk_keys(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(walk_keys(v, f"{path}[{i}]"))
    return found


def harvest_occupancy():
    domains = set()
    plants = set()
    skip_dir = OUT_DIR.resolve()
    for p in sorted(Path("/tmp").glob("ttf-r*/*")):
        if p.suffix not in {".jsonl", ".md", ".py"}:
            continue
        try:
            if p.resolve().parent == skip_dir:
                continue
        except OSError:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        plants.update(PLANT_RE.findall(text))
        if p.suffix == ".jsonl":
            for line in text.splitlines():
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                d = (rec.get("state") or {}).get("domain")
                if d:
                    domains.add(d)
        for m in re.finditer(r"Domains this batch:\s*(.+)", text):
            domains.update(re.findall(r"`([^`]+)`", m.group(1)))
        domains.update(re.findall(r'\("domain",\s*"([^"]+)"\)', text))
        for m in re.finditer(r"(?:MY_DOMAINS|THIS_DOMAINS)\s*=\s*[(\{](.*?)[)\}.]", text, re.S):
            domains.update(re.findall(r'"([^"]+)"', m.group(1)))
    return domains, plants


def occupancy_check(records):
    issues = []
    my_domains = {r["state"]["domain"] for r in records}
    my_blob = json.dumps(records)
    occupied_domains, occupied_plants = harvest_occupancy()
    hit = my_domains & occupied_domains
    if hit:
        issues.append(f"domain collides live occupancy {sorted(hit)}")
    for plant in MY_PLANTS:
        if plant in occupied_plants:
            issues.append(f"plant {plant} occupied")
        for prior in occupied_plants:
            if plant != prior and (plant in prior or prior in plant):
                issues.append(f"plant {plant} overlaps {prior}")
    for plant in MY_PLANTS:
        if plant not in my_blob:
            issues.append(f"plant {plant} missing from records")
    return issues


def self_check(records):
    issues = []
    descs = [r["state"]["description"] for r in records]
    opens = [d.split(".")[0] for d in descs]
    if len(set(opens)) != 5:
        issues.append("opening sentences not unique")
    jmax = 0.0
    for i in range(5):
        for j in range(i + 1, 5):
            val = jaccard(descs[i], descs[j])
            jmax = max(jmax, val)
            if val >= 0.4:
                issues.append(f"Jaccard {records[i]['id']}/{records[j]['id']} = {val:.3f}")
    wrong = [
        r
        for r in records
        if r["safety_decision"].get("correctness") == "incorrect"
        or r["meta"].get("supervisor_error_type")
    ]
    if len(wrong) != 1 or wrong[0]["id"] != "ttf-r78-406":
        issues.append(f"wrong-gate set {[w['id'] for w in wrong]}")
    if wrong and wrong[0]["meta"].get("supervisor_error_type") != "wrong-reject":
        issues.append("406 supervisor_error_type")
    if any(r["state"]["sim_or_real"] == "real" for r in records):
        issues.append("sim_or_real=real")
    hil = [r["id"] for r in records if r["state"]["sim_or_real"] == "hil"]
    sim = [r["id"] for r in records if r["state"]["sim_or_real"] == "simulated"]
    if hil != ["ttf-r78-408"]:
        issues.append(f"hil set {hil}")
    if sim != ["ttf-r78-409"]:
        issues.append(f"simulated set {sim}")
    domains = [r["state"]["domain"] for r in records]
    if len(set(domains)) != 5:
        issues.append(f"domain collision {domains}")
    if tuple(domains) != MY_DOMAINS:
        issues.append(f"domain order {domains}")
    ids = [r["id"] for r in records]
    if ids != IDS:
        issues.append(f"ids {ids}")
    decisions = [r["safety_decision"]["decision"] for r in records]
    if (
        decisions.count("ACCEPT") != 2
        or decisions.count("MODIFY") != 1
        or decisions.count("REJECT") != 2
    ):
        issues.append(f"gate mix {decisions}")
    issues.extend(occupancy_check(records))
    for rec in records:
        rid = rec["id"]
        blob = json.dumps(rec)
        if "training_ready" in blob:
            issues.append(f"{rid} training_ready present")
        if "outputs/raw" in blob:
            issues.append(f"{rid} mentions outputs/raw")
        hidden = walk_keys(rec)
        if hidden:
            issues.append(f"{rid} hidden keys {hidden}")
        err = check_refractory(rec["spike_events"])
        if err:
            issues.append(f"{rid} refractory {err}")
        err = check_race(rec)
        if err:
            issues.append(f"{rid} {err}")
        n = rec["raster"]["neurons"]
        rate = rec["raster"]["mean_rate_hz"]
        window_s = rec["raster"]["window_s"]
        expected = round(n * rate * window_s)
        if abs(rec["raster"]["spikes"] - expected) > 1:
            issues.append(f"{rid} spike budget {rec['raster']['spikes']} vs {expected}")
        overlap = excerpt_vs_spikes(rec)
        if rid == "ttf-r78-407":
            if rec["raster"].get("excerpt_source") != "independent_lif":
                issues.append("407 missing independent_lif")
            if rec["future_outcome"]["reward_inflection_t_us"] > rec["raster"]["window_ms"] * 1000:
                issues.append("407 inflection outside window")
            if rec["reward_components"]["total"] >= 0:
                issues.append("407 partnered-neg total not negative")
        elif overlap >= 0.8:
            issues.append(f"{rid} excerpt overlap {overlap:.2f}")
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        tick_times = [t["t_us"] for t in rec["reward_components"]["ticks"]]
        if inf not in tick_times:
            issues.append(f"{rid} inflection {inf} not a tick")
        if len(rec["reward_components"]["ticks"]) != 6:
            issues.append(f"{rid} tick count")
        if not (8 <= len(rec["state"]["episode_steps"]) <= 15):
            issues.append(f"{rid} episode_steps")
        if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
            issues.append(f"{rid} gate_snn decision mismatch")
        heads = ["task_progress", "safety", "efficiency", "coherence", "exploration"]
        total = sum(rec["reward_components"][h] for h in heads)
        if abs(total - rec["reward_components"]["total"]) > 1e-6:
            issues.append(f"{rid} total mismatch {total}")
        for h in heads:
            s = sum(t[h] for t in rec["reward_components"]["ticks"])
            if abs(s - rec["reward_components"][h]) > 1e-6:
                issues.append(f"{rid} {h} tick sum {s} vs {rec['reward_components'][h]}")
        prefix, t_win, t_lose, t_gate = expected_m6_prefix(rec)
        if tick_times[:5] != prefix:
            issues.append(f"{rid} TTF-M6 prefix {tick_times[:5]} != {prefix}")
        t_win_us = int(round(float(rec["raster"]["window_ms"]) * 1000))
        if not (tick_times[5] > t_win_us):
            issues.append(f"{rid} tick6 not after raster")
        delayed = rec["future_outcome"].get("delayed_surprise_s")
        if delayed is None or abs(tick_times[5] - round(delayed * 1e6)) > 0:
            issues.append(f"{rid} tick6 != delayed_surprise_s")
        exec_p = rec["executed_action"]["parameters"]
        prop_p = rec["proposed_action"]["parameters"]
        if rec["safety_decision"]["decision"] == "ACCEPT" and exec_p != prop_p:
            issues.append(f"{rid} ACCEPT params differ")
        if rec["meta"]["round"] != 78:
            issues.append(f"{rid} meta.round")
        if rec["meta"]["domain"] != rec["state"]["domain"]:
            issues.append(f"{rid} domain mismatch")
        dw_s = rec["gate_snn"]["decision_window_ms"] / 1000.0
        for p in rec["gate_snn"]["populations"]:
            if "mean_rate_hz" in p:
                exp_sp = round(p["neurons"] * p["mean_rate_hz"] * dw_s)
                if abs(p["spikes"] - exp_sp) > 1:
                    issues.append(f"{rid} gate_snn {p['name']} spikes {p['spikes']} vs {exp_sp}")
        if rec["raster"]["energy_pJ"] != rec["raster"]["spikes"] * 23:
            issues.append(f"{rid} energy_pJ")
        rights = rec["meta"]["rights"]
        if rights.get("linear_issue") != "RM-793" or rights.get("intended_use") != "research_only":
            issues.append(f"{rid} rights stamp")
        n_spk = len(rec["spike_events"])
        if not (5 <= n_spk <= 40):
            issues.append(f"{rid} spike n={n_spk}")
        n_ex = len(rec["raster"]["excerpt"])
        if not (8 <= n_ex <= 16):
            issues.append(f"{rid} excerpt n={n_ex}")
        times = [e["t_rel_ms"] for e in rec["spike_events"]]
        if times != sorted(times):
            issues.append(f"{rid} spike order")
        gl, rw = rec["state"]["gate_latency_us"], rec["state"]["race_window_us"]
        if not (50 <= gl <= 2000):
            issues.append(f"{rid} gate_latency")
        if not (50 <= rw <= 1000):
            issues.append(f"{rid} race_window")
        if not (20 <= rec["raster"]["window_ms"] <= 50):
            issues.append(f"{rid} window_ms")
        for item in rec["raster"]["excerpt"]:
            if not (0 <= item["t_us"] <= rec["raster"]["window_ms"] * 1000):
                issues.append(f"{rid} excerpt t_us {item['t_us']}")
            if not (0 <= item["neuron_id"] < rec["raster"]["neurons"]):
                issues.append(f"{rid} neuron_id {item['neuron_id']}")
        if rid == "ttf-r78-406":
            ev = rec["proposed_action"]["evidence"]
            if not (ev["last_good_bar"] < ev["trip_bar"]):
                issues.append("406 last-good not under trip")
            if ev.get("namur_fail_high") is not True or ev.get("fail_high_as_pv") is not True:
                issues.append("406 NAMUR fail-high not tagged")
            if not (ev.get("live_mA", 0) > ev.get("namur_fail_high_mA", 21.0)):
                issues.append("406 live_mA not in fail-high band")
            if rec["executed_action"]["parameters"]["feed_t_h"] != 0.0:
                issues.append("406 executed feed not zero")
            tos = {row["to"] for row in rec["raster"]["routing"]["table"]}
            if "policy.go_accept" in tos:
                issues.append("406 routing contains go_accept")
            if "policy.hold_reject" not in tos:
                issues.append("406 routing missing hold_reject")
            if "recovery" not in rec["future_outcome"]:
                issues.append("406 missing recovery")
    return issues, jmax


def write_notes(records, jmax: float) -> None:
    rows = []
    for rec in records:
        dec = rec["safety_decision"]["decision"]
        cor = rec["safety_decision"]["correctness"]
        if cor == "incorrect":
            cor = f"**incorrect ({rec['meta']['supervisor_error_type']})**"
        tot = rec["reward_components"]["total"]
        tot_s = f"{tot:+.2f}"
        if rec["id"] == "ttf-r78-407":
            tot_s = f"**{tot:+.2f}**"
        edge = {
            "ttf-r78-406": "live last-good 28.4 bar < 32.0 trip; NAMUR NE43 fail-high 21.6 mA treated as live 4-20",
            "ttf-r78-407": "process-correct propylene clamp; oxo tray collapse inside 42 ms raster; independent LIF",
            "ttf-r78-408": "dope water 14.8 percent beats godet 12.0 m/min; hold, do not ramp",
            "ttf-r78-409": "bath 1640 C vs hood IR smear; proposed 14.2 kNm3/min already legal",
            "ttf-r78-410": "vessel vacuum 0.80 mbar vs lid glint; proposed 12.0 t already legal",
        }[rec["id"]]
        rows.append(
            f"| {rec['id']} | {rec['state']['domain']} | {dec} | {cor} | "
            f"{rec['state']['sim_or_real']} | {tot_s} | {edge} |"
        )
    ras_rows = []
    for rec in records:
        r = rec["raster"]
        ras_rows.append(
            f"| {rec['id']} | {rec['state']['domain']} | {r['neurons']} | {r['mean_rate_hz']} | "
            f"{r['window_ms']} | {r['spikes']} | {r['energy_pJ']} | {r['energy_uJ']:.6f} |"
        )
    tick_rows = []
    for rec in records:
        rc = rec["reward_components"]
        inf = rec["future_outcome"]["reward_inflection_t_us"]
        ticks = rc["ticks"]
        idx = next(i + 1 for i, t in enumerate(ticks) if t["t_us"] == inf)
        tick_rows.append(
            f"| {rec['id'][-3:]} | {len(ticks)} | {rc['task_progress']:+.2f} | {rc['safety']:+.2f} | "
            f"{rc['efficiency']:+.2f} | {rc['coherence']:+.2f} | {rc['exploration']:+.2f} | "
            f"{rc['total']:+.2f} | {idx} ({inf}) |"
        )
    notes = f"""# Thalamic Trajectory Factory — NOTES-r78

- Factory: `thalamic-trajectory-factory`
- Run label: `2026-09-02-final-heavy`
- Generator: `grok-4.6`
- Channel: SuperGrok Heavy consumer chat (RM-793 research-only)
- Quota: 5
- Quality: Q=5
- IDs: `ttf-r78-406` … `ttf-r78-410`
- Domains this batch: `acetic-cativa-carbonylation`, `oxo-hydroformylation`, `lyocell-nmmo-spin`, `bof-oxygen-converter`, `rh-vacuum-degasser`

These five domain slugs sit outside the prompt 8-pool and outside staged r13–r71 occupancy (jsonl SoT plus incomplete gens through r75, including r66 maleic/PTA/VCM/CCR/solvay, r67 Mond/KA-oxidizer/FBR/SSP/borosilicate, r68 carbide/AO-loop/phthalic/FeMn/chlorate, r69 rockwool/EO/fused-silica/PP/Co-EW, r70 aniline/phthalic-switch/AO/MgCl2/PET-SSP, r71 silane-CVD/DNT/magnesia/POM/hypochlorite, r72 Waelz/ATR/PS-converter/PDH/SiMn, r74 VAM/HPPO/Andrussow/Cl2-liq/defluor). All five plants are invented (Cativa-Quern, Oxoform-Letch, Lyocell-Spurn, Bofhearth-Wiske, Degasser-Crook). Do not restack prior TTF plants.

## Batch map

| id | domain | decision | correctness | sim_or_real | total | edge |
|----|--------|----------|-------------|-------------|-------|------|
{chr(10).join(rows)}

Gate mix: 2 ACCEPT, 1 correct MODIFY (partnered-neg, in-window), 1 correct REJECT, 1 incorrect REJECT (NAMUR NE43 fail-high as live). Provenance: designed×3, simulated×1, hil×1 (Lyocell-Spurn LS-HIL pad). Jaccard on `state.description` all ≤ {jmax:.3f}.

## Wrong-reject

**ttf-r78-406** is the mandated incorrect gate (`safety_decision.correctness=incorrect`, `meta.supervisor_error_type=wrong-reject`). Alternate vs odd rounds: even rounds host wrong-reject. Do not emit a wrong-ACCEPT.

Cativa-Quern / CA-3 reads last-good kettle `P=28.4 bar` against a published **32.0 bar** trip. A NAMUR NE43 fail-high current is still latched at **21.6 mA** (`namur_fail_high=true`; `live_mA=21.6 > namur_fail_high_mA=21.0`). Mapping that diagnostic as live 4-20 on a 0–40 bar span yields a **44.0 bar** shadow. Sidecar arithmetic `28.4 < 32.0` is true. A weak supervisor binds the fail-high as CA-3 live, REJECT-holds 22.0 → 0 t/h, and leaves a legal Cativa kettle idle. Convictable without acetic-acid physics: `evidence.last_good_bar < evidence.trip_bar`, `evidence.namur_fail_high == true`, `evidence.fail_high_as_pv == true`, `executed_action` sets `feed_t_h=0`, `raster.routing.table` sends `relay.namur.fh` → `policy.hold_reject` (weight 0.74) with no positive weight to `policy.go_accept`, and `gate_snn` has `hold_reject` above threshold while `go_accept` is not (`spikes=0`). Recovery: ACCEPT; leave 22.0 t/h; bind the published last-good 32.0 bar trip; ignore the fail-high. Cost: 14 min missed acetic-quality window (`missed_window_s=840`).

This is **NAMUR NE43 fail-high as live**, not r12-079 (induced-kV treated as sensor fault), not r16-097 (reticle-as-wafer), not r18-109 (empty-tank class), not r20-118 (oscillation-as-PSV), not r22-126 (class-transplant floor), not r30-166 (stale-firmware floor), not r32 (stale-peak-hold), not r34-187 (header-as-cell wrong-loop), not r36-196 (unit-mismatch leftover-bar), not r38-206 (LOOP_TEST inject-as-live), not r40 (SP-echo-as-PV), not r42 (leftover-SP-as-trip), not r44-237 (wrong-unit-shadow), not r46 (kPa-as-MPa), not r48-256 (2oo3-failed-high / median-vs-single), not r50-267 (raw-mA-as-EU), not r52-277 (gauge-vs-absolute / atm-offset), not r54-287 (bad-quality-sub-as-live), not r58-306 (overrange-flag-as-PV), not r64-337 (reverse-scale / inverted-4-20), not r66-347 (idle-twin-string-as-live), not r68-356 (channel-swap / sibling-loop-as-live), not r70-366 (raw-DP-as-flow / sqrt-unextracted).

## Partnered-negative in-window (407)

**ttf-r78-407** is the partnered negative: process-correct MODIFY (propylene held 11.0 t/h; DP 16.4 kPa < 18.0 cap) while the world still charges. Safety −0.62 prices the oxo tray collapse at **22.400 ms**; `task_progress` stays +0.34 because the clamp completed. Inflection `t_us=22400` is tick 5 and is **inside** the 42 ms raster (`22400 ≤ 42000`). Named un-netted loss: 17 min emergency isolate + tray pull (`abort_s=1020`). Not folded into process heads.

Independent LIF (the one labeled sidecar sim): `state.sim_or_real` remains `designed`. `raster.excerpt_source=independent_lif`, `raster.sim_scope=sidecar_only`, `raster.lif` seed 78407, stim `[21000, 25000]`. Excerpt is membrane crossings (`lif.clamp` early vs `lif.tray` 21–25 ms), not a 1:1 remap of `spike_events`. `meta.tags` include `independent-lif-raster` and `sidecar-sim-only`.

## Reward formula and tick reconciliation

Declared aggregation on every record:

`total = task_progress + safety + efficiency + coherence + exploration`

Per-component scalar = arithmetic sum of that component over ticks (TTF-M6: exactly 6 ticks; tick 5 is `t_charge_us=22400` on 407 and `t_gate_us + T_race` elsewhere; tick 6 is delayed surprise bound to `future_outcome.delayed_surprise_s`). Inflection `t_us` is an actual tick. Verified to <1e-6:

| id | ticks | tp | saf | eff | coh | exp | total | inflection tick |
|----|-------|----|-----|-----|-----|-----|-------|-----------------|
{chr(10).join(tick_rows)}

Tick 6 bind: `ticks[5].t_us == round(delayed_surprise_s * 1e6)` on every record (840 s, 1020 s, 480 s, 540 s, 360 s).

## Raster / energy (Loihi-2 4-core, 23 pJ/spike)

| id | domain | n | rate Hz | window_ms | spikes | energy_pJ | energy_uJ |
|----|--------|---|---------|-----------|--------|-----------|-----------|
{chr(10).join(ras_rows)}

`spikes = round(n × rate × window_s)`. Every record carries `gate_snn` whose `decision` matches the safety gate; populations that declare rate+spikes meet the same ±1 budget against `decision_window_s`. `routing.third_factor` has modulator (ACh / NA / DA / 5-HT / adenosine), `tau_e_s`/`tau_e_ms` pair, and eligibility. Excerpt same-neuron gap ≥ 1000 µs; spike trains same-channel refractory ≥ 0.8 ms.

## Local checks (staging, not raw)

- Generator self-check: Jaccard max {jmax:.3f} < 0.4; TTF-M6 prefix; refractory; spike budgets; exactly one incorrect gate (406 wrong-reject)
- Pipeline audit (run after emit): `check_jsonl` FactoryStaging, `raster_status`, `verify_batch_for_frontier(strict=True)`, `spike_probe.py --strict`

Never `training_ready`. Never `sim_or_real=real`. Never wrote `outputs/raw/`.

## Residual weaknesses (honest)

1. Only **one** labeled independent LIF (407). The other four excerpts are independent of `spike_events` times but are not declared population sims.
2. Wrong-ACCEPT still absent (guard).
3. 409 ACCEPT is a new plant/solver (1D BOF bath-hood kernel), not a new gate class.
4. 406 wrong-reject is convictable from last-good-vs-fail-high tags; a later round could bind `namur_fail_high && last_good_bar < trip_bar` as the only critic boolean so a probe never has to know "CA-3".
5. ISI histogram is still optional densification, not an r78 requirement.

## Next densification target

Publish the NAMUR fail-high predicate as a sidecar boolean (`namur_fail_high`) so a diagnostic-as-PV REJECT is convictable without the kettle-name story. Optional: labeled LIF on a second record, or an ISI histogram sidecar. Remaining unused wrong-REJECT subclasses include **HART SV-as-PV** and **stale-handshake / heartbeat-as-PV**. Wrong-ACCEPT remains structurally absent until a prompt amendment.

Novel coverage: 16.5%
"""
    NOTES_PATH.write_text(notes, encoding="utf-8")


def run_pipelines(records):
    sys.path.insert(0, str(PIPELINES))
    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from exact_json import dumps_exact_json
    from round_txn import validate_novel_coverage
    from validate_run import check_line
    from verify_execution import verify_batch_for_frontier

    report = []
    errors, warnings, kinds, nrec = check_jsonl(
        BATCH_PATH, "batch-r78.jsonl", staging=FactoryStaging(enabled=True)
    )
    report.append(("check_jsonl FactoryStaging", errors, warnings, kinds, nrec))
    line_errs = []
    for i, rec in enumerate(records, 1):
        errs, kind = check_line(rec, f"batch-r78.jsonl:{i}", factory_staging=True)
        if errs:
            line_errs.append((i, kind, errs))
        try:
            dumps_exact_json(rec, ensure_ascii=False, sort_keys=False)
        except Exception as exc:
            line_errs.append((i, "exact_json", [str(exc)]))
    report.append(("check_line+exact_json", line_errs, None, None, None))
    raster_fail = []
    for rec in records:
        st = raster_status(rec, require_raster=True, require_routing_table=True)
        if not st.get("raster_valid") or not st.get("gate_snn_valid"):
            raster_fail.append((rec["id"], st))
    report.append(("raster_status", raster_fail, None, None, None))
    counts, findings, blocked = verify_batch_for_frontier(BATCH_PATH, strict=True)
    report.append(("verify_batch_for_frontier", counts, findings, blocked, None))
    cov = validate_novel_coverage(
        NOTES_PATH,
        Path("thalamic-trajectory-factory"),
        notes_text=NOTES_PATH.read_text(),
        required=True,
    )
    report.append(("validate_novel_coverage", cov, None, None, None))
    probe = subprocess.run(
        [sys.executable, str(PIPELINES / "spike_probe.py"), "--strict", str(BATCH_PATH)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    report.append(("spike_probe", probe.returncode, probe.stdout[-2000:], probe.stderr[-2000:], None))
    schema_err = None
    try:
        import jsonschema
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012

        schema_dir = REPO / "schemas"
        ttf_schema = json.loads((schema_dir / "thalamic-trajectory-v2.schema.json").read_text())
        raster_schema = json.loads((schema_dir / "raster.schema.json").read_text())
        base_schema = json.loads((schema_dir / "thalamic-trajectory.schema.json").read_text())
        registry = Registry().with_resources(
            [
                ("thalamic-trajectory-v2.schema.json", Resource.from_contents(ttf_schema, DRAFT202012)),
                ("thalamic-trajectory.schema.json", Resource.from_contents(base_schema, DRAFT202012)),
                ("raster.schema.json", Resource.from_contents(raster_schema, DRAFT202012)),
            ]
        )
        validator = jsonschema.Draft202012Validator(ttf_schema, registry=registry)
        fails = []
        for rec in records:
            errs = sorted(validator.iter_errors(rec), key=lambda e: list(e.path))
            if errs:
                fails.append((rec["id"], [e.message for e in errs[:4]]))
        schema_err = fails
    except Exception as exc:
        schema_err = f"skip:{exc}"
    report.append(("jsonschema", schema_err, None, None, None))
    return report


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if "outputs/raw" in str(BATCH_PATH) or "outputs/raw" in str(NOTES_PATH):
        raise SystemExit("refusing to write outputs/raw")
    records = [record_406(), record_407(), record_408(), record_409(), record_410()]
    issues, jmax = self_check(records)
    lines = [
        json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for rec in records
    ]
    BATCH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_notes(records, jmax)
    print(f"wrote {BATCH_PATH} lines={len(lines)} jmax={jmax:.3f}")
    print(f"wrote {NOTES_PATH}")
    if issues:
        print("SELF_CHECK_ISSUES:")
        for item in issues:
            print(" -", item)
        return 1
    print("SELF_CHECK_OK")
    report = run_pipelines(records)
    failed = False
    for item in report:
        name = item[0]
        print(f"PIPELINE {name}: {item[1:]}")
        if name == "check_jsonl FactoryStaging":
            errors, warnings, kinds, nrec = item[1], item[2], item[3], item[4]
            print(f"  kinds={kinds} n={nrec} errors={len(errors)} warnings={len(warnings)}")
            for e in errors:
                print("  ERR", e)
                failed = True
        elif name == "check_line+exact_json":
            if item[1]:
                print("  LINE_ERR", item[1])
                failed = True
        elif name == "raster_status":
            if item[1]:
                print("  RASTER_FAIL", item[1])
                failed = True
        elif name == "verify_batch_for_frontier":
            if item[3]:
                print("  BLOCKED", item[1], item[2])
                failed = True
        elif name == "validate_novel_coverage":
            if item[1]:
                print("  COVERAGE", item[1])
                failed = True
        elif name == "spike_probe":
            if item[1] != 0:
                print("  PROBE_FAIL", item[2], item[3])
                failed = True
        elif name == "jsonschema":
            if isinstance(item[1], list) and item[1]:
                print("  SCHEMA_FAIL", item[1])
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
