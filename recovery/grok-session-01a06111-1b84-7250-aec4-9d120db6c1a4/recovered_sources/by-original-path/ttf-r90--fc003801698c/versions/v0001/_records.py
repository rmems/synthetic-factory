def lif_467_excerpt():
    """Independent CUBA LIF (seed 90467). Plant remains designed."""

    n = 88
    dt_us = 100
    tau_m_ms = 19.8
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.48
    stim = (21800, 25800)
    seed = 90467
    window_us = 44000
    i_clamp_extra = 0.67
    clamp_n = 16
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
    early = [(t, nid) for t, nid in spikes if t < 21800]
    burst = [(t, nid) for t, nid in spikes if 21800 <= t < 25800]
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
            early_flag = pool[0][0] < 21800
            have = len([1 for t, _ in picked if (t < 21800) == early_flag])
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
    take(burst, 9, label_times=(23800, 24600, 25400))
    clamp = [(t, nid) for t, nid in picked if t < 21800][:7]
    tile = [(t, nid) for t, nid in picked if t >= 21800][:9]
    picked = sorted(clamp + tile, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise RuntimeError(f"LIF excerpt too short: {len(picked)}")
    channels = ["lif.clamp" if t < 21800 else "lif.xfer" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 88),
            ("dt_us", 100),
            ("tau_m_ms", 19.8),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.91),
            ("i_stim_peak", 2.48),
            ("stim_t_us", [21800, 25800]),
            ("i_clamp_extra", 0.67),
            ("clamp_n", 16),
            ("seed", 90467),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-15 carry +0.67 EO-clamp bias; stim 21.8-25.8 ms is the "
                "transfer-line freeze-plug rupture.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 1200),
            ("delayed_surprise_s", 1200),
        ]
    )
    return excerpt_items(picked, channels), extra


