def lif_257_excerpt():
    """Independent CUBA LIF (seed 48257). Plant remains designed."""

    n = 84
    dt_us = 100
    tau_m_ms = 20.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.92
    i_stim_peak = 2.45
    stim = (21000, 25000)
    seed = 48257
    window_us = 40000
    i_clamp_extra = 0.68
    clamp_n = 14
    rng = random.Random(seed)
    tau_s = tau_m_ms / 1000.0
    dt_s = dt_us / 1e6
    decay = math.exp(-dt_s / tau_s)
    steps = window_us // dt_us
    voltage = [rng.random() * v_th * 0.98 for _ in range(n)]
    bias = [i_bias * (1.0 + 0.12 * (rng.random() * 2 - 1)) for _ in range(n)]
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
    take(burst, 9, label_times=(22400, 23100, 23800))
    clamp = [(t, nid) for t, nid in picked if t < 21000][:7]
    mist = [(t, nid) for t, nid in picked if t >= 21000][:9]
    picked = sorted(clamp + mist, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise RuntimeError(f"LIF excerpt too short: {len(picked)}")
    channels = ["lif.clamp" if t < 21000 else "lif.mist" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 84),
            ("dt_us", 100),
            ("tau_m_ms", 20.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.92),
            ("i_stim_peak", 2.45),
            ("stim_t_us", [21000, 25000]),
            ("i_clamp_extra", 0.68),
            ("clamp_n", 14),
            ("seed", 48257),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.68 ID-fan-clamp bias; stim 21-25 ms is the mist-eliminator pack collapse.",
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


def record_256():
    ticks = [
        tick(2112, -0.02, 0.01, -0.02, -0.01, 0.01),
        tick(5280, -0.04, 0.01, -0.04, -0.02, 0.01),
        tick(5510, -0.03, 0.01, -0.03, -0.01, 0.01),
        tick(6000, -0.06, 0.02, -0.08, -0.03, 0.02),
        tick(6400, -0.02, 0.01, -0.03, -0.01, 0.01),
        tick(780000000, -0.01, 0.00, -0.02, 0.00, 0.00),
    ]
    spikes = [
        spike("enc.feed.ctx", 1.205, 0.44),
        spike("rtd.median.c", 2.410, 0.61),
        spike("rtd.failed.c", 3.880, 0.52),
        spike("bus.soaker.ctx", 4.620, 0.47),
        spike("rtd.median.c", 5.280, 1.31),
        spike("rtd.failed.c", 5.510, 1.18),
        spike("ctrl.gate", 6.000, 0.99),
        spike("rtd.median.c", 7.220, 0.84),
        spike("rtd.failed.c", 9.440, 0.66),
        spike("ctrl.gate", 14.880, 0.88),
        spike("enc.feed.ctx", 18.400, 0.41),
        spike("rtd.median.c", 24.200, 0.58),
    ]
    excerpt = independent_excerpt(48256, 80, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Soaker drum SN-6 at Soaker-Naze already holds a 2oo3 median of 412 C when that "
                "median sample races a stuck-high RTD-B that still prints 448 C. Published trip "
                "is 430 C on the median; a weak supervisor treats the failed channel as the vote "
                "and zeros a legal 18.0 t/h visbreaker feed.",
            ),
            ("domain", "visbreaker-soaker"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 18.0 t/h on SN-6, keep 2oo3 median T < 430 C trip, and finish the "
                "13 min residue window.",
            ),
            ("t0_us", 1762300000000256),
            ("gate_latency_us", 720),
            ("race_window_us", 400),
            ("race_window_rel_ms", [5.280, 5.680]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.median.c 412 C live 2oo3 median",
                                "rtd.failed.c 448 C RTD-B stuck-high",
                            ],
                        ),
                        (
                            "semantics",
                            "Median-first should ACCEPT 18.0 t/h (412 C < 430 C trip). "
                            "Failed-channel-first would only delay confirmation of the same legal median.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one soaker 2oo3 median slot versus the failed-channel publisher "
                            "on this 2 kHz visbreaker bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 76 us (median 34 + failed 42): 3.0x over "
                            "a 2.0x trust floor. Order is correctly median-first. The error is binding "
                            "a stuck-high RTD-B as if it were the 2oo3 vote, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "2oo3 soaker RTD median, 2 kHz, 34 us jitter, axis soaker_t",
                    "RTD-B failed-high, 1 kHz, 42 us jitter, vote_failed true",
                    "feed-mass encoder (context)",
                    "coil-outlet IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("median_C", 412.0),
                        ("trip_C", 430.0),
                        ("failed_C", 448.0),
                        ("failed_channel", "RTD-B"),
                        ("vote_failed", True),
                        ("proposed_t_h", 18.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Soaker SN-6 indexed on Soaker-Naze; live median 412 C, 18.0 t/h armed.",
                    "2. Published 2oo3 trip 430 C; RTD-B tagged vote_failed and stuck at 448 C.",
                    "3. Encoder precursor at 1.205 ms.",
                    "4. Race window [5.280, 5.680] ms.",
                    "5. Median 412 C at 5.280 ms (winner).",
                    "6. Failed RTD-B 448 C at 5.510 ms (loser by 230 us).",
                    "7. Gate at 6.000 ms: wrong REJECT holds 0 t/h on the failed channel.",
                    "8. Feed idle; median never crossed 430 C.",
                    "9. 13 min residue window missed.",
                    "10. QA: correct gate was ACCEPT; leave 18.0 t/h; bind median 412 vs 430 C trip.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "soaker_18_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 18.0),
                        ("median_C", 412.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("median_C", 412.0),
                        ("trip_C", 430.0),
                        ("failed_C", 448.0),
                        ("failed_channel", "RTD-B"),
                        ("vote_failed", True),
                        ("ft_axis", "soaker_t"),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 76),
                        ("t_gate_us", 6000),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.0 t/h because 2oo3 median 412 C is 18 C under the published "
                "430 C trip and the 448 C reading is a vote_failed RTD-B stuck-high.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "RTD-B 448 C is over the 430 C trip (true vs that failed channel). REJECT: "
                "hold 0 t/h until the failed channel recovers under 430 C so the soaker does not "
                "see an over-temperature event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "soaker_t_C",
                            OrderedDict(
                                [
                                    ("published_median_trip", 430.0),
                                    ("observed_median", 412.0),
                                    ("failed_channel_applied", 448.0),
                                    ("failed_channel", "RTD-B"),
                                    ("executed_t_h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 230),
                                    ("combined_jitter_us", 76),
                                    ("ratio", 3.03),
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
            ("name", "soaker_hold_failed_vote"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 0.0),
                        ("median_C", 412.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): feed 18.0 -> 0 t/h. Routing relay.rtd.failed -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Median 412 C never "
                "violated the 430 C trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze SN-6 at 0 t/h while 2oo3 median stayed 412 C under the "
                "430 C trip. 13 min residue window missed. Correct gate was ACCEPT of the "
                "already-legal 18.0 t/h command.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("soaker", "held at 0 t/h; 18.0 t/h abandoned"),
                        ("median_C", "still 412 C, under 430 C published trip"),
                        ("coil", "13 min residue window missed"),
                        ("vote", "no over-temperature; RTD-B false positive"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 448 C reading is a vote_failed RTD-B stuck-high, not a published 2oo3 trip.",
                    "Delayed (13 min): sister soaker SN-7 ran the same 18.0 t/h residue window after QA rebound the median trip; SN-6's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: median 412 C < published 430 C trip; leave 18.0 t/h.",
                        ),
                        ("correct_trip_C", 430.0),
                        ("wrong_failed_C", 448.0),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("feed_t_h", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "13 min missed residue window (task/efficiency); median never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.median.c (5.280 ms, 412 C)"),
                        ("loser", "rtd.failed.c (5.510 ms, 448 C RTD-B)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "Failed-channel-first by < 230 us would still show median 412 C < 430 C. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the median win "
                            "on a stuck-high RTD-B.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6000),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (6.000 ms, tick 4). The 13 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 780.0),
            ("missed_window_s", 780),
        ]
    )
    ras = raster_core(
        26,
        80,
        30,
        62,
        routing(
            "relay.rtd.failed",
            "policy.hold_reject",
            [
                ("relay.rtd.failed", "policy.hold_reject", 0.71),
                ("relay.rtd.median", "policy.hold_reject", 0.22),
            ],
            "acetylcholine",
            0.08,
            "failed_vote_stdp; ACh tags the (wrong) hold_reject bind at the median win",
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
                    pop("median_trip_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r48-256",
        "WRONG-REJECT at Soaker-Naze / SN-6: 2oo3 median 412 C is legal vs "
        "published 430 C trip; supervisor bound a stuck-high RTD-B 448 C as the vote",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 412 < 430 is true; clamp bound to a "
        "vote_failed RTD-B 448 C. total -0.36 = -0.18 + 0.06 + -0.22 + -0.08 + 0.06.",
        ras,
        gate,
        "visbreaker-soaker",
        [
            "reject",
            "wrong-gate",
            "2oo3-failed-high",
            "median-vs-single",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct median<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed.",
        1,
        supervisor_error_type="wrong-reject",
    )


def record_257():
    excerpt, extra = lif_257_excerpt()
    ticks = [
        tick(1848, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(4620, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(4850, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5500, 0.10, -0.06, -0.03, 0.02, -0.01),
        tick(22400, 0.05, -0.42, -0.04, 0.00, -0.02),
        tick(960000000, 0.02, -0.05, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Absorber A-2 at Limestone-Linn is already pulling 92 percent ID-fan when a "
                "gas-side Delta-P pulse arrives 230 us before the recycle-pH probe that still "
                "reads a legal slurry. Pressure-first latches a process clamp under the 2.20 kPa "
                "cap; pH-first would keep cruise fan. Stored mist-eliminator pack load is not "
                "yet an observable of either race channel.",
            ),
            ("domain", "wet-FGD-absorber"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep A-2 on 92 percent ID-fan only while gas Delta-P stays <= 2.20 kPa, and "
                "leave the mist-eliminator pack un-collapsed.",
            ),
            ("t0_us", 1762300000000257),
            ("gate_latency_us", 880),
            ("race_window_us", 380),
            ("race_window_rel_ms", [4.620, 5.000]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "dp.gas.kpa 2.48 kPa absorber gas",
                                "ph.recycle.su 5.60 still-legal slurry",
                            ],
                        ),
                        (
                            "semantics",
                            "Pressure-first latches ID-fan clamp 92 -> 78 percent; pH-first keeps "
                            "cruise fan on a 'slurry still open' model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one gas-side DP slot minus recycle-pH group delay on this "
                            "1 kHz absorber bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 68 us (DP 30 + pH 38): 3.4x over "
                            "a 2.0x trust floor. Reversing order by < 230 us inside the 380 us window "
                            "would have kept 92 percent cruise; predicted next-sample DP 2.31 kPa > 2.20 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "absorber gas DP, 1 kHz, 30 us timestamp jitter",
                    "recycle-slurry pH, 1 kHz, 38 us jitter",
                    "ID-fan encoder (context)",
                    "mist-eliminator AE (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("dp_cap_kPa", 2.20),
                        ("observed_dp_kPa", 2.48),
                        ("proposed_fan_pct", 92.0),
                        ("fan_floor_pct", 60.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Absorber A-2 indexed; 92 percent ID-fan; gas DP 2.48 kPa > 2.20 cap.",
                    "2. Cruise fan 92 percent armed; bed over the 2.20 kPa cap.",
                    "3. Encoder precursor at 1.848 ms; gas-side warm-start 2.48 kPa.",
                    "4. Race window [4.620, 5.000] ms opens on the absorber bus.",
                    "5. Gas DP 2.48 kPa at 4.620 ms (winner).",
                    "6. Recycle pH 5.60 at 4.850 ms (loser by 230 us).",
                    "7. Gate at 5.500 ms (winner + 880 us): MODIFY clamp 92 -> 78 percent.",
                    "8. Clamp executes; next-sample DP 1.64 kPa < 2.20 cap.",
                    "9. At 22.400 ms stored pack load collapses a mist-eliminator bay.",
                    "10. Emergency isolate 16 min + pack pull; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_id_fan"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("fan_pct", 92.0),
                        ("dp_kPa", 2.48),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("dp_kPa", 2.48),
                        ("dp_cap_kPa", 2.20),
                        ("predicted_unclamped_next_kPa", 2.31),
                        ("fan_pct", 92.0),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 68),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 92 percent cruise: recycle pH looks like an open slurry, not a "
                "plugged pack, and the 2.20 kPa DP cap is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Gas DP 2.48 kPa won by 230 us, so the absorber is running packed, not still "
                "free. Holding 92 percent predicts next-sample 2.31 kPa > 2.20 kPa cap. MODIFY: fan "
                "92 -> 78 percent. Observed after clamp 1.64 kPa < 2.20. A full REJECT is not "
                "indicated: a sound absorber accepts 78 percent.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "gas_dp_kPa",
                            OrderedDict(
                                [
                                    ("cap", 2.20),
                                    ("observed", 2.48),
                                    ("predicted_unclamped_next", 2.31),
                                    ("clamped_fan_pct", 78.0),
                                    ("observed_after_clamp", 1.64),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 230),
                                    ("combined_jitter_us", 68),
                                    ("ratio", 3.38),
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
            ("name", "clamped_id_fan"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("fan_pct", 78.0),
                        ("dp_kPa", 1.64),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: ID-fan 92 -> 78 percent. Process-correct vs the 2.20 kPa DP cap. Mist-eliminator "
                "pack collapse still occurs at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held DP at 1.64 kPa. At 22.400 ms stored pack load collapsed "
                "a mist-eliminator bay. Clamp reduced fan energy; it did not dump the pack charge. "
                "Partnered negative: process heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("fan", "clamp executed; DP 1.64 kPa < 2.20"),
                        ("mist_eliminator", "pack collapse at 22.400 ms"),
                        ("repair", "16 min emergency isolate + pack pull"),
                        ("mission", "absorber still scrubbing; pack precursor controlled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither gas DP nor recycle pH predicted the pack charge; ae.mist.pack is a new channel at 22.400 ms, 16.900 ms after the gate, still inside the 40 ms raster.",
                    "Delayed (16 min): emergency isolate and pack pull close the collapse. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "16 min emergency isolate + pack pull after a mist-eliminator collapse. Safety "
                "head -0.62 prices the precursor; task_progress stays +0.34 because the fan clamp "
                "completed under the 2.20 kPa cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "dp.gas.kpa (4.620 ms, 2.48 kPa)"),
                        ("loser", "ph.recycle.su (4.850 ms, 5.60 pH)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "pH-first by < 230 us inside the 380 us window would have kept "
                            "92 percent cruise; predicted next-sample 2.31 kPa would have exceeded the "
                            "2.20 kPa cap even without the pack charge. The MODIFY is still the "
                            "correct process. The collapse is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms mist-eliminator pack drop (tick t_us=22400), inside the "
                "40 ms raster. The correct MODIFY at 5.500 ms is in the same excerpt. Do not put "
                "inflection on the +16 min isolate tick.",
            ),
            ("delayed_surprise_s", 960.0),
            ("abort_s", 960),
        ]
    )
    spikes = [
        spike("enc.fan.ctx", 1.120, 0.43),
        spike("dp.gas.kpa", 2.240, 0.62),
        spike("ph.recycle.su", 3.180, 0.55),
        spike("dp.gas.kpa", 4.620, 1.34),
        spike("ph.recycle.su", 4.850, 1.12),
        spike("ctrl.gate", 5.500, 0.97),
        spike("dp.gas.kpa", 7.200, 0.81),
        spike("ph.recycle.su", 10.400, 0.66),
        spike("ctrl.gate", 15.200, 0.84),
        spike("ae.mist.pack", 22.400, 1.42),
        spike("ae.mist.pack", 23.600, 0.91),
        spike("enc.fan.ctx", 29.800, 0.41),
        spike("dp.gas.kpa", 36.200, 0.58),
    ]
    ras = raster_core(
        40,
        84,
        26,
        87,
        routing(
            "thalamic-relay.dp-fan",
            "spikenaut.policy.fan-clamp",
            [
                ("relay.dp.gas", "policy.fan_clamp", 0.64),
                ("relay.ph.recycle", "policy.slurry_hold", 0.29),
                ("relay.ae.mist", "policy.fan_clamp", -0.46),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at DP win (4.620 ms) opens a 50 ms eligibility "
            "trace that still covers the 22.400 ms mist-eliminator pack collapse",
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
                    pop("fan_clamp", 48, 0.50, 220.0, 4),
                    pop("slurry_hold", 48, 0.50, 50.0, 1),
                    pop("dp_cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r48-257",
        "Limestone-Linn absorber / A-2: gas DP beats recycle pH by 230 us; correct "
        "MODIFY still eats an in-window mist-eliminator pack collapse (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "40 ms raster. total -0.44 = 0.34 + -0.62 + -0.16 + 0.04 + -0.04. Named "
        "isolate+pack-pull loss is not netted into task_progress.",
        ras,
        gate,
        "wet-FGD-absorber",
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
        "16 min gap.",
        2,
    )
