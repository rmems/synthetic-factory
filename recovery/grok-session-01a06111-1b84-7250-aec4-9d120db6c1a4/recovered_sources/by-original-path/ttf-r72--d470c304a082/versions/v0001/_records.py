def lif_377_excerpt():
    """Independent CUBA LIF (seed 72377). Plant remains designed."""

    n = 84
    dt_us = 100
    tau_m_ms = 20.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.92
    i_stim_peak = 2.45
    stim = (21000, 25000)
    seed = 72377
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
    kick = [(t, nid) for t, nid in picked if t >= 21000][:9]
    picked = sorted(clamp + kick, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise RuntimeError(f"LIF excerpt too short: {len(picked)}")
    channels = ["lif.clamp" if t < 21000 else "lif.hoop" for t, _ in picked]
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
            ("seed", 72377),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.68 steam-carbon-clamp bias; stim 21-25 ms is the "
                "reformer-tube hoop-strain kick.",
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


def record_376():
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
        spike("rtd.bed.c", 2.410, 0.61),
        spike("namur.failsafe.ma", 3.880, 0.52),
        spike("bus.waelz.ctx", 4.620, 0.47),
        spike("rtd.bed.c", 5.280, 1.31),
        spike("namur.failsafe.ma", 5.510, 1.18),
        spike("ctrl.gate", 6.000, 0.99),
        spike("rtd.bed.c", 7.220, 0.84),
        spike("namur.failsafe.ma", 9.440, 0.66),
        spike("ctrl.gate", 14.880, 0.88),
        spike("enc.feed.ctx", 18.400, 0.41),
        spike("rtd.bed.c", 24.200, 0.58),
    ]
    excerpt = independent_excerpt(72376, 80, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Waelz kiln WK-4 at Gahnite-Wyke already holds a live bed analog of 1084 C when that "
                "analog sample races a NAMUR NE43 fail-safe that still prints 21.5 mA. Published trip "
                "is 1140 C on the analog; a weak supervisor scales the diagnostic current as 4-20 mA "
                "EU and zeros a legal 18.0 t/h residue feed.",
            ),
            ("domain", "waelz-kiln"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 18.0 t/h residue on WK-4, keep live bed T < 1140 C, and finish the "
                "13 min zinc-fume quality window.",
            ),
            ("t0_us", 1762300000000376),
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
                                "rtd.bed.c 1084 C live analog",
                                "namur.failsafe.ma 21.5 mA diagnostic shadow",
                            ],
                        ),
                        (
                            "semantics",
                            "Analog-first should ACCEPT 18.0 t/h (1084 C < 1140 C trip). "
                            "Fail-safe-first would only delay confirmation of the same legal analog.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one kiln-bed RTD slot versus the NAMUR diagnostic publisher "
                            "on this 2 kHz Waelz bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 76 us (bed 34 + namur 42): 3.0x over "
                            "a 2.0x trust floor. Order is correctly analog-first. The error is binding "
                            "21.5 mA fail-safe as if it were 4-20 mA EU, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "kiln-bed RTD, 2 kHz, 34 us jitter, axis bed_C",
                    "NAMUR NE43 diagnostic current, 1 kHz, 42 us jitter, namur_failsafe_high true",
                    "residue-mass encoder (context)",
                    "offgas ZnO IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("live_C", 1084.0),
                        ("trip_C", 1140.0),
                        ("live_mA", 11.573),
                        ("diag_mA", 21.5),
                        ("eu_from_diag_C", 1456.25),
                        ("span_lo_C", 800.0),
                        ("span_hi_C", 1400.0),
                        ("namur_failsafe_high", True),
                        ("analog_fresh", True),
                        ("heartbeat_age_ms", 18),
                        ("proposed_t_h", 18.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Waelz WK-4 indexed on Gahnite-Wyke; live bed 1084 C, 18.0 t/h armed.",
                    "2. Published analog trip 1140 C; NAMUR tag 21.5 mA would scale to 1456.25 C if treated as 4-20.",
                    "3. Encoder precursor at 1.205 ms.",
                    "4. Race window [5.280, 5.680] ms.",
                    "5. Bed analog 1084 C at 5.280 ms (winner).",
                    "6. NAMUR fail-safe 21.5 mA at 5.510 ms (loser by 230 us).",
                    "7. Gate at 6.000 ms: wrong REJECT holds 0 t/h on the diagnostic-as-EU bind.",
                    "8. Kiln idle; analog never crossed 1140 C.",
                    "9. 13 min zinc-fume quality window missed.",
                    "10. QA: correct gate was ACCEPT; leave 18.0 t/h; bind analog 1084 vs 1140 C.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "waelz_18_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 18.0),
                        ("live_C", 1084.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 1084.0),
                        ("trip_C", 1140.0),
                        ("live_mA", 11.573),
                        ("diag_mA", 21.5),
                        ("eu_from_diag_C", 1456.25),
                        ("namur_failsafe_high", True),
                        ("analog_fresh", True),
                        ("heartbeat_age_ms", 18),
                        ("ft_axis", "bed_C"),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 76),
                        ("t_gate_us", 6000),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.0 t/h because live analog 1084 C is 56 C under the "
                "published 1140 C trip and the 21.5 mA reading is a NAMUR fail-safe, not 4-20 EU.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "NAMUR 21.5 mA treated as 4-20 EU is 1456 C, over the 1140 C trip (true vs that "
                "wrong scale). REJECT: hold 0 t/h until the diagnostic tag recovers under 20 mA so "
                "the kiln does not see an over-temperature event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("published_analog_trip", 1140.0),
                                    ("observed_analog", 1084.0),
                                    ("namur_applied_as_eu", 1456.25),
                                    ("namur_failsafe_high", True),
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
            ("name", "waelz_hold_namur_as_eu"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 0.0),
                        ("live_C", 1084.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): feed 18.0 -> 0 t/h. Routing relay.namur.failsafe -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Analog 1084 C never "
                "violated the 1140 C trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze WK-4 at 0 t/h while live analog stayed 1084 C under the "
                "1140 C trip. 13 min zinc-fume window missed. Correct gate was ACCEPT of the "
                "already-legal 18.0 t/h command.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("kiln", "held at 0 t/h; 18.0 t/h abandoned"),
                        ("live_C", "still 1084 C, under 1140 published trip"),
                        ("fume", "13 min quality window missed"),
                        ("vote", "no over-temperature; namur-failsafe-as-EU false positive"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 21.5 mA reading is NAMUR NE43 fail-safe high, not a 4-20 mA process measurement.",
                    "Delayed (13 min): sister kiln WK-5 ran the same 18.0 t/h fume window after QA rebound the analog trip; WK-4's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: analog 1084 C < published 1140 C trip; leave 18.0 t/h.",
                        ),
                        ("correct_trip_C", 1140.0),
                        ("wrong_diag_mA", 21.5),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("feed_t_h", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "13 min missed zinc-fume window (task/efficiency); analog never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.c (5.280 ms, 1084 C)"),
                        ("loser", "namur.failsafe.ma (5.510 ms, 21.5 mA)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "Fail-safe-first by < 230 us would still show analog 1084 < 1140 C. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the analog win "
                            "on a namur-failsafe-as-EU bind.",
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
            "relay.namur.failsafe",
            "policy.hold_reject",
            [
                ("relay.namur.failsafe", "policy.hold_reject", 0.71),
                ("relay.rtd.bed", "policy.hold_reject", 0.22),
            ],
            "acetylcholine",
            0.08,
            "namur_failsafe_as_eu_stdp; ACh tags the (wrong) hold_reject bind at the analog win",
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
                    pop("bed_trip_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r72-376",
        "WRONG-REJECT at Gahnite-Wyke / WK-4: live analog 1084 C is legal vs "
        "published 1140 C trip; supervisor bound NAMUR 21.5 mA fail-safe as 4-20 EU",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 1084 < 1140 is true; clamp bound to a "
        "NAMUR fail-safe 21.5 mA scaled as EU. total -0.36 = -0.18 + 0.06 + -0.22 + -0.08 + 0.06.",
        ras,
        gate,
        "waelz-kiln",
        [
            "reject",
            "wrong-gate",
            "namur-failsafe-as-eu",
            "diagnostic-mA-as-PV",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct analog<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed.",
        1,
        supervisor_error_type="wrong-reject",
    )


def record_377():
    excerpt, extra = lif_377_excerpt()
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
                "Autothermal reformer ATR-7 at Syngas-Clough is already pulling 2.40 steam/carbon when a "
                "burner-outlet pulse arrives 230 us before the methane-slip probe that still reads a "
                "legal recipe. Temperature-first latches a process clamp under the 1000 C cap; "
                "slip-first would keep cruise steam. Stored hoop strain in a reformer tube is not "
                "yet an observable of either race channel.",
            ),
            ("domain", "autothermal-reformer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep ATR-7 on 2.40 steam/carbon only while burner-outlet stays <= 1000 C, and "
                "leave the reformer tubes un-kicked.",
            ),
            ("t0_us", 1762300000000377),
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
                                "jt.burner.c 1048 C burner outlet",
                                "ch4.slip.pct 0.62 still-legal methane slip",
                            ],
                        ),
                        (
                            "semantics",
                            "Temperature-first latches steam/carbon clamp 2.40 -> 2.90; slip-first keeps "
                            "cruise steam on a 'recipe still open' model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one burner-outlet RTD slot minus methane-GC group delay on this "
                            "1 kHz ATR bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 68 us (burner 30 + slip 38): 3.4x over "
                            "a 2.0x trust floor. Reversing order by < 230 us inside the 380 us window "
                            "would have kept 2.40 steam/carbon cruise; predicted next-sample burner 1022 C > 1000 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "burner-outlet RTD, 1 kHz, 30 us timestamp jitter",
                    "methane-slip GC, 1 kHz, 38 us jitter",
                    "steam encoder (context)",
                    "tube AE (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("burner_cap_C", 1000.0),
                        ("observed_burner_C", 1048.0),
                        ("proposed_sc", 2.40),
                        ("sc_floor", 2.10),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. ATR-7 indexed; 2.40 steam/carbon; burner 1048 C > 1000 cap.",
                    "2. Cruise steam 2.40 armed; burner over the 1000 C cap.",
                    "3. Encoder precursor at 1.848 ms; burner warm-start 1048 C.",
                    "4. Race window [4.620, 5.000] ms opens on the ATR bus.",
                    "5. Burner 1048 C at 4.620 ms (winner).",
                    "6. Methane slip 0.62 at 4.850 ms (loser by 230 us).",
                    "7. Gate at 5.500 ms (winner + 880 us): MODIFY clamp 2.40 -> 2.90.",
                    "8. Clamp executes; next-sample burner 978 C < 1000 cap.",
                    "9. At 22.400 ms stored hoop strain kicks a reformer tube.",
                    "10. Emergency isolate 16 min + tube pull; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_steam"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_carbon", 2.40),
                        ("burner_C", 1048.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("burner_C", 1048.0),
                        ("burner_cap_C", 1000.0),
                        ("predicted_unclamped_next_C", 1022.0),
                        ("steam_carbon", 2.40),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 68),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.40 steam/carbon cruise: methane slip looks like an open recipe, not a "
                "hooped tube, and the 1000 C burner cap is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Burner 1048 C won by 230 us, so the reformer is running packed, not still "
                "free. Holding 2.40 steam/carbon predicts next-sample 1022 C > 1000 C cap. MODIFY: steam/carbon "
                "2.40 -> 2.90. Observed after clamp 978 C < 1000. A full REJECT is not "
                "indicated: a sound ATR accepts 2.90 steam/carbon.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "burner_C",
                            OrderedDict(
                                [
                                    ("cap", 1000.0),
                                    ("observed", 1048.0),
                                    ("predicted_unclamped_next", 1022.0),
                                    ("clamped_steam_carbon", 2.90),
                                    ("observed_after_clamp", 978.0),
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
            ("name", "clamped_steam"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("steam_carbon", 2.90),
                        ("burner_C", 978.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: steam/carbon 2.40 -> 2.90. Process-correct vs the 1000 C burner cap. Reformer-tube "
                "hoop kick still occurs at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held burner at 978 C. At 22.400 ms stored hoop strain kicked "
                "a reformer tube. Clamp raised steam; it did not dump the hoop charge. "
                "Partnered negative: process heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("steam", "clamp executed; burner 978 C < 1000"),
                        ("tube", "hoop kick at 22.400 ms"),
                        ("repair", "16 min emergency isolate + tube pull"),
                        ("mission", "ATR still reforming; hoop precursor controlled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither burner RTD nor methane GC predicted the hoop charge; ae.tube.hoop is a new channel at 22.400 ms, 16.900 ms after the gate, still inside the 40 ms raster.",
                    "Delayed (16 min): emergency isolate and tube pull close the kick. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "16 min emergency isolate + tube pull after a reformer-tube hoop kick. Safety "
                "head -0.62 prices the precursor; task_progress stays +0.34 because the steam clamp "
                "completed under the 1000 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "jt.burner.c (4.620 ms, 1048 C)"),
                        ("loser", "ch4.slip.pct (4.850 ms, 0.62)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "Slip-first by < 230 us inside the 380 us window would have kept "
                            "2.40 steam/carbon cruise; predicted next-sample 1022 C would have exceeded the "
                            "1000 C cap even without the hoop charge. The MODIFY is still the "
                            "correct process. The kick is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms reformer-tube hoop kick (tick t_us=22400), inside the "
                "40 ms raster. The correct MODIFY at 5.500 ms is in the same excerpt. Do not put "
                "inflection on the +16 min isolate tick.",
            ),
            ("delayed_surprise_s", 960.0),
            ("abort_s", 960),
        ]
    )
    spikes = [
        spike("enc.steam.ctx", 1.120, 0.43),
        spike("jt.burner.c", 2.240, 0.62),
        spike("ch4.slip.pct", 3.180, 0.55),
        spike("jt.burner.c", 4.620, 1.34),
        spike("ch4.slip.pct", 4.850, 1.12),
        spike("ctrl.gate", 5.500, 0.97),
        spike("jt.burner.c", 7.200, 0.81),
        spike("ch4.slip.pct", 10.400, 0.66),
        spike("ctrl.gate", 15.200, 0.84),
        spike("ae.tube.hoop", 22.400, 1.42),
        spike("ae.tube.hoop", 23.600, 0.91),
        spike("enc.steam.ctx", 29.800, 0.41),
        spike("jt.burner.c", 36.200, 0.58),
    ]
    ras = raster_core(
        40,
        84,
        26,
        87,
        routing(
            "thalamic-relay.burner-steam",
            "spikenaut.policy.steam-clamp",
            [
                ("relay.jt.burner", "policy.steam_clamp", 0.64),
                ("relay.ch4.slip", "policy.recipe_hold", 0.29),
                ("relay.ae.tube", "policy.steam_clamp", -0.46),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at burner win (4.620 ms) opens a 50 ms eligibility "
            "trace that still covers the 22.400 ms reformer-tube hoop kick",
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
                    pop("steam_clamp", 48, 0.50, 220.0, 4),
                    pop("recipe_hold", 48, 0.50, 50.0, 1),
                    pop("burner_cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r72-377",
        "Syngas-Clough ATR / ATR-7: burner RTD beats methane-slip GC by 230 us; correct "
        "MODIFY still eats an in-window reformer-tube hoop kick (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "40 ms raster. total -0.44 = 0.34 + -0.62 + -0.16 + 0.04 + -0.04. Named "
        "isolate+tube-pull loss is not netted into task_progress.",
        ras,
        gate,
        "autothermal-reformer",
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


def record_378():
    ticks = [
        tick(1568, 0.01, 0.04, 0.02, 0.01, 0.01),
        tick(3920, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(4110, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5100, 0.03, 0.12, 0.04, 0.04, 0.02),
        tick(5380, 0.02, 0.07, 0.01, 0.01, 0.01),
        tick(540000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.air.ctx", 1.040, 0.44),
        spike("ae.mouth.pps", 2.180, 0.71),
        spike("enc.tuyere.nm3h", 3.020, 0.52),
        spike("ae.mouth.pps", 3.920, 1.36),
        spike("enc.tuyere.nm3h", 4.110, 1.14),
        spike("ctrl.gate", 5.100, 0.98),
        spike("ae.mouth.pps", 7.400, 0.82),
        spike("enc.tuyere.nm3h", 10.800, 0.61),
        spike("ctrl.gate", 16.200, 0.86),
        spike("ae.mouth.pps", 24.600, 0.70),
        spike("enc.tuyere.nm3h", 33.400, 0.48),
        spike("bus.ps.ctx", 41.200, 0.40),
    ]
    excerpt = independent_excerpt(72378, 112, 46000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Peirce-Smith converter PS-2 on the Chalcocite-Dene HIL pad is blowing 8400 Nm3/h "
                "tuyere air when an AE burst at 52 pps on the mouth races the air encoder that still "
                "looks in-band for a blast step. Ramp is legal only if AE <= 40 pps. AE-first latches "
                "hold; encoder-first would treat in-band flow as mouth clearance.",
            ),
            ("domain", "peirce-smith-converter"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not ramp PS-2 unless AE <= 40 pps; keep blast 0 Nm3/h until the "
                "mouth is quiet.",
            ),
            ("t0_us", 1762300000000378),
            ("gate_latency_us", 1180),
            ("race_window_us", 280),
            ("race_window_rel_ms", [3.920, 4.200]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.mouth.pps 52 pps mouth splash",
                                "enc.tuyere.nm3h 8400 Nm3/h still-in-band",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches REJECT hold 0 Nm3/h; encoder-first would keep 8400 Nm3/h "
                            "on an in-band-flow-as-clearance model.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one AE envelope slot versus the tuyere-encoder publisher on this "
                            "pad cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 190 us vs combined jitter 54 us (AE 24 + encoder 30): 3.5x over a "
                            "2.0x trust floor. Pad injects encoder 90-130 us before the AE envelope "
                            "finishes (hydrophone lag, not a sensor fault); the encoder packet is still "
                            "the loser in this 280 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "mouth AE, 24 us jitter, 40 pps trip",
                    "tuyere-air encoder, 30 us jitter",
                    "bath thermocouple (context)",
                    "offgas SO2 (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_trip_pps", 40.0),
                        ("observed_ae_pps", 52.0),
                        ("blast_cap_nm3h", 9200.0),
                        ("proposed_nm3h", 8400.0),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("bench", "Chalcocite-Dene CD-HIL Peirce-Smith pad, PS-2"),
                        ("inject", "AE envelope delayed 90-130 us vs encoder; hydrophone lag, not a false AE"),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. PS-2 on Chalcocite-Dene HIL pad; converter in band; blast armed at 8400 Nm3/h.",
                    "2. AE trip 40 pps; observed 52 pps burst on mouth.",
                    "3. Encoder precursor at 1.040 ms.",
                    "4. Race window [3.920, 4.200] ms.",
                    "5. AE 52 pps at 3.920 ms (winner).",
                    "6. Tuyere encoder 8400 Nm3/h at 4.110 ms (loser by 190 us).",
                    "7. Gate at 5.100 ms: REJECT hold 0 Nm3/h, do not blow.",
                    "8. Pad recycle 9 min; AE decays under 40 pps after hold.",
                    "9. Converter never splashed into a hood fire; encoder-as-clearance would have blown into the burst.",
                    "10. QA: correct gate was REJECT; leave 0 Nm3/h until AE <= 40 pps.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "blast_8400"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("blast_nm3h", 8400.0),
                        ("ae_pps", 52.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 52.0),
                        ("ae_trip_pps", 40.0),
                        ("blast_nm3h", 8400.0),
                        ("blast_cap_nm3h", 9200.0),
                        ("race_margin_us", 190),
                        ("combined_jitter_us", 54),
                        ("t_gate_us", 5100),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 8400 Nm3/h because blast is under the 9200 Nm3/h cap and treats "
                "the tuyere encoder as mouth clearance, ignoring the 52 pps AE burst.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "AE 52 pps won by 190 us and is over the 40 pps trip. Encoder 8400 Nm3/h is under "
                "a blast cap but is not clearance. REJECT: hold 0 Nm3/h until AE <= 40 pps.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "mouth_ae_pps",
                            OrderedDict(
                                [
                                    ("trip", 40.0),
                                    ("observed", 52.0),
                                    ("executed_nm3h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 190),
                                    ("combined_jitter_us", 54),
                                    ("ratio", 3.52),
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
            ("name", "ps_hold_ae"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("blast_nm3h", 0.0),
                        ("ae_pps", 52.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: blast 8400 -> 0 Nm3/h. Routing relay.ae.mouth -> policy.hold_reject. "
                "Do not blow into the 52 pps mouth splash.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held PS-2 at 0 Nm3/h while AE 52 pps decayed. Encoder-as-clearance "
                "would have blown 8400 Nm3/h into the splash. Pad recycle 9 min.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("converter", "held at 0 Nm3/h"),
                        ("mouth", "AE burst decaying under trip after hold"),
                        ("tuyeres", "still charged, not blowing"),
                        ("pad", "9 min recycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Pad injects encoder 90-130 us before AE envelope finish; that is hydrophone lag, not a false AE.",
                    "Delayed (9 min): pad recycle restacks the mouth after AE < 40 pps.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.mouth.pps (3.920 ms, 52 pps)"),
                        ("loser", "enc.tuyere.nm3h (4.110 ms, 8400 Nm3/h)"),
                        ("margin_us", 190),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 190 us would have treated 8400 Nm3/h as clearance and "
                            "blown into the 52 pps splash. The REJECT is still required; reversal "
                            "only delays the AE bind.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5100),
            (
                "reward_inflection_note",
                "Safety credit lands at the correct REJECT (5.100 ms, tick 4). Pad recycle is delayed surprise.",
            ),
            ("delayed_surprise_s", 540.0),
            ("pad_recycle_s", 540),
        ]
    )
    ras = raster_core(
        46,
        112,
        20,
        103,
        routing(
            "relay.ae.mouth",
            "policy.hold_reject",
            [
                ("relay.ae.mouth", "policy.hold_reject", 0.74),
                ("relay.enc.tuyere", "policy.blast_go", 0.18),
            ],
            "dopamine",
            0.06,
            "ae_trip_stdp; DA tags the hold_reject bind at the AE win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.28),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 64, 0.50, 180.0, 3),
                    pop("blast_go", 64, 0.80, 8.0, 0),
                    pop("ae_trip_veto", 32, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r72-378",
        "Chalcocite-Dene Peirce-Smith HIL / PS-2: AE 52 pps beats tuyere encoder 8400 Nm3/h by 190 us; "
        "correct REJECT holds the mouth",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 52 > 40 trip beats in-band tuyere flow. total +0.78 = "
        "0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "peirce-smith-converter",
        [
            "reject",
            "hil-pad",
            "ae-vs-encoder",
            "mouth-splash-hold",
            "sidecar-convictable",
            "hil",
        ],
        "Teaches a probe that an in-band tuyere encoder is not mouth clearance when "
        "AE is over trip and routing.table[0].to is policy.hold_reject.",
        3,
    )


def record_379():
    ticks = [
        tick(2496, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(6240, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(6470, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(7140, 0.12, 0.08, 0.05, 0.03, 0.02),
        tick(7500, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(600000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    params = OrderedDict(
        [
            ("whsv_h", 0.38),
            ("bed_C", 582.0),
            ("reactor_id", 12),
            ("hold", False),
        ]
    )
    spikes = [
        spike("ft.feed.ctx", 1.480, 0.42),
        spike("rtd.bed.c", 3.120, 0.58),
        spike("ir.coke.smear", 4.660, 0.50),
        spike("rtd.bed.c", 6.240, 1.28),
        spike("ir.coke.smear", 6.470, 1.10),
        spike("ctrl.gate", 7.140, 0.96),
        spike("rtd.bed.c", 9.200, 0.74),
        spike("ir.coke.smear", 12.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("rtd.bed.c", 24.600, 0.55),
        spike("ft.feed.ctx", 29.800, 0.40),
    ]
    excerpt = independent_excerpt(72379, 56, 30000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Catofin reactor R-12 of the Propene-Thorp propane-dehydrogenation train is feeding "
                "0.38 h-1 WHSV when a bed RTD at 582 C races a quench-flare smear that still claims "
                "over-coke. Commanded 0.38 h-1 and 582 C sit 0.08 h-1 and 38 C inside the legal "
                "envelopes. The RTD win only ratifies the WHSV already in the bed.",
            ),
            ("domain", "propane-dehydrogenation"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the Catofin pass on Propene-Thorp, keep bed RTD <= 620 C and "
                "WHSV >= 0.30 h-1, and leave coke in spec.",
            ),
            ("t0_us", 1762300000000379),
            ("gate_latency_us", 900),
            ("race_window_us", 360),
            ("race_window_rel_ms", [6.240, 6.600]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bed.c 582 C catalyst bed",
                                "ir.coke.smear over-coke claim",
                            ],
                        ),
                        (
                            "semantics",
                            "RTD-first confirms the already-legal 0.38 h-1 / 582 C pass; "
                            "smear-first would have treated the RTD as a smear echo and looked "
                            "for an extra hold the bed does not need.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one Catofin-bed RTD kernel step versus the coke-probe publisher "
                            "on this rigid dehydrogenation train.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 230 us vs combined jitter 70 us (RTD 32 + coke 38): 3.3x over "
                            "a 2.0x trust floor. Reversing order by < 230 us would not make the "
                            "proposed pass illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed RTD, 32 us jitter",
                    "coke IR smear, 38 us jitter",
                    "feed-mass encoder (context)",
                    "H2/HC analyzer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 620.0),
                        ("observed_bed_C", 582.0),
                        ("whsv_floor_h", 0.30),
                        ("proposed_whsv_h", 0.38),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "Catofin 1-D bed + coke-make kernel, seed 72; 12 axial nodes; NOT lumped CSTR, NOT a fluid-LES field",
                        ),
                        (
                            "fidelity_limits",
                            "No radial maldistribution or steam-diluent leak; beds are rigid temperature sources. Raster is kernelized events, not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Propene-Thorp Catofin indexed; R-12 feeding 0.38 h-1 at 582 C bed.",
                    "2. Caps: bed 620 C, WHSV floor 0.30 h-1; both proposed values inside.",
                    "3. Feed precursor at 1.480 ms.",
                    "4. Race window [6.240, 6.600] ms.",
                    "5. Bed RTD 582 C at 6.240 ms (winner).",
                    "6. Coke IR smear at 6.470 ms (loser by 230 us).",
                    "7. Gate at 7.140 ms: ACCEPT 0.38 h-1 / 582 C already legal.",
                    "8. Pass continues; no extra hold.",
                    "9. 10 min survey confirms coke still in spec.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "whsv_0p38_thold"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 582.0),
                        ("bed_cap_C", 620.0),
                        ("whsv_h", 0.38),
                        ("whsv_floor_h", 0.30),
                        ("race_margin_us", 230),
                        ("combined_jitter_us", 70),
                        ("t_gate_us", 7140),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 0.38 h-1 because bed 582 C is 38 C under the 620 C cap "
                "and WHSV is 0.08 h-1 over the 0.30 h-1 floor.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 582 C won by 230 us and is under 620 C. WHSV 0.38 h-1 is over "
                "0.30 h-1. ACCEPT the already-legal pass; coke IR smear is not a cap violation.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 620.0),
                                    ("observed", 582.0),
                                    ("executed_whsv_h", 0.38),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 230),
                                    ("combined_jitter_us", 70),
                                    ("ratio", 3.29),
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
            ("name", "whsv_0p38_thold"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: WHSV 0.38 h-1 and bed 582 C unchanged. Routing relay.rtd.bed "
                "-> policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left Catofin R-12 at 0.38 h-1 / 582 C. Coke IR smear did not justify a "
                "hold. 10 min survey confirmed coke in spec.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("reactor", "still 0.38 h-1 / 582 C"),
                        ("coke", "in spec after survey"),
                        ("train", "Catofin continues"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Coke IR smear is a quench-flare optical claim, not a bed-temperature violation.",
                    "Delayed (10 min): survey restacks R-12 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.c (6.240 ms, 582 C)"),
                        ("loser", "ir.coke.smear (6.470 ms, over-coke claim)"),
                        ("margin_us", 230),
                        (
                            "counterfactual_if_reversed",
                            "Smear-first by < 230 us would only delay confirmation. The pass stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7140),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (7.140 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 600.0),
            ("survey_s", 600),
        ]
    )
    ras = raster_core(
        30,
        56,
        38,
        64,
        routing(
            "relay.rtd.bed",
            "policy.go_accept",
            [
                ("relay.rtd.bed", "policy.go_accept", 0.68),
                ("relay.ir.coke", "policy.smear_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_whsv_stdp; 5-HT tags the go_accept bind at the bed-RTD win",
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
                    pop("smear_hold", 40, 0.80, 10.0, 0),
                    pop("bed_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r72-379",
        "Propene-Thorp Catofin / R-12: bed RTD 582 C beats coke IR smear by 230 us; ACCEPT "
        "already-legal 0.38 h-1 pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal Catofin pass. total +1.06 = "
        "0.42 + 0.28 + 0.18 + 0.10 + 0.08.",
        ras,
        gate,
        "propane-dehydrogenation",
        [
            "accept",
            "already-legal",
            "simulated-catofin",
            "rtd-vs-coke",
            "sidecar-convictable",
            "simulated",
        ],
        "Teaches that a bed RTD under cap can confirm an already-legal WHSV without "
        "a coke smear becoming a hold.",
        4,
    )


def record_380():
    ticks = [
        tick(1672, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(4180, 0.10, 0.08, 0.04, 0.02, 0.02),
        tick(4360, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(4940, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5240, 0.06, 0.05, 0.02, 0.01, 0.01),
        tick(420000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    params = OrderedDict(
        [
            ("current_kA", 42.0),
            ("bath_C", 1480.0),
            ("hearth_id", 3),
            ("hold", False),
        ]
    )
    spikes = [
        spike("enc.gap.ctx", 0.920, 0.41),
        spike("rtd.bath.c", 2.140, 0.60),
        spike("ir.roof.glint", 3.080, 0.51),
        spike("rtd.bath.c", 4.180, 1.30),
        spike("ir.roof.glint", 4.360, 1.12),
        spike("ctrl.gate", 4.940, 0.97),
        spike("rtd.bath.c", 6.800, 0.78),
        spike("ir.roof.glint", 9.200, 0.62),
        spike("ctrl.gate", 13.600, 0.85),
        spike("rtd.bath.c", 18.400, 0.54),
        spike("ir.roof.glint", 21.200, 0.43),
    ]
    excerpt = independent_excerpt(72380, 48, 24000, 11, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "SAF hearth H-3 at Rhodonite-Hurst is armed for a 42 kA pass when a bath dip at "
                "1480 C races a roof IR that still claims a roof-glint trip. Commanded 42 kA and "
                "1480 C sit 6 kA over the 36 kA floor and 60 C under the 1540 C cap. The "
                "dip win only ratifies the current already on the electrodes.",
            ),
            ("domain", "silicomanganese-furnace"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run hearth H-3 at 42 kA, keep bath dip <= 1540 C and roof IR glint from becoming "
                "a hold, and leave the furnace on schedule.",
            ),
            ("t0_us", 1762300000000380),
            ("gate_latency_us", 760),
            ("race_window_us", 300),
            ("race_window_rel_ms", [4.180, 4.480]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bath.c 1480 C SiMn bath",
                                "ir.roof.glint 8 kPa-equivalent hitch claim",
                            ],
                        ),
                        (
                            "semantics",
                            "Bath-first confirms the already-legal 42 kA / 1480 C pass; glint-first "
                            "would have treated the dip as a hitch echo and looked for an extra hold "
                            "the furnace does not need.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one bath-dip RTD slot versus the roof-IR publisher on this "
                            "SAF bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (dip 28 + IR 30): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed pass illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bath dip RTD, 28 us jitter",
                    "roof IR, 30 us jitter",
                    "electrode current encoder (context)",
                    "offgas CO (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bath_cap_C", 1540.0),
                        ("observed_bath_C", 1480.0),
                        ("current_floor_kA", 36.0),
                        ("proposed_kA", 42.0),
                        ("glint_claim", True),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Hearth H-3 indexed on Rhodonite-Hurst SAF; current armed 42 kA pass.",
                    "2. Caps: bath 1540 C, current floor 36 kA.",
                    "3. Encoder precursor at 0.920 ms.",
                    "4. Race window [4.180, 4.480] ms.",
                    "5. Bath dip 1480 C at 4.180 ms (winner).",
                    "6. Roof IR glint at 4.360 ms (loser by 180 us).",
                    "7. Gate at 4.940 ms: ACCEPT 42 kA / 1480 C already legal.",
                    "8. Pass continues; no extra hold.",
                    "9. 7 min survey confirms bath still under 1540 C.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "pass_42kA"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bath_C", 1480.0),
                        ("bath_cap_C", 1540.0),
                        ("current_kA", 42.0),
                        ("current_floor_kA", 36.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("t_gate_us", 4940),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 42 kA pass because bath 1480 C is 60 C under the 1540 C "
                "cap and current is 6 kA over the 36 kA floor.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bath 1480 C won by 180 us and is under 1540 C. Current 42 kA is over "
                "the 36 kA floor. ACCEPT the already-legal pass; roof-IR glint is not a cap violation.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bath_C",
                            OrderedDict(
                                [
                                    ("cap", 1540.0),
                                    ("observed", 1480.0),
                                    ("executed_kA", 42.0),
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
            ("name", "pass_42kA"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 42 kA pass and 1480 C bath unchanged. Routing relay.rtd.bath -> "
                "policy.go_accept.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left hearth H-3 on a 42 kA / 1480 C pass. Roof-IR glint did not "
                "justify a hold. 7 min survey confirmed bath still under 1540 C.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("hearth", "still 42 kA / 1480 C"),
                        ("glint", "residual, not a trip"),
                        ("furnace", "on schedule"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Roof IR glint is residual slag splash, not a bath over-temperature.",
                    "Delayed (7 min): survey restacks H-3 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bath.c (4.180 ms, 1480 C)"),
                        ("loser", "ir.roof.glint (4.360 ms, hitch claim)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 180 us would only delay confirmation. The pass stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4940),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (4.940 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 420.0),
            ("survey_s", 420),
        ]
    )
    ras = raster_core(
        24,
        48,
        42,
        48,
        routing(
            "relay.rtd.bath",
            "policy.go_accept",
            [
                ("relay.rtd.bath", "policy.go_accept", 0.66),
                ("relay.ir.roof", "policy.glint_hold", 0.20),
            ],
            "dopamine",
            0.04,
            "legal_pass_stdp; DA tags the go_accept bind at the bath-dip win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.30),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("go_accept", 40, 0.50, 160.0, 2),
                    pop("glint_hold", 40, 0.80, 10.0, 0),
                    pop("bath_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r72-380",
        "Rhodonite-Hurst SAF / H-3: bath dip 1480 C beats roof IR glint by 180 us; "
        "ACCEPT already-legal 42 kA pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal SiMn SAF pass. total +1.14 = "
        "0.44 + 0.32 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "silicomanganese-furnace",
        [
            "accept",
            "already-legal",
            "bath-vs-roof-ir",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches that a bath dip under cap can confirm an already-legal current without "
        "a roof-IR glint becoming a hold.",
        5,
    )