def record_466():
    ticks = [
        tick(1920, -0.02, 0.01, -0.02, -0.01, 0.01),
        tick(4800, -0.04, 0.01, -0.04, -0.02, 0.01),
        tick(5040, -0.03, 0.01, -0.03, -0.01, 0.01),
        tick(5600, -0.06, 0.02, -0.08, -0.03, 0.02),
        tick(6000, -0.02, 0.01, -0.03, -0.01, 0.01),
        tick(720000000, -0.01, 0.00, -0.02, 0.00, 0.00),
    ]
    spikes = [
        spike("enc.d4.ctx", 1.200, 0.44),
        spike("rtd.ktype.c", 2.400, 0.61),
        spike("tc.stype.eu", 3.680, 0.52),
        spike("bus.eq.ctx", 4.200, 0.47),
        spike("rtd.ktype.c", 4.800, 1.31),
        spike("tc.stype.eu", 5.040, 1.18),
        spike("ctrl.gate", 5.600, 0.99),
        spike("rtd.ktype.c", 7.200, 0.84),
        spike("tc.stype.eu", 9.480, 0.66),
        spike("ctrl.gate", 14.800, 0.88),
        spike("enc.d4.ctx", 18.400, 0.41),
        spike("rtd.ktype.c", 24.200, 0.58),
    ]
    excerpt = independent_excerpt(90466, 76, 28000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Cyclic D4 equilibrator EQ-4 at Silox-Frith already tracks a type-K kettle "
                "thermocouple of 86.0 C, cold-junction compensated at 24.0 C, when that millivolt "
                "sample races a leftover type-S linearization table still printing 118.4 C with a "
                "disconnected ice-point CJ offset. Published trip is 102.0 C on the live type-K; a "
                "weak supervisor binds the type-S EU as process T and zeros a legal 9.5 t/h D4 feed.",
            ),
            ("domain", "silicone-d4-equilibrator"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 9.5 t/h D4 on EQ-4, keep type-K kettle T < 102.0 C trip, and finish the "
                "12 min siloxane-viscosity window.",
            ),
            ("t0_us", 1762300000000466),
            ("gate_latency_us", 800),
            ("race_window_us", 400),
            ("race_window_rel_ms", [4.800, 5.200]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.ktype.c 86.0 C type-K + live CJC 24.0 C",
                                "tc.stype.eu 118.4 C leftover type-S table + ice-point CJ",
                            ],
                        ),
                        (
                            "semantics",
                            "Type-K-first should ACCEPT 9.5 t/h (86.0 C < 102.0 C trip). "
                            "Type-S-first would only delay confirmation of the same legal kettle.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one type-K analog slot versus the leftover type-S publisher "
                            "on this 2 kHz siloxane bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 240 us vs combined jitter 70 us (K 32 + S 38): 3.4x over "
                            "a 2.0x trust floor. Order is correctly type-K-first. The error is binding "
                            "the type-S table plus ice-point CJ as if it were the live process PV, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "type-K kettle TC, 2 kHz, 32 us jitter, live CJ RTD 24.0 C, axis eq4_proc_t, tc_type_swap false",
                    "leftover type-S linearization table, 1 kHz, 38 us jitter, ice-point CJ 0.0 C not process",
                    "D4-feed encoder (context)",
                    "KOH catalyst PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("live_C", 86.0),
                        ("trip_C", 102.0),
                        ("bound_C", 118.4),
                        ("tc_type_live", "K"),
                        ("tc_type_bound", "S"),
                        ("tc_type_swap", True),
                        ("cjc_live_C", 24.0),
                        ("cjc_bound_C", 0.0),
                        ("cjc_is_live", False),
                        ("cjc_offset_applied", True),
                        ("analog_fresh", True),
                        ("proposed_t_h", 9.5),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Equilibrator EQ-4 indexed on Silox-Frith; type-K 86.0 C, D4 9.5 t/h armed.",
                    "2. Published live trip 102.0 C; leftover type-S table tagged ice-point CJ, not process PV.",
                    "3. Encoder precursor at 1.200 ms.",
                    "4. Race window [4.800, 5.200] ms.",
                    "5. Type-K 86.0 C at 4.800 ms (winner).",
                    "6. Type-S leftover 118.4 C at 5.040 ms (loser by 240 us).",
                    "7. Gate at 5.600 ms: wrong REJECT holds 0 t/h on type-S-as-PV.",
                    "8. Feed idle; type-K never crossed 102.0 C.",
                    "9. 12 min siloxane-viscosity window missed.",
                    "10. QA: correct gate was ACCEPT; leave 9.5 t/h; bind type-K 86.0 vs 102.0 C trip.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "d4_9p5_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 9.5),
                        ("proc_C", 86.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 86.0),
                        ("trip_C", 102.0),
                        ("bound_C", 118.4),
                        ("tc_type_live", "K"),
                        ("tc_type_bound", "S"),
                        ("tc_type_swap", True),
                        ("cjc_live_C", 24.0),
                        ("cjc_bound_C", 0.0),
                        ("cjc_is_live", False),
                        ("cjc_offset_applied", True),
                        ("analog_fresh", True),
                        ("ft_axis", "eq4_proc_t"),
                        ("race_margin_us", 240),
                        ("combined_jitter_us", 70),
                        ("t_gate_us", 5600),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 9.5 t/h because type-K 86.0 C is 16.0 C under the "
                "published 102.0 C trip and type-S 118.4 C is a leftover table plus ice-point CJ, not process T.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Type-S EU prints 118.4 C, so the kettle is treated as 118.4 C over the 102.0 C "
                "trip (true vs that leftover type-S table plus ice-point CJ). REJECT: hold 0 t/h until "
                "the type-S EU falls so the equilibrator does not see an over-temp event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "eq4_proc_t",
                            OrderedDict(
                                [
                                    ("published_trip_C", 102.0),
                                    ("observed_type_k_C", 86.0),
                                    ("tc_type_swap_applied", True),
                                    ("cjc_offset_applied", True),
                                    ("bound_C", 118.4),
                                    ("executed_t_h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 240),
                                    ("combined_jitter_us", 70),
                                    ("ratio", 3.43),
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
            ("name", "d4_hold_stype"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_t_h", 0.0),
                        ("proc_C", 86.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): feed 9.5 -> 0 t/h. Routing relay.tc.stype -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Type-K 86.0 C never "
                "violated the 102.0 C trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze EQ-4 at 0 t/h while type-K stayed 86.0 C under the "
                "102.0 C trip. 12 min siloxane-viscosity window missed. Correct gate was ACCEPT of the "
                "already-legal 9.5 t/h command.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("equilibrator", "held at 0 t/h; 9.5 t/h abandoned"),
                        ("proc_C", "still 86.0 C, under 102.0 C published trip"),
                        ("siloxane", "12 min viscosity window missed"),
                        ("flag", "no over-temp; type-S-as-PV plus ice-point CJ false positive"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 118.4 C tag is a leftover type-S table with ice-point CJ 0.0 C, not a live type-K PV.",
                    "Delayed (12 min): sister kettle EQ-5 ran the same 9.5 t/h D4 window after QA rebound the type-K trip; EQ-4's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: type-K 86.0 C < published 102.0 C trip; leave 9.5 t/h; ignore type-S table and ice-point CJ.",
                        ),
                        ("correct_trip_C", 102.0),
                        ("wrong_flag", True),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("feed_t_h", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "12 min missed siloxane-viscosity window (task/efficiency); type-K never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.ktype.c (4.800 ms, 86.0 C)"),
                        ("loser", "tc.stype.eu (5.040 ms, leftover type-S 118.4 C)"),
                        ("margin_us", 240),
                        (
                            "counterfactual_if_reversed",
                            "Type-S-first by < 240 us would still show type-K 86.0 C < 102.0. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the type-K win "
                            "on leftover type-S plus ice-point CJ.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5600),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (5.600 ms, tick 4). The 12 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 720.0),
            ("missed_window_s", 720),
        ]
    )
    ras = raster_core(
        28,
        76,
        30,
        64,
        routing(
            "relay.tc.stype",
            "policy.hold_reject",
            [
                ("relay.tc.stype", "policy.hold_reject", 0.74),
                ("relay.rtd.ktype", "policy.hold_reject", 0.19),
            ],
            "acetylcholine",
            0.08,
            "tc_type_swap_stdp; ACh tags the (wrong) hold_reject bind at the type-K win",
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
                    pop("hold_reject", 48, 0.50, 210.0, 4),
                    pop("go_accept", 48, 0.80, 8.0, 0),
                    pop("temp_trip_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r90-466",
        "WRONG-REJECT at Silox-Frith / EQ-4: type-K 86.0 C is legal vs "
        "published 102.0 C trip; supervisor bound leftover type-S table plus ice-point CJ as the process PV",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 86.0 < 102.0 is true; clamp bound to leftover "
        "type-S plus ice-point CJ. total -0.36 = -0.18 + 0.06 + -0.22 + -0.08 + 0.06.",
        ras,
        gate,
        "silicone-d4-equilibrator",
        [
            "reject",
            "wrong-gate",
            "cold-junction-offset",
            "thermocouple-type-swap",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct type-K<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed.",
        1,
        supervisor_error_type="wrong-reject",
    )


def record_467():
    excerpt, extra = lif_467_excerpt()
    ticks = [
        tick(2040, 0.05, -0.02, -0.02, 0.01, 0.00),
        tick(5100, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(5340, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6000, 0.10, -0.06, -0.03, 0.02, -0.01),
        tick(23800, 0.05, -0.42, -0.04, 0.00, -0.02),
        tick(1200000000, 0.02, -0.05, -0.02, 0.00, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Alkoxylation kettle AK-2 at Alkox-Grove is already pulling 8.4 t/h ethylene oxide "
                "when a kettle-temperature pulse arrives 240 us before the EO-flow encoder that still "
                "reads a legal feed. Temperature-first latches a process clamp under the "
                "162 C cap; flow-first would keep cruise EO. Stored transfer-line freeze-plug load is "
                "not yet an observable of either race channel.",
            ),
            ("domain", "polyether-polyol-alkoxylator"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep AK-2 on 8.4 t/h EO only while kettle temperature stays <= 162 C, and "
                "leave the PO-rich transfer-line freeze plug un-ruptured.",
            ),
            ("t0_us", 1762300000000467),
            ("gate_latency_us", 900),
            ("race_window_us", 400),
            ("race_window_rel_ms", [5.100, 5.500]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.kettle.c 168 C alkoxylation kettle",
                                "ft.eo.t_h 8.4 t/h still-legal EO feed",
                            ],
                        ),
                        (
                            "semantics",
                            "Temperature-first latches EO clamp 8.4 -> 5.6 t/h; flow-first keeps "
                            "cruise EO on a 'transfer line still open' model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one kettle RTD slot minus EO-encoder group delay on this "
                            "1 kHz alkoxylation bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 240 us vs combined jitter 68 us (RTD 30 + flow 38): 3.5x over "
                            "a 2.0x trust floor. Reversing order by < 240 us inside the 400 us window "
                            "would have kept 8.4 t/h cruise; predicted next-sample kettle 164 C > 162 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "alkox kettle RTD, 1 kHz, 30 us timestamp jitter",
                    "EO-flow encoder, 1 kHz, 38 us jitter",
                    "starter-polyol encoder (context)",
                    "transfer-line AE (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("kettle_cap_C", 162.0),
                        ("observed_kettle_C", 168.0),
                        ("proposed_eo_t_h", 8.4),
                        ("eo_floor_t_h", 3.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Alkoxylation kettle AK-2 indexed; 8.4 t/h EO; kettle 168 C > 162 cap.",
                    "2. Cruise EO 8.4 t/h armed; kettle over the 162 C cap.",
                    "3. Encoder precursor at 1.180 ms; kettle-side warm-start 168 C.",
                    "4. Race window [5.100, 5.500] ms opens on the alkoxylation bus.",
                    "5. Kettle RTD 168 C at 5.100 ms (winner).",
                    "6. EO flow 8.4 t/h at 5.340 ms (loser by 240 us).",
                    "7. Gate at 6.000 ms (winner + 900 us): MODIFY clamp 8.4 -> 5.6 t/h.",
                    "8. Clamp executes; next-sample kettle 157 C < 162 cap.",
                    "9. At 23.800 ms stored freeze-plug load ruptures a PO-rich transfer line.",
                    "10. Emergency isolate 20 min + line pull; named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_eo_alkox"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("eo_t_h", 8.4),
                        ("kettle_C", 168.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("kettle_C", 168.0),
                        ("kettle_cap_C", 162.0),
                        ("predicted_unclamped_next_C", 164.0),
                        ("eo_t_h", 8.4),
                        ("race_margin_us", 240),
                        ("combined_jitter_us", 68),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 8.4 t/h cruise: EO flow looks like an open transfer line, not a "
                "frozen plug, and the 162 C kettle cap is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Kettle 168 C won by 240 us, so the alkoxylation is running packed, not still "
                "free. Holding 8.4 t/h predicts next-sample 164 C > 162 C cap. MODIFY: EO "
                "8.4 -> 5.6 t/h. Observed after clamp 157 C < 162. A full REJECT is not "
                "indicated: a sound alkoxylation kettle accepts 5.6 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "kettle_C",
                            OrderedDict(
                                [
                                    ("cap", 162.0),
                                    ("observed", 168.0),
                                    ("predicted_unclamped_next", 164.0),
                                    ("clamped_eo_t_h", 5.6),
                                    ("observed_after_clamp", 157.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 240),
                                    ("combined_jitter_us", 68),
                                    ("ratio", 3.53),
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
            ("name", "clamped_eo_alkox"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("eo_t_h", 5.6),
                        ("kettle_C", 157.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: EO 8.4 -> 5.6 t/h. Process-correct vs the 162 C kettle cap. Transfer-line "
                "freeze-plug rupture still occurs at 23.800 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held kettle at 157 C. At 23.800 ms stored freeze-plug load "
                "ruptured a PO-rich transfer line. Clamp reduced EO energy; it did not dump the plug charge. "
                "Partnered negative: process heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("eo", "clamp executed; kettle 157 C < 162"),
                        ("transfer_line", "freeze-plug rupture at 23.800 ms"),
                        ("repair", "20 min emergency isolate + line pull"),
                        ("mission", "kettle still alkoxylating; plug precursor controlled"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither kettle RTD nor EO flow predicted the plug charge; ae.xfer.plug is a new channel at 23.800 ms, 17.800 ms after the gate, still inside the 44 ms raster.",
                    "Delayed (20 min): emergency isolate and line pull close the rupture. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "20 min emergency isolate + line pull after a PO-rich transfer-line freeze-plug rupture. Safety "
                "head -0.62 prices the precursor; task_progress stays +0.34 because the EO clamp "
                "completed under the 162 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.kettle.c (5.100 ms, 168 C)"),
                        ("loser", "ft.eo.t_h (5.340 ms, 8.4 t/h)"),
                        ("margin_us", 240),
                        (
                            "counterfactual_if_reversed",
                            "Flow-first by < 240 us inside the 400 us window would have kept "
                            "8.4 t/h cruise; predicted next-sample 164 C would have exceeded the "
                            "162 C cap even without the plug charge. The MODIFY is still the "
                            "correct process. The rupture is a later world charge either way, cheaper "
                            "with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 23800),
            (
                "reward_inflection_note",
                "Safety collapses at the 23.800 ms transfer-line freeze-plug rupture (tick t_us=23800), inside the "
                "44 ms raster. The correct MODIFY at 6.000 ms is in the same excerpt. Do not put "
                "inflection on the +20 min isolate tick.",
            ),
            ("delayed_surprise_s", 1200.0),
            ("abort_s", 1200),
        ]
    )
    spikes = [
        spike("enc.alkox.ctx", 1.180, 0.43),
        spike("rtd.kettle.c", 2.440, 0.62),
        spike("ft.eo.t_h", 3.360, 0.55),
        spike("rtd.kettle.c", 5.100, 1.34),
        spike("ft.eo.t_h", 5.340, 1.12),
        spike("ctrl.gate", 6.000, 0.97),
        spike("rtd.kettle.c", 7.800, 0.81),
        spike("ft.eo.t_h", 11.200, 0.66),
        spike("ctrl.gate", 16.200, 0.84),
        spike("ae.xfer.plug", 23.800, 1.42),
        spike("ae.xfer.plug", 25.400, 0.91),
        spike("enc.alkox.ctx", 31.600, 0.41),
        spike("rtd.kettle.c", 40.200, 0.58),
    ]
    ras = raster_core(
        44,
        88,
        22,
        85,
        routing(
            "thalamic-relay.rtd-kettle",
            "spikenaut.policy.eo-clamp",
            [
                ("relay.rtd.kettle", "policy.eo_clamp", 0.64),
                ("relay.ft.eo", "policy.xfer_hold", 0.29),
                ("relay.ae.xfer", "policy.eo_clamp", -0.46),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at RTD win (5.100 ms) opens a 50 ms eligibility "
            "trace that still covers the 23.800 ms transfer-line freeze-plug rupture",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("eo_clamp", 48, 0.50, 220.0, 4),
                    pop("xfer_hold", 48, 0.50, 50.0, 1),
                    pop("kettle_cap_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r90-467",
        "Alkox-Grove alkoxylation / AK-2: kettle RTD beats EO encoder by 240 us; correct "
        "MODIFY still eats an in-window transfer-line freeze-plug rupture (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "44 ms raster. total -0.44 = 0.34 + -0.62 + -0.16 + 0.04 + -0.04. Named "
        "isolate+line-pull loss is not netted into task_progress.",
        ras,
        gate,
        "polyether-polyol-alkoxylator",
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
        "20 min gap.",
        2,
    )


def record_468():
    ticks = [
        tick(1760, 0.01, 0.04, 0.02, 0.01, 0.01),
        tick(4400, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(4620, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(5500, 0.03, 0.12, 0.04, 0.04, 0.02),
        tick(5900, 0.02, 0.07, 0.01, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.pmma.ctx", 1.060, 0.44),
        spike("ae.gel.pps", 2.280, 0.71),
        spike("enc.agit.rpm", 3.120, 0.52),
        spike("ae.gel.pps", 4.400, 1.36),
        spike("enc.agit.rpm", 4.620, 1.14),
        spike("ctrl.gate", 5.500, 0.98),
        spike("ae.gel.pps", 7.700, 0.82),
        spike("enc.agit.rpm", 11.400, 0.61),
        spike("ctrl.gate", 16.900, 0.86),
        spike("ae.gel.pps", 25.600, 0.70),
        spike("enc.agit.rpm", 34.400, 0.48),
        spike("t.jacket.ctx", 43.200, 0.40),
    ]
    excerpt = independent_excerpt(90468, 108, 46000, 13, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "PMMA bulk-reactor HIL kettle BR-3 at Pmma-Chine already shows gel-effect acoustic "
                "emission at 48 pps when that burst races an agitator encoder still printing 62 rpm. "
                "Speed-up is legal only if AE <= 32 pps. AE-first latches hold; encoder-first would treat "
                "in-band rpm as gel clearance.",
            ),
            ("domain", "pmma-bulk-reactor"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not speed BR-3 unless gel AE <= 32 pps; keep MMA feed 0 t/h until the "
                "syrup is quiet.",
            ),
            ("t0_us", 1762300000000468),
            ("gate_latency_us", 1100),
            ("race_window_us", 400),
            ("race_window_rel_ms", [4.400, 4.800]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.gel.pps 48 pps Trommsdorff gel flare",
                                "enc.agit.rpm 62 rpm still-in-band agitator speed",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches REJECT hold 0 rpm; encoder-first would speed 62 rpm "
                            "on an in-band-rate-as-clearance model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one AE envelope slot versus the agitator-encoder publisher "
                            "on this pad cycle.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 60 us (AE 28 + encoder 32): 3.7x over a "
                            "2.0x trust floor. Pad injects encoder 80-120 us before the AE envelope "
                            "finishes (loop lag, not a sensor fault); the encoder packet is still "
                            "the loser in this 400 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "gel AE analyzer, 28 us jitter, 32 pps trip",
                    "agitator encoder, 32 us jitter",
                    "jacket RTD (context)",
                    "MMA header FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_trip_pps", 32.0),
                        ("observed_ae_pps", 48.0),
                        ("agit_cap_rpm", 80.0),
                        ("proposed_agit_rpm", 62.0),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        ("bench", "Pmma-Chine PC-HIL bulk-PMMA pad, BR-3"),
                        ("inject", "AE envelope delayed 80-120 us vs encoder; loop lag, not a false AE pickup"),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. BR-3 on Pmma-Chine HIL pad; MMA armed; agitator 62 rpm.",
                    "2. AE trip 32 pps; observed 48 pps gel-effect flare.",
                    "3. Encoder precursor at 1.060 ms.",
                    "4. Race window [4.400, 4.800] ms.",
                    "5. AE 48 pps at 4.400 ms (winner).",
                    "6. Agitator encoder 62 rpm at 4.620 ms (loser by 220 us).",
                    "7. Gate at 5.500 ms: REJECT hold 0 rpm, do not speed.",
                    "8. Pad recycle 8 min; AE decays under 32 pps after hold.",
                    "9. Syrup never ran a gel dump; encoder-as-clearance would have sped into the flare.",
                    "10. QA: correct gate was REJECT; leave 0 rpm until AE <= 32 pps.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "agit_62"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("agit_rpm", 62.0),
                        ("ae_pps", 48.0),
                        ("hold", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 48.0),
                        ("ae_trip_pps", 32.0),
                        ("agit_rpm", 62.0),
                        ("agit_cap_rpm", 80.0),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 60),
                        ("t_gate_us", 5500),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 62 rpm because agitator speed is under the 80 rpm cap and treats "
                "the encoder as gel clearance, ignoring the 48 pps AE flare.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "AE 48 pps won by 220 us and is over the 32 pps trip. Encoder 62 rpm is under "
                "the 80 rpm cap but is not clearance. REJECT: hold 0 rpm until AE <= 32 pps.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "gel_ae_pps",
                            OrderedDict(
                                [
                                    ("trip", 32.0),
                                    ("observed", 48.0),
                                    ("executed_agit_rpm", 0.0),
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
            ("name", "agit_hold_ae"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("agit_rpm", 0.0),
                        ("ae_pps", 48.0),
                        ("hold", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: agitator 62 -> 0 rpm. Routing relay.ae.gel -> policy.hold_reject. "
                "Do not speed into the 48 pps flare.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held BR-3 at 0 rpm while AE 48 pps decayed. Encoder-as-clearance "
                "would have sped 62 rpm into the flare. Pad recycle 8 min.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("agitator", "held at 0 rpm"),
                        ("gel", "AE flare decaying under trip after hold"),
                        ("syrup", "no gel dump"),
                        ("pad", "8 min recycle"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Pad injects encoder 80-120 us before AE envelope finish; that is loop lag, not a false AE pickup.",
                    "Delayed (8 min): pad recycle restacks the PMMA syrup after AE < 32 pps.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.gel.pps (4.400 ms, 48 pps)"),
                        ("loser", "enc.agit.rpm (4.620 ms, 62 rpm)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Encoder-first by < 220 us would have treated 62 rpm as clearance and "
                            "sped into the 48 pps flare. The REJECT is still required; reversal "
                            "only delays the AE bind.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5500),
            (
                "reward_inflection_note",
                "Safety credit lands at the correct REJECT (5.500 ms, tick 4). Pad recycle is delayed surprise.",
            ),
            ("delayed_surprise_s", 480.0),
            ("pad_recycle_s", 480),
        ]
    )
    ras = raster_core(
        46,
        108,
        21,
        104,
        routing(
            "relay.ae.gel",
            "policy.hold_reject",
            [
                ("relay.ae.gel", "policy.hold_reject", 0.74),
                ("relay.enc.agit", "policy.agit_go", 0.18),
            ],
            "dopamine",
            0.06,
            "ae_trip_stdp; DA tags the hold_reject bind at the AE win",
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
                    pop("hold_reject", 64, 0.50, 160.0, 4),
                    pop("agit_go", 64, 0.80, 8.0, 0),
                    pop("ae_trip_veto", 32, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r90-468",
        "Pmma-Chine bulk-PMMA HIL / BR-3: gel AE 48 pps beats agitator encoder 62 rpm by 220 us; "
        "correct REJECT holds the syrup kettle",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 48 > 32 trip beats in-band agitator speed. total +0.78 = "
        "0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "pmma-bulk-reactor",
        [
            "reject",
            "hil-pad",
            "ae-vs-encoder",
            "gel-hold",
            "sidecar-convictable",
            "hil",
        ],
        "Teaches a probe that an in-band agitator encoder is not gel clearance when "
        "AE is over trip and routing.table[0].to is policy.hold_reject.",
        3,
    )


def record_469():
    ticks = [
        tick(2240, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5600, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5820, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(6500, 0.12, 0.08, 0.05, 0.03, 0.03),
        tick(6900, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(540000000, 0.02, 0.02, 0.01, 0.00, 0.00),
    ]
    params = OrderedDict(
        [
            ("h2_nm3h", 2400.0),
            ("liquor_C", 54.2),
            ("hold", False),
        ]
    )
    spikes = [
        spike("ft.h2.ctx", 1.280, 0.42),
        spike("rtd.ws.c", 2.860, 0.58),
        spike("ir.bed.glint", 4.360, 0.50),
        spike("rtd.ws.c", 5.600, 1.28),
        spike("ir.bed.glint", 5.820, 1.10),
        spike("ctrl.gate", 6.500, 0.96),
        spike("rtd.ws.c", 8.800, 0.74),
        spike("ir.bed.glint", 12.200, 0.60),
        spike("ctrl.gate", 17.600, 0.82),
        spike("rtd.ws.c", 24.000, 0.55),
        spike("ft.h2.ctx", 29.200, 0.40),
    ]
    excerpt = independent_excerpt(90469, 64, 30000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Working-solution hydrogenator HY-2 at Hydranth-Ley already keeps a liquor RTD of "
                "54.2 C when that analog sample races a bed-IR glint still printing 71 C. Commanded "
                "2400 Nm3/h H2 and 54.2 C sit 400 Nm3/h and 7.8 C inside the legal envelopes. The liquor "
                "win only ratifies the hydrogen already in the working solution.",
            ),
            ("domain", "h2o2-ao-hydrogenator"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the anthraquinone working-solution hydrogen pass on Hydranth-Ley, keep liquor "
                "<= 62.0 C and H2 >= 1800 Nm3/h, and leave bed draft in spec.",
            ),
            ("t0_us", 1762300000000469),
            ("gate_latency_us", 900),
            ("race_window_us", 400),
            ("race_window_rel_ms", [5.600, 6.000]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.ws.c 54.2 C working-solution liquor",
                                "ir.bed.glint 71 C bed-IR smear, not liquor",
                            ],
                        ),
                        (
                            "semantics",
                            "Liquor-first should ACCEPT already-legal 2400 Nm3/h. Glint-first would "
                            "only delay confirmation of the same legal hydrogenator.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one liquor RTD slot versus the bed-IR publisher on this "
                            "2 kHz AO-hydrogenator bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 64 us (RTD 30 + IR 34): 3.4x over a "
                            "2.0x trust floor. Order is liquor-first. The pass is already legal either way.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "working-solution liquor RTD, 2 kHz, 30 us jitter",
                    "bed IR pyrometer, 1 kHz, 34 us jitter, glint not liquor",
                    "H2 header FT (context)",
                    "anthraquinone GC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("liquor_cap_C", 62.0),
                        ("observed_liquor_C", 54.2),
                        ("h2_floor_nm3h", 1800.0),
                        ("h2_cap_nm3h", 2800.0),
                        ("proposed_h2_nm3h", 2400.0),
                    ]
                ),
            ),
            (
                "solver",
                OrderedDict(
                    [
                        ("kind", "1d_working_sol_h2_kernel"),
                        ("note", "Sidecar 1D H2-in-working-solution kernel; plant remains simulated, not real."),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. HY-2 indexed on Hydranth-Ley; liquor 54.2 C; H2 2400 Nm3/h armed.",
                    "2. Liquor cap 62.0 C; H2 floor 1800 / cap 2800 Nm3/h; proposed already legal.",
                    "3. H2 precursor at 1.280 ms.",
                    "4. Race window [5.600, 6.000] ms.",
                    "5. Liquor RTD 54.2 C at 5.600 ms (winner).",
                    "6. Bed IR glint 71 C at 5.820 ms (loser by 220 us).",
                    "7. Gate at 6.500 ms: ACCEPT 2400 Nm3/h.",
                    "8. Hydrogenator stays in envelope; glint is not liquor.",
                    "9. 9 min survey confirms conversion in spec.",
                    "10. QA: correct gate was ACCEPT; leave 2400 Nm3/h; ignore bed-IR glint.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "h2_2400_hold"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("liquor_C", 54.2),
                        ("liquor_cap_C", 62.0),
                        ("glint_C", 71.0),
                        ("h2_nm3h", 2400.0),
                        ("h2_floor_nm3h", 1800.0),
                        ("h2_cap_nm3h", 2800.0),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 64),
                        ("t_gate_us", 6500),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2400 Nm3/h because liquor 54.2 C is 7.8 C under the 62.0 C cap "
                "and H2 sits 400 Nm3/h inside the 1800-2800 envelope; bed-IR 71 C is glint, not liquor.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Liquor 54.2 C won by 220 us and is under the 62.0 C cap. Proposed 2400 Nm3/h is "
                "inside 1800-2800. Bed-IR 71 C is glint. ACCEPT: leave 2400 Nm3/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "liquor_C",
                            OrderedDict(
                                [
                                    ("cap", 62.0),
                                    ("observed", 54.2),
                                    ("executed_h2_nm3h", 2400.0),
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
            ("name", "h2_2400_hold"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: leave 2400 Nm3/h. Routing relay.rtd.ws -> policy.go_accept. "
                "Bed-IR glint does not hitch the already-legal hydrogenator.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left HY-2 at 2400 Nm3/h. Liquor stayed 54.2 C under 62.0 C. "
                "Bed-IR glint 71 C was not process T. Survey 9 min.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("h2", "left at 2400 Nm3/h"),
                        ("liquor", "54.2 C under 62.0 C cap"),
                        ("bed", "IR glint ignored"),
                        ("survey", "9 min conversion check"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "1D working-solution H2 kernel predicted the same legal envelope as the liquor RTD.",
                    "Delayed (9 min): survey confirms anthraquinone conversion in spec after the ACCEPT.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.ws.c (5.600 ms, 54.2 C)"),
                        ("loser", "ir.bed.glint (5.820 ms, bed-IR smear)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 220 us would only delay confirmation. The pass stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6500),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (6.500 ms, tick 4). Survey is delayed surprise.",
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
            "relay.rtd.ws",
            "policy.go_accept",
            [
                ("relay.rtd.ws", "policy.go_accept", 0.66),
                ("relay.ir.bed", "policy.hitch_hold", 0.20),
            ],
            "serotonin",
            0.045,
            "legal_ao_h2_stdp; 5-HT tags the go_accept bind at the liquor-RTD win",
        ),
        excerpt,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("go_accept", 40, 0.50, 130.0, 2),
                    pop("hitch_hold", 40, 0.80, 10.0, 0),
                    pop("liquor_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r90-469",
        "Hydranth-Ley AO hydrogenator / HY-2: liquor 54.2 C beats bed-IR glint by 220 us; "
        "ACCEPT already-legal 2400 Nm3/h H2",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal AO hydrogenator pass. total +1.06 = "
        "0.42 + 0.28 + 0.18 + 0.10 + 0.08.",
        ras,
        gate,
        "h2o2-ao-hydrogenator",
        [
            "accept",
            "already-legal",
            "liquor-vs-bed-ir",
            "sidecar-convictable",
            "simulated",
        ],
        "Teaches that a liquor RTD under cap can confirm an already-legal H2 pass without "
        "a bed-IR hitch becoming a hold.",
        4,
    )


def record_470():
    ticks = [
        tick(1520, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(3800, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(4020, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(4500, 0.14, 0.10, 0.05, 0.04, 0.03),
        tick(4900, 0.06, 0.06, 0.02, 0.01, 0.01),
        tick(360000000, 0.02, 0.02, 0.01, 0.01, 0.00),
    ]
    params = OrderedDict(
        [
            ("sicl4_kg_h", 1.8),
            ("preform_C", 1620.0),
            ("hold", False),
        ]
    )
    spikes = [
        spike("enc.lathe.ctx", 1.040, 0.42),
        spike("py.preform.c", 2.160, 0.58),
        spike("ir.plasma.glint", 3.040, 0.50),
        spike("py.preform.c", 3.800, 1.28),
        spike("ir.plasma.glint", 4.020, 1.10),
        spike("ctrl.gate", 4.500, 0.96),
        spike("py.preform.c", 6.200, 0.74),
        spike("ir.plasma.glint", 9.400, 0.60),
        spike("ctrl.gate", 14.200, 0.82),
        spike("py.preform.c", 19.600, 0.55),
        spike("enc.lathe.ctx", 23.200, 0.40),
    ]
    excerpt = independent_excerpt(90470, 56, 24000, 11, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "MCVD preform lathe ML-1 at McVd-Hanger already tracks a substrate pyrometer of "
                "1620 C when that analog sample races a plasma-IR glint still printing 1810 C. Commanded "
                "1.8 kg/h SiCl4 sits 0.3 kg/h inside the legal envelope and 1620 C sits 60 C under the "
                "1680 C cap. The pyrometer win only ratifies the deposition already on the bait.",
            ),
            ("domain", "optical-fiber-mcvd"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the MCVD soot pass on McVd-Hanger, keep substrate <= 1680 C and SiCl4 "
                ">= 1.2 kg/h, and leave plasma draft in spec.",
            ),
            ("t0_us", 1762300000000470),
            ("gate_latency_us", 700),
            ("race_window_us", 400),
            ("race_window_rel_ms", [3.800, 4.200]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "py.preform.c 1620 C substrate pyrometer",
                                "ir.plasma.glint 1810 C plasma smear, not bait",
                            ],
                        ),
                        (
                            "semantics",
                            "Pyrometer-first should ACCEPT already-legal 1.8 kg/h. Glint-first would "
                            "only delay confirmation of the same legal lathe.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one pyrometer slot versus the plasma-IR publisher on this "
                            "2 kHz MCVD bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 220 us vs combined jitter 62 us (pyrometer 28 + IR 34): 3.5x over a "
                            "2.0x trust floor. Order is pyrometer-first. The pass is already legal either way.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "substrate pyrometer, 2 kHz, 28 us jitter",
                    "plasma IR, 1 kHz, 34 us jitter, glint not bait",
                    "lathe encoder (context)",
                    "SiCl4 mass-flow (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("preform_cap_C", 1680.0),
                        ("observed_preform_C", 1620.0),
                        ("sicl4_floor_kg_h", 1.2),
                        ("sicl4_cap_kg_h", 2.4),
                        ("proposed_sicl4_kg_h", 1.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. ML-1 indexed on McVd-Hanger; pyrometer 1620 C; SiCl4 1.8 kg/h armed.",
                    "2. Substrate cap 1680 C; SiCl4 floor 1.2 / cap 2.4 kg/h; proposed already legal.",
                    "3. Lathe precursor at 1.040 ms.",
                    "4. Race window [3.800, 4.200] ms.",
                    "5. Pyrometer 1620 C at 3.800 ms (winner).",
                    "6. Plasma IR glint 1810 C at 4.020 ms (loser by 220 us).",
                    "7. Gate at 4.500 ms: ACCEPT 1.8 kg/h.",
                    "8. Deposition stays in envelope; glint is not substrate.",
                    "9. 6 min survey confirms soot density in spec.",
                    "10. QA: correct gate was ACCEPT; leave 1.8 kg/h; ignore plasma-IR glint.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "sicl4_1p8_hold"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("preform_C", 1620.0),
                        ("preform_cap_C", 1680.0),
                        ("glint_C", 1810.0),
                        ("sicl4_kg_h", 1.8),
                        ("sicl4_floor_kg_h", 1.2),
                        ("sicl4_cap_kg_h", 2.4),
                        ("race_margin_us", 220),
                        ("combined_jitter_us", 62),
                        ("t_gate_us", 4500),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.8 kg/h because substrate 1620 C is 60 C under the 1680 C cap "
                "and SiCl4 sits 0.3 kg/h inside the 1.2-2.4 envelope; plasma IR 1810 C is glint, not bait.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Pyrometer 1620 C won by 220 us and is under the 1680 C cap. Proposed 1.8 kg/h is "
                "inside 1.2-2.4. Plasma IR 1810 C is glint. ACCEPT: leave 1.8 kg/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "preform_C",
                            OrderedDict(
                                [
                                    ("cap", 1680.0),
                                    ("observed", 1620.0),
                                    ("executed_sicl4_kg_h", 1.8),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 220),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 3.55),
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
            ("name", "sicl4_1p8_hold"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: leave 1.8 kg/h. Routing relay.py.preform -> policy.go_accept. "
                "Plasma-IR glint does not hitch the already-legal lathe.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left ML-1 at 1.8 kg/h. Substrate stayed 1620 C under 1680 C. "
                "Plasma-IR glint 1810 C was not bait T. Survey 6 min.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("sicl4", "left at 1.8 kg/h"),
                        ("preform", "1620 C under 1680 C cap"),
                        ("plasma", "IR glint ignored"),
                        ("survey", "6 min soot-density check"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Plasma-IR 1810 C is torch glint on the bait, not substrate pyrometry.",
                    "Delayed (6 min): survey confirms soot density in spec after the ACCEPT.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "py.preform.c (3.800 ms, 1620 C)"),
                        ("loser", "ir.plasma.glint (4.020 ms, plasma smear)"),
                        ("margin_us", 220),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 220 us would only delay confirmation. The pass stays "
                            "legal either way; ACCEPT is still required.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4500),
            (
                "reward_inflection_note",
                "Task credit lands at the ACCEPT (4.500 ms, tick 4). Survey is delayed surprise.",
            ),
            ("delayed_surprise_s", 360.0),
            ("survey_s", 360),
        ]
    )
    ras = raster_core(
        24,
        56,
        38,
        51,
        routing(
            "relay.py.preform",
            "policy.go_accept",
            [
                ("relay.py.preform", "policy.go_accept", 0.66),
                ("relay.ir.plasma", "policy.hitch_hold", 0.20),
            ],
            "adenosine",
            0.04,
            "legal_mcvd_stdp; adenosine tags the go_accept bind at the pyrometer win",
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
                    pop("go_accept", 40, 0.50, 160.0, 2),
                    pop("hitch_hold", 40, 0.80, 10.0, 0),
                    pop("preform_cap_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r90-470",
        "McVd-Hanger MCVD lathe / ML-1: substrate 1620 C beats plasma glint by 220 us; "
        "ACCEPT already-legal 1.8 kg/h SiCl4",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal MCVD pass. total +1.14 = "
        "0.44 + 0.32 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "optical-fiber-mcvd",
        [
            "accept",
            "already-legal",
            "pyrometer-vs-plasma-ir",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches that a substrate pyrometer under cap can confirm an already-legal MCVD pass without "
        "a plasma-IR hitch becoming a hold.",
        5,
    )
