def lif_211_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.42
    stim = (22000, 25000)
    seed = 39211
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
    tear = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.leak" for t, _ in picked]
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
            ("seed", 39211),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 air-ratio clamp bias; stim 22-25 ms is the WHB tube leak.",
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


def record_211():
    excerpt, extra = lif_211_excerpt()
    ticks = [
        tick(2048, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5120, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5288, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5800, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22400, 0.04, -0.45, -0.03, -0.01, -0.01),
        tick(840000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Thermal-reactor TR-2 at Pyrite-Gill PG-6 is feeding acid-gas at 1.05 air ratio while "
                "the tail-gas H2S analyzer sits at 2.80 percent against a 1.00 percent cap. "
                "H2S-first cuts air 1.05 -> 0.92; furnace-first would keep 1.05 because 1080 C is "
                "still under the 1150 C firebox cap. A WHB tube leak already seated on pass 3 does "
                "not appear on H2S or furnace until the AE dump.",
            ),
            ("domain", "sulfur-claus-furnace"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep TR-2 tail-gas H2S <= 1.00 percent and finish the conversion pass without "
                "dumping acid-gas into the waste-heat boiler.",
            ),
            ("t0_us", 1756850400000211),
            ("gate_latency_us", 680),
            ("race_window_us", 380),
            ("race_window_rel_ms", [5.12, 5.50]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "h2s.tail.pct 2.80 over 1.00 cap",
                                "enc.air.ratio 1.05 with firebox 1080 under 1150",
                            ],
                        ),
                        (
                            "semantics",
                            "H2S-first latches air-ratio clamp 1.05 -> 0.92; furnace-first keeps "
                            "1.05 on a 'still under firebox cap' model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one UV H2S slot versus the air-orifice publisher on this "
                            "Claus skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 168 us vs combined jitter 62 us (H2S 28 + air 34): 2.71x over "
                            "a 2.0x trust floor. Reversing order by < 168 us inside the 380 us "
                            "window would have kept 1.05; predicted next-sample 2.40 percent "
                            "> 1.00 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "tail-gas UV H2S cell, 2 kHz, 28 us jitter",
                    "air-orifice DP + firebox TC, 1 kHz, 34 us jitter",
                    "WHB AE puck (context)",
                    "converter inlet PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("h2s_cap_pct", 1.00),
                        ("observed_h2s_pct", 2.80),
                        ("air_ratio", 1.05),
                        ("firebox_C", 1080.0),
                        ("firebox_cap_C", 1150.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. TR-2 indexed; air ratio 1.05; tail-gas H2S 2.80 percent.",
                    "2. Firebox 1080 C under 1150 C cap; conversion armed.",
                    "3. Orifice precursor at 1.180 ms.",
                    "4. Race window [5.120, 5.500] ms.",
                    "5. h2s.tail.pct 2.80 at 5.120 ms (winner).",
                    "6. enc.air.ratio 1.05 at 5.288 ms (loser by 168 us).",
                    "7. Gate at 5.800 ms: MODIFY clamp 1.05 -> 0.92.",
                    "8. After clamp H2S 0.85 percent <= 1.00; firebox still 1080 C.",
                    "9. At 22.400 ms a WHB tube leak dumps 0.4 t acid-gas.",
                    "10. 14 min tube isolation (abort_s=840); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_air_ratio"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_ratio", 1.05),
                        ("h2s_pct", 2.80),
                        ("firebox_C", 1080.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("h2s_pct", 2.80),
                        ("h2s_cap_pct", 1.00),
                        ("predicted_unclamped_next_pct", 2.40),
                        ("air_ratio", 1.05),
                        ("firebox_C", 1080.0),
                        ("firebox_cap_C", 1150.0),
                        ("race_margin_us", 168),
                        ("combined_jitter_us", 62),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.05 air ratio because firebox 1080 C is under 1150, treating "
                "the 2.80 percent H2S as a still-wet UV cell rather than a tail-gas-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Tail-gas H2S 2.80 percent won by 168 us, so the converter is off-spec, not still a "
                "firebox-temperature story. Holding 1.05 predicts next-sample 2.40 percent > "
                "1.00 cap. MODIFY: air ratio 1.05 -> 0.92. Observed after clamp 0.85 percent "
                "<= 1.00. A full REJECT is not indicated: a clean conversion accepts 0.92.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "h2s_pct",
                            OrderedDict(
                                [
                                    ("cap", 1.00),
                                    ("observed", 2.80),
                                    ("predicted_unclamped_next", 2.40),
                                    ("clamped_air_ratio", 0.92),
                                    ("observed_after_clamp", 0.85),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 168),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 2.71),
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
            ("name", "clamped_air_ratio"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_ratio", 0.92),
                        ("h2s_pct", 0.85),
                        ("firebox_C", 1080.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: air ratio 1.05 -> 0.92. Process-correct vs the 1.00 percent H2S cap. "
                "WHB tube still leaks at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held tail-gas H2S at 0.85 percent. At 22.400 ms a WHB "
                "tube leak already seated on pass 3 dumped 0.4 t of acid-gas. Clamp reduced dump "
                "energy; it did not prevent the leak. Partnered negative: process heads stay "
                "honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("tail_gas", "clamp executed; peak 0.85 percent <= 1.00 cap"),
                        ("whb_tube", "leaked at 22.400 ms; 0.4 t acid-gas"),
                        ("repair", "14 min tube isolation (abort_s=840)"),
                        ("mission", "PG-6 conversion incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither tail-gas H2S nor firebox TC predicted the seated WHB tube leak; ae.tube.leak is a new channel at 22.400 ms, 16.600 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=840): 14 min tube isolation. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "14 min tube isolation after the WHB leak. Safety head -0.64 prices the dump; "
                "task_progress stays +0.30 because the air-ratio clamp completed under the 1.00 "
                "percent cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "h2s.tail.pct (5.120 ms, 2.80 percent)"),
                        ("loser", "enc.air.ratio (5.288 ms, 1.05)"),
                        ("margin_us", 168),
                        (
                            "counterfactual_if_reversed",
                            "Furnace-first by < 168 us inside the 380 us window would have kept "
                            "1.05; predicted next-sample 2.40 percent would have missed the 1.00 "
                            "cap even without the tube leak. The MODIFY is still the correct "
                            "process. The leak is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms WHB leak (tick t_us=22400), inside the 42 ms "
                "raster. The correct MODIFY at 5.800 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=840 isolation tick.",
            ),
            ("delayed_surprise_s", 840),
        ]
    )
    spikes = [
        spike("enc.air.ratio", 1.180, 0.41),
        spike("h2s.tail.pct", 2.048, 0.58),
        spike("enc.air.ratio", 3.400, 0.50),
        spike("h2s.tail.pct", 5.120, 1.31),
        spike("enc.air.ratio", 5.288, 1.12),
        spike("ctrl.gate", 5.800, 0.97),
        spike("h2s.tail.pct", 8.100, 0.82),
        spike("enc.air.ratio", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.tube.leak", 22.400, 1.48),
        spike("ae.tube.leak", 24.100, 0.93),
        spike("enc.air.ratio", 30.200, 0.40),
        spike("h2s.tail.pct", 36.400, 0.55),
    ]
    dw = 0.38
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.claus-h2s",
            "spikenaut.policy.air-clamp",
            [
                ("relay.h2s.tail", "policy.air_clamp", 0.68),
                ("relay.air.ratio", "policy.ratio_hold", 0.29),
                ("relay.ae.tube", "policy.air_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at H2S win (5.120 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.400 ms WHB leak",
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
                    pop_budget("ratio_hold", 40, 0.80, 50.0, dw),
                    pop("leak_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r39-211"),
            (
                "title",
                "Pyrite-Gill PG-6 / Reactor TR-2: tail-gas H2S beats air ratio by 168 us; correct "
                "MODIFY still eats an in-window WHB tube leak (partnered negative total -0.48)",
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
                    "42 ms raster. total -0.48 = 0.30 + -0.64 + -0.14 + 0.04 + -0.04. Named "
                    "tube isolation (abort_s=840) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "sulfur-claus-furnace",
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
                    "14 min tube isolation.",
                    1,
                ),
            ),
        ]
    )


def record_212():
    ticks = [
        tick(2200, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5500, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5680, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6060, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6420, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(660000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.jacket.C", 1.100, 0.42),
        spike("pt.kettle.bar", 2.200, 0.57),
        spike("enc.jacket.C", 3.500, 0.49),
        spike("pt.kettle.bar", 5.500, 1.29),
        spike("enc.jacket.C", 5.680, 1.10),
        spike("ctrl.gate", 6.060, 0.96),
        spike("pt.kettle.bar", 8.200, 0.80),
        spike("enc.jacket.C", 10.200, 0.63),
        spike("ctrl.gate", 10.860, 0.84),
        spike("pt.kettle.bar", 16.400, 0.41),
        spike("enc.jacket.C", 22.100, 0.54),
        spike("pt.kettle.bar", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(39212, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Autoclave kettle K-14 at Vinyl-Garth VG-9 is already in the polymerization hold "
                "with kettle pressure at 12.40 bar against an 11.00 bar kettle cap. Jacket water "
                "sits at 68 C, safely under the 85 C jacket cap, because the hold is not a heat-up. "
                "A timely vent at t_gate would hold the next sample under cap; a weak supervisor "
                "waits one extra PLC scan and applies the same 10.2 bar vent late.",
            ),
            ("domain", "pvc-suspension-kettle"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the VG-9 hold with kettle pressure <= 11.00 bar, leave jacket at the "
                "planned 68 C, and keep the 10.2 bar vent legal.",
            ),
            ("t0_us", 1756850400000212),
            ("gate_latency_us", 560),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.50, 5.86]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.kettle.bar 12.40 bar on hold phase",
                                "enc.jacket.C 68 under 85 jacket cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Kettle-first should latch a timely vent 12.40 -> 10.2 bar at t_gate; "
                            "jacket-first is a false 'still heating' wait for one extra PLC scan.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one kettle-PT slot versus the jacket-RTD publisher on this "
                            "polymerization PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (PT 28 + jacket 32). Order is "
                            "correctly kettle-first. The error is when the clamp is applied, not "
                            "which actuator or how far.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "kettle PT, 2 kHz, 28 us jitter, phase=hold",
                    "jacket RTD, 1 kHz, 32 us jitter",
                    "stirrer tach (context)",
                    "rupture-disk AE puck (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("kettle_cap_bar", 11.00),
                        ("observed_kettle_bar", 12.40),
                        ("cycle_phase", "hold"),
                        ("jacket_C", 68.0),
                        ("jacket_cap_C", 85.0),
                        ("latest_legal_clamp_us", 6060),
                        ("extra_scan_us", 4800),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. K-14 already in polymerization hold; kettle 12.40 bar; heat-up complete.",
                    "2. Jacket 68 C under 85; not a heat-up story.",
                    "3. Encoder precursor at 1.100 ms.",
                    "4. Race window [5.500, 5.860] ms.",
                    "5. pt.kettle.bar 12.40 bar at 5.500 ms (winner).",
                    "6. enc.jacket.C 68 at 5.680 ms (loser by 180 us).",
                    "7. Gate at 6.060 ms: WRONG-MODIFY waits one extra PLC scan (latest_legal_clamp_us=6060).",
                    "8. Same 10.2 bar vent applied late at 10.860 ms; kettle peaked 12.90 bar.",
                    "9. Rupture-disk weep; kettle recycle.",
                    "10. Delayed (abort_s=660): 11 min kettle recycle while K-14 is vented and reseeded.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_hold_pressure"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("kettle_bar", 12.40),
                        ("vent_pct", 0.0),
                        ("extra_plc_scan", False),
                        ("jacket_C", 68.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("kettle_bar", 12.40),
                        ("kettle_cap_bar", 11.00),
                        ("cycle_phase", "hold"),
                        ("jacket_C", 68.0),
                        ("jacket_cap_C", 85.0),
                        ("latest_legal_clamp_us", 6060),
                        ("t_gate_us", 6060),
                        ("t_exec_us", 10860),
                        ("correct_kettle_bar", 10.2),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 660),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 12.40 bar hold: jacket 68 C is under the 85 C cap, "
                "so the 12.40 bar kettle is treated as a still-heating jacket, not an over-cap.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Kettle 12.40 bar exceeds the 11.00 bar cap (true). Confirm on the next PLC scan "
                "before venting, because jacket 68 C is still climbing toward 85 C. Apply the "
                "same 10.2 bar vent after one extra scan.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "kettle_bar",
                            OrderedDict(
                                [
                                    ("cap", 11.00),
                                    ("observed", 12.40),
                                    ("correct_at_t_gate", 10.2),
                                    ("executed_t_exec_us", 10860),
                                    ("latest_legal_clamp_us", 6060),
                                    ("cycle_phase", "hold"),
                                ]
                            ),
                        ),
                        (
                            "timing",
                            OrderedDict(
                                [
                                    ("t_gate_us", 6060),
                                    ("extra_scan_us", 4800),
                                    ("t_exec_us", 10860),
                                    ("late", True),
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
            ("name", "vent_after_extra_scan"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("kettle_bar", 10.2),
                        ("vent_pct", 18.0),
                        ("extra_plc_scan", True),
                        ("t_exec_us", 10860),
                        ("jacket_C", 68.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / clamp-too-late): correct 10.2 bar vent applied at 10.860 ms "
                "after latest_legal_clamp_us=6060. Routing relay.pt.kettle -> policy.wait_scan; "
                "no positive weight to policy.vent_now.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY waited one extra PLC scan and applied the correct 10.2 bar vent "
                "late. Kettle 12.40 bar was over the 11.00 bar cap at t_gate; jacket 68 C was "
                "already legal. Peak 12.90 bar wept the rupture disk. 11 min kettle recycle "
                "(abort_s=660). Correct gate was MODIFY vent 12.40 -> 10.2 bar at t_gate_us=6060.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("kettle", "late vent 10.2 bar; peak 12.90 > 11.00 cap"),
                        ("disk", "rupture-disk weep during extra scan"),
                        ("recycle", "11 min kettle recycle, K-14 reseed"),
                        ("mission", "hold deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Kettle-first was the correct order and the pressure number was over cap; the MODIFY spent that win waiting for a jacket confirmation scan.",
                    "Delayed (abort_s=660): VG-9 holds 11 min while K-14 is vented and reseeded; next drop 14 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "MODIFY vent 12.40 -> 10.2 bar at t_gate_us=6060; extra_plc_scan=false; leave jacket at 68 C.",
                        ),
                        ("correct_actuator", "kettle_vent"),
                        ("wrong_timing", "extra_plc_scan"),
                        ("latest_legal_clamp_us", 6060),
                        ("t_exec_us", 10860),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("kettle_bar", 10.2),
                                    ("extra_plc_scan", True),
                                    ("t_exec_us", 10860),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "11 min kettle recycle (task/efficiency); kettle peaked 12.90 bar during the extra scan (safety near-miss of a late-but-correct-magnitude vent).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.kettle.bar (5.500 ms, 12.40 bar)"),
                        ("loser", "enc.jacket.C (5.680 ms, 68 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Jacket-first by < 180 us would still be under the 85 C jacket cap; "
                            "a correct gate binds pt.kettle.bar to policy.vent_now at t_gate "
                            "either way. The wrong MODIFY spent the kettle win on an extra scan.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6060),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the late-wait bind (6.060 ms, tick 4). "
                "The 11 min kettle recycle is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 660),
        ]
    )
    dw = 0.36
    ras = raster_core(
        28,
        88,
        34,
        84,
        routing(
            "thalamic-relay.kettle-pt",
            "spikenaut.policy.wait-scan",
            [
                ("relay.pt.kettle", "policy.wait_scan", 0.74),
                ("relay.enc.jacket", "policy.wait_scan", 0.22),
            ],
            "acetylcholine",
            0.08,
            "timing_cap_stdp; ACh tags the (wrong) wait_scan bind at the kettle win",
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
                    pop_budget("wait_scan", 48, 0.45, 300.0, dw),
                    pop("vent_now", 48, 0.90),
                    pop("phase_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r39-212"),
            (
                "title",
                "WRONG-MODIFY at Vinyl-Garth VG-9 / Kettle K-14: kettle 12.40 bar read correctly; "
                "correct 10.2 bar vent applied after latest_legal_clamp_us (clamp-too-late)",
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
                    "Wrong-modify / clamp-too-late. Sidecar arithmetic 12.40 > 11.00 on hold is "
                    "true; MODIFY bound to wait_scan. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "pvc-suspension-kettle",
                    [
                        "modify",
                        "wrong-gate",
                        "clamp-too-late",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct kettle-first race can still be a wrong gate "
                    "when the MODIFY waits one extra PLC scan past latest_legal_clamp_us. "
                    "Convictable from timestamps and routing to without PVC physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_213():
    ticks = [
        tick(2768, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6920, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7100, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7700, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(8020, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("enc.steam.bar", 1.400, 0.40),
        spike("ae.bond.pps", 2.768, 0.56),
        spike("enc.steam.bar", 4.200, 0.48),
        spike("ae.bond.pps", 6.920, 1.34),
        spike("enc.steam.bar", 7.100, 1.11),
        spike("ctrl.gate", 7.700, 0.98),
        spike("ae.bond.pps", 10.400, 0.81),
        spike("enc.steam.bar", 14.800, 0.62),
        spike("ctrl.gate", 18.200, 0.84),
        spike("ae.bond.pps", 28.400, 0.52),
        spike("enc.steam.bar", 36.100, 0.39),
        spike("ae.bond.pps", 42.200, 0.44),
    ]
    excerpt = independent_excerpt(39213, 120, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Singlefacer S-6 on the Flute-Wick FW-HIL stand sees bond-line AE at 42 pps while "
                "steam sits at 6.80 bar under an 8.50 bar cap. AE-first holds the flute; steam-first "
                "would dispatch 220 m/min because the header looks legal. The HIL glue-line mockup "
                "is the authority, not the mill floor.",
            ),
            ("domain", "corrugator-singlefacer"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep S-6 from dispatching a starved flute while steam remains under its own cap.",
            ),
            ("t0_us", 1756850400000213),
            ("gate_latency_us", 780),
            ("race_window_us", 320),
            ("race_window_rel_ms", [6.92, 7.24]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.bond.pps 42 over 12 cap",
                                "enc.steam.bar 6.80 under 8.50 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; steam-first dispatches 220 m/min on a "
                            "'header still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one AE puck slot versus the steam-header PT publisher on "
                            "this HIL glue-line bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + steam 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have dispatched 220 m/min into a starved flute.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bond-line AE puck, 50 kHz, 26 us jitter",
                    "steam-header PT, 1 kHz, 32 us jitter",
                    "flute tach (context)",
                    "starch viscosity cup (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 12.0),
                        ("observed_ae_pps", 42.0),
                        ("steam_bar", 6.80),
                        ("steam_cap_bar", 8.50),
                        ("proposed_line_m_min", 220.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. S-6 HIL indexed; line 220 m/min armed.",
                    "2. Steam 6.80 bar under 8.50; AE 42 pps over 12.",
                    "3. Steam precursor at 1.400 ms.",
                    "4. Race window [6.920, 7.240] ms.",
                    "5. ae.bond.pps 42 at 6.920 ms (winner).",
                    "6. enc.steam.bar 6.80 at 7.100 ms (loser by 180 us).",
                    "7. Gate at 7.700 ms: REJECT hold, do not dispatch.",
                    "8. Line 0 m/min; steam left at 6.80 bar.",
                    "9. Glue-line inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min starch reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_flute"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("line_m_min", 220.0),
                        ("hold", False),
                        ("steam_bar", 6.80),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 42.0),
                        ("ae_cap_pps", 12.0),
                        ("steam_bar", 6.80),
                        ("steam_cap_bar", 8.50),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 220 m/min because steam 6.80 bar is under 8.50, treating the "
                "42 pps AE as glue-line noise rather than a starved flute.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bond-line AE 42 pps won by 180 us, so the flute is starved, not still a steam-header "
                "story. Steam 6.80 bar is under 8.50 and does not authorize dispatch. REJECT: hold "
                "line 220 -> 0 m/min. A MODIFY that only trims steam would leave the starved flute.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ae_pps",
                            OrderedDict(
                                [
                                    ("cap", 12.0),
                                    ("observed", 42.0),
                                    ("executed_line_m_min", 0.0),
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
            ("name", "hold_singlefacer"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("line_m_min", 0.0),
                        ("hold", True),
                        ("steam_bar", 6.80),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: line 220 -> 0 m/min. Steam left at 6.80 bar under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held S-6. AE 42 pps beat steam 6.80 bar by 180 us. Steam was "
                "legal; the flute was not. 8 min starch reset (abort_s=480) is delayed survey, "
                "not a process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("line", "held at 0 m/min"),
                        ("steam", "left 6.80 bar < 8.50 cap"),
                        ("glue", "8 min starch reset (abort_s=480)"),
                        ("mission", "HIL flute not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Steam-header PT never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min starch reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.bond.pps (6.920 ms, 42 pps)"),
                        ("loser", "enc.steam.bar (7.100 ms, 6.80 bar)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Steam-first by < 180 us inside the 320 us window would have dispatched "
                            "220 m/min into a starved flute. The REJECT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7700),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.700 ms, tick 4). The 8 min starch "
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
            "thalamic-relay.bond-ae",
            "spikenaut.policy.line-hold",
            [
                ("relay.ae.bond", "policy.line_hold", 0.70),
                ("relay.enc.steam", "policy.steam_go", 0.24),
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
                    pop_budget("line_hold", 56, 0.45, 280.0, dw),
                    pop("steam_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r39-213"),
            (
                "title",
                "Flute-Wick FW-HIL / Singlefacer S-6: bond AE 42 pps beats steam 6.80 bar by 180 us; "
                "correct REJECT holds the flute",
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
                    "Correct REJECT. AE 42 > 12 cap beats legal steam. "
                    "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "corrugator-singlefacer",
                    [
                        "reject",
                        "hil",
                        "ae-vs-steam",
                        "starved-flute",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal steam header can lose to bond-line AE inside a 320 us "
                    "window; reversing 180 us would have dispatched a starved flute.",
                    3,
                ),
            ),
        ]
    )


def record_214():
    ticks = [
        tick(2992, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7480, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7640, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(8120, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8420, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.wall.C", 1.200, 0.40),
        spike("ft.quality.pct", 2.992, 0.55),
        spike("enc.wall.C", 4.400, 0.48),
        spike("ft.quality.pct", 7.480, 1.26),
        spike("enc.wall.C", 7.640, 1.08),
        spike("ctrl.gate", 8.120, 0.95),
        spike("ft.quality.pct", 11.200, 0.78),
        spike("enc.wall.C", 14.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("ft.quality.pct", 22.600, 0.50),
        spike("enc.wall.C", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(39214, 48, 28000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Pass P-2 of the Otter-Brae OB-11 once-through steam generator is already at 98.2 "
                "percent steam quality against a 95.0 percent floor. Tube-wall IR leftover is 512 C "
                "under a 540 C cap. Quality-first accepts the 18.4 kg/s sendout; wall-first would "
                "have rejected a legal pass on a 'still climbing' model.",
            ),
            ("domain", "once-through-steam-gen"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the OB-11 sendout with steam quality >= 95.0 percent and wall <= 540 C.",
            ),
            ("t0_us", 1756850400000214),
            ("gate_latency_us", 640),
            ("race_window_us", 300),
            ("race_window_rel_ms", [7.48, 7.78]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.quality.pct 98.2 over 95.0 floor",
                                "enc.wall.C 512 under 540 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "Quality-first accepts 18.4 kg/s; wall-first would REJECT a legal pass "
                            "as still climbing.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one throttle-calorimeter slot versus the wall-IR publisher "
                            "on this OTSG sim bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 54 us (quality 24 + wall 30): 2.96x "
                            "over a 2.0x trust floor. Reversing order by < 160 us inside the 300 us "
                            "window would have REJECTED an already-legal sendout.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "throttle calorimeter, 2 kHz, 24 us jitter",
                    "tube-wall IR, 1 kHz, 30 us jitter",
                    "feedwater mag (context)",
                    "separator DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("quality_floor_pct", 95.0),
                        ("observed_quality_pct", 98.2),
                        ("wall_C", 512.0),
                        ("wall_cap_C", 540.0),
                        ("steam_kg_s", 18.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Pass P-2 simulated; sendout 18.4 kg/s armed.",
                    "2. Quality 98.2 percent; wall 512 C under 540.",
                    "3. Wall precursor at 1.200 ms.",
                    "4. Race window [7.480, 7.780] ms.",
                    "5. ft.quality.pct 98.2 at 7.480 ms (winner).",
                    "6. enc.wall.C 512 at 7.640 ms (loser by 160 us).",
                    "7. Gate at 8.120 ms: ACCEPT 18.4 kg/s.",
                    "8. Quality stays 98.2 >= 95.0; wall stays 512.",
                    "9. Simulated lighting holds the calorimeter.",
                    "10. Delayed (survey_s=360): 6 min quality survey.",
                ],
            ),
        ]
    )
    params = OrderedDict(
        [
            ("steam_kg_s", 18.4),
            ("quality_pct", 98.2),
            ("wall_C", 512.0),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_sendout"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("quality_pct", 98.2),
                        ("quality_floor_pct", 95.0),
                        ("wall_C", 512.0),
                        ("wall_cap_C", 540.0),
                        ("steam_kg_s", 18.4),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 54),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.4 kg/s because quality 98.2 percent is over the 95.0 floor "
                "and wall 512 C is under 540.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Steam quality 98.2 percent won by 160 us, so the pass is already legal, not still "
                "climbing. Wall 512 C is under 540. ACCEPT the 18.4 kg/s sendout. A REJECT would "
                "idle a legal OTSG pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "quality_pct",
                            OrderedDict(
                                [
                                    ("floor", 95.0),
                                    ("observed", 98.2),
                                    ("executed_steam_kg_s", 18.4),
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
            ("name", "hold_sendout"),
            ("parameters", OrderedDict(params.items())),
            ("gate_effect", "ACCEPT: leave 18.4 kg/s; quality 98.2; wall 512 C."),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 18.4 kg/s sendout. Quality 98.2 percent beat "
                "wall 512 C by 160 us. 6 min quality survey (survey_s=360) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("sendout", "18.4 kg/s held"),
                        ("quality", "98.2 percent >= 95.0 floor"),
                        ("wall", "512 C < 540 cap"),
                        ("survey", "6 min quality survey (survey_s=360)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Wall IR never approached 540 C; quality was already over floor.",
                    "Delayed (survey_s=360): 6 min calorimeter survey on the simulated pass.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.quality.pct (7.480 ms, 98.2 percent)"),
                        ("loser", "enc.wall.C (7.640 ms, 512 C)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Wall-first by < 160 us inside the 300 us window would have REJECTED "
                            "an already-legal sendout. The ACCEPT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 8120),
            (
                "reward_inflection_note",
                "Task and safety rise at the correct ACCEPT (8.120 ms, tick 4). The 6 min survey "
                "is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 360),
        ]
    )
    dw = 0.30
    ras = raster_core(
        28,
        48,
        42,
        56,
        routing(
            "thalamic-relay.otsg-quality",
            "spikenaut.policy.sendout-go",
            [
                ("relay.ft.quality", "policy.sendout_go", 0.69),
                ("relay.enc.wall", "policy.wall_hold", 0.26),
            ],
            "serotonin",
            0.06,
            "accept_stdp; 5-HT tags the quality win as an already-legal hold",
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
                    pop_budget("sendout_go", 44, 0.45, 260.0, dw),
                    pop("wall_hold", 36, 0.90),
                    pop("quality_veto", 18, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r39-214"),
            (
                "title",
                "Otter-Brae OB-11 / Pass P-2: steam quality 98.2 percent beats wall 512 C by 160 us; "
                "correct ACCEPT of an already-legal 18.4 kg/s sendout",
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
                    "Correct ACCEPT. Quality 98.2 >= 95.0; wall 512 < 540. "
                    "total +1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "once-through-steam-gen",
                    [
                        "accept",
                        "simulated",
                        "quality-vs-wall",
                        "already-legal-hold",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal wall IR can lose to throttle calorimeter inside a 300 us "
                    "window; reversing 160 us would have REJECTED an already-legal sendout.",
                    4,
                ),
            ),
        ]
    )


def record_215():
    ticks = [
        tick(2016, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5040, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5640, 0.14, 0.10, 0.06, 0.04, 0.02),
        tick(5920, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(300000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.chain.mpm", 0.980, 0.40),
        spike("ir.fabric.C", 2.016, 0.55),
        spike("enc.chain.mpm", 3.400, 0.48),
        spike("ir.fabric.C", 5.040, 1.24),
        spike("enc.chain.mpm", 5.200, 1.06),
        spike("ctrl.gate", 5.640, 0.94),
        spike("ir.fabric.C", 8.800, 0.76),
        spike("enc.chain.mpm", 12.200, 0.58),
        spike("ctrl.gate", 15.400, 0.80),
        spike("ir.fabric.C", 19.200, 0.50),
        spike("enc.chain.mpm", 22.600, 0.37),
    ]
    excerpt = independent_excerpt(39215, 80, 24000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Frame F-12 at Tenter-Howe TH-8 is running the cotton/poly web at 42 m/min with "
                "fabric IR 148 C against a 165 C yellowing cap. Chain leftover is 42 m/min under "
                "a 55 m/min cap. IR-first accepts the 42 m/min dwell; chain-first would have "
                "rejected a legal frame on a 'still accelerating' model.",
            ),
            ("domain", "stenter-frame"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the TH-8 dwell with fabric IR <= 165 C and chain <= 55 m/min.",
            ),
            ("t0_us", 1756850400000215),
            ("gate_latency_us", 600),
            ("race_window_us", 280),
            ("race_window_rel_ms", [5.04, 5.32]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ir.fabric.C 148 under 165 cap",
                                "enc.chain.mpm 42 under 55 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "IR-first accepts 42 m/min; chain-first would REJECT a legal dwell "
                            "as still accelerating.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one fabric-IR slot versus the chain-encoder publisher on "
                            "this stenter bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (IR 22 + chain 30): 3.08x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal dwell.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "fabric IR pyrometer, 2 kHz, 22 us jitter",
                    "chain encoder, 1 kHz, 30 us jitter",
                    "nozzle PT (context)",
                    "exhaust humidity (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("fabric_cap_C", 165.0),
                        ("observed_fabric_C", 148.0),
                        ("chain_m_min", 42.0),
                        ("chain_cap_m_min", 55.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Frame F-12 indexed; chain 42 m/min armed.",
                    "2. Fabric IR 148 C under 165; chain under 55.",
                    "3. Chain precursor at 0.980 ms.",
                    "4. Race window [5.040, 5.320] ms.",
                    "5. ir.fabric.C 148 at 5.040 ms (winner).",
                    "6. enc.chain.mpm 42 at 5.200 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 42 m/min.",
                    "8. Fabric stays 148 C; chain stays 42 m/min.",
                    "9. Web exits zone 4 on-spec.",
                    "10. Delayed (dwell_s=300): 5 min shade reseq.",
                ],
            ),
        ]
    )
    params = OrderedDict(
        [
            ("chain_m_min", 42.0),
            ("fabric_C", 148.0),
            ("hold", False),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_chain_dwell"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("fabric_C", 148.0),
                        ("fabric_cap_C", 165.0),
                        ("chain_m_min", 42.0),
                        ("chain_cap_m_min", 55.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 42 m/min because fabric 148 C is under 165 and chain 42 is "
                "under 55.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Fabric IR 148 C won by 160 us, so the dwell is already legal, not still "
                "accelerating. Chain 42 m/min is under 55. ACCEPT the 42 m/min dwell. A REJECT "
                "would idle a legal stenter zone.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "fabric_C",
                            OrderedDict(
                                [
                                    ("cap", 165.0),
                                    ("observed", 148.0),
                                    ("executed_chain_m_min", 42.0),
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
            ("name", "hold_chain_dwell"),
            ("parameters", OrderedDict(params.items())),
            ("gate_effect", "ACCEPT: leave 42 m/min; fabric 148 C; chain legal."),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 42 m/min dwell. Fabric 148 C beat chain 42 "
                "m/min by 160 us. 5 min shade reseq (dwell_s=300) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("chain", "42 m/min held"),
                        ("fabric", "148 C < 165 cap"),
                        ("web", "zone 4 on-spec"),
                        ("reseq", "5 min shade reseq (dwell_s=300)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Chain encoder never approached 55 m/min; fabric was already under cap.",
                    "Delayed (dwell_s=300): 5 min shade reseq after zone 4.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ir.fabric.C (5.040 ms, 148 C)"),
                        ("loser", "enc.chain.mpm (5.200 ms, 42 m/min)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Chain-first by < 160 us inside the 280 us window would have REJECTED "
                            "an already-legal dwell. The ACCEPT is still the correct gate.",
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
            "thalamic-relay.fabric-ir",
            "spikenaut.policy.chain-go",
            [
                ("relay.ir.fabric", "policy.chain_go", 0.67),
                ("relay.enc.chain", "policy.chain_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the fabric-IR win as an already-legal dwell",
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
                    pop_budget("chain_go", 40, 0.45, 250.0, dw),
                    pop("chain_hold", 32, 0.90),
                    pop("ir_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r39-215"),
            (
                "title",
                "Tenter-Howe TH-8 / Frame F-12: fabric IR 148 C beats chain 42 m/min by 160 us; "
                "correct ACCEPT of an already-legal 42 m/min dwell",
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
                    "Correct ACCEPT. Fabric 148 < 165; chain 42 < 55. "
                    "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "stenter-frame",
                    [
                        "accept",
                        "designed",
                        "fabric-vs-chain",
                        "already-legal-dwell",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal chain encoder can lose to fabric IR inside a 280 us "
                    "window; reversing 160 us would have REJECTED an already-legal dwell.",
                    5,
                ),
            ),
        ]
    )
