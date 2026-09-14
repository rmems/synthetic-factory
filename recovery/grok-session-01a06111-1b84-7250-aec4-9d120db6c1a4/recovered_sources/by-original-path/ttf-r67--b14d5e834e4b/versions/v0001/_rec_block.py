def lif_351_excerpt():
    n = 72
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.45
    stim = (22000, 25000)
    seed = 67351
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
    take(burst, 9, label_times=(22800, 23300, 24100))
    clamp = [(t, nid) for t, nid in picked if t < 22000][:7]
    tear = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + tear, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.sieve" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 72),
            ("dt_us", 100),
            ("tau_m_ms", 19.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.91),
            ("i_stim_peak", 2.45),
            ("stim_t_us", [22000, 25000]),
            ("i_clamp_extra", 0.62),
            ("clamp_n", 14),
            ("seed", 67351),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 carbonyl-feed clamp bias; stim 22-25 ms is the pellet-sieve tear.",
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


def record_351():
    excerpt, extra = lif_351_excerpt()
    extra = OrderedDict(extra)
    extra["abort_s"] = 840
    extra["delayed_surprise_s"] = 840
    ticks = [
        tick(2280, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5420, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5608, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(6140, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22800, 0.04, -0.45, -0.03, -0.01, -0.01),
        tick(840000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Decomposer D-4 at Mond-Riggs MR-2 already shows 92 ppm outlet CO versus a 40 ppm "
                "stack cap, and the pellet bed is still a legal 178 C. CO-first cuts carbonyl "
                "feed 6.4 -> 4.1 kg/h; bed-first would keep 6.4 kg/h because 178 C sits under "
                "the 190 C sinter ceiling. A torn pellet sieve already seated on the takeaway "
                "does not appear on CO or bed T until the AE dump.",
            ),
            ("domain", "mond-nickel-carbonyl"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep D-4 outlet CO <= 40 ppm and finish the pellet pass without dumping "
                "carbonyl-wet nickel through a torn takeaway sieve.",
            ),
            ("t0_us", 1756850400000351),
            ("gate_latency_us", 720),
            ("race_window_us", 380),
            ("race_window_rel_ms", [5.42, 5.80]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "co.out.ppm 92 over 40 stack cap",
                                "tc.bed.C 178 with sinter 190 still clear",
                            ],
                        ),
                        (
                            "semantics",
                            "CO-first latches feed clamp 6.4 -> 4.1 kg/h; bed-first keeps 6.4 kg/h "
                            "on a 'still under sinter ceiling' model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one IR CO slot versus the bed-TC publisher on this Mond "
                            "decomposer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 188 us vs combined jitter 62 us (CO 28 + TC 34): 3.03x over "
                            "a 2.0x trust floor. Reversing order by < 188 us inside the 380 us "
                            "window would have kept 6.4 kg/h; predicted next-sample 74 ppm > 40 "
                            "stack cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "outlet IR CO cell, 2 kHz, 28 us jitter",
                    "pellet-bed thermocouple tree, 1 kHz, 34 us jitter",
                    "takeaway-sieve AE puck (context)",
                    "carbonyl-orifice DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("co_cap_ppm", 40.0),
                        ("observed_co_ppm", 92.0),
                        ("feed_kg_h", 6.4),
                        ("bed_C", 178.0),
                        ("sinter_cap_C", 190.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Decomposer D-4 indexed on Mond-Riggs MR-2; feed 6.4 kg/h; outlet CO 92 ppm.",
                    "2. Bed 178 C under 190 C sinter; pellet pass armed.",
                    "3. Orifice precursor at 1.160 ms.",
                    "4. Race window [5.420, 5.800] ms.",
                    "5. co.out.ppm 92 at 5.420 ms (winner).",
                    "6. tc.bed.C 178 at 5.608 ms (loser by 188 us).",
                    "7. Gate at 6.140 ms: MODIFY clamp 6.4 -> 4.1 kg/h.",
                    "8. After clamp CO 28 ppm <= 40; bed still 178 C.",
                    "9. At 22.800 ms a torn pellet sieve dumps 0.2 t of wet nickel.",
                    "10. 14 min sieve isolate (abort_s=840); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_carbonyl_feed"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_kg_h", 6.4),
                        ("co_ppm", 92.0),
                        ("bed_C", 178.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("co_ppm", 92.0),
                        ("co_cap_ppm", 40.0),
                        ("predicted_unclamped_next_ppm", 74.0),
                        ("feed_kg_h", 6.4),
                        ("bed_C", 178.0),
                        ("sinter_cap_C", 190.0),
                        ("race_margin_us", 188),
                        ("combined_jitter_us", 62),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 6.4 kg/h because bed 178 C is under 190, treating the 92 ppm "
                "CO as a still-wet IR cell rather than a stack-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Outlet CO 92 ppm won by 188 us, so the decomposer is off-spec, not still a "
                "sinter-ceiling story. Holding 6.4 kg/h predicts next-sample 74 ppm > 40 cap. "
                "MODIFY: feed 6.4 -> 4.1 kg/h. Observed after clamp 28 ppm <= 40. A full REJECT "
                "is not indicated: a clean pellet pass accepts 4.1 kg/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "co_ppm",
                            OrderedDict(
                                [
                                    ("cap", 40.0),
                                    ("observed", 92.0),
                                    ("predicted_unclamped_next", 74.0),
                                    ("clamped_feed_kg_h", 4.1),
                                    ("observed_after_clamp", 28.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 188),
                                    ("combined_jitter_us", 62),
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
            ("name", "clamped_carbonyl_feed"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_kg_h", 4.1),
                        ("co_ppm", 28.0),
                        ("bed_C", 178.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: feed 6.4 -> 4.1 kg/h. Process-correct vs the 40 ppm CO cap. "
                "Pellet sieve still tears at 22.800 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held outlet CO at 28 ppm. At 22.800 ms a torn pellet "
                "sieve already seated on the takeaway dumped 0.2 t of carbonyl-wet nickel. "
                "Clamp reduced dump energy; it did not prevent the tear. Partnered negative: "
                "process heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("outlet", "clamp executed; peak 28 ppm <= 40 cap"),
                        ("sieve", "tore at 22.800 ms; 0.2 t wet nickel"),
                        ("repair", "14 min sieve isolate (abort_s=840)"),
                        ("mission", "MR-2 pellet pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither outlet CO nor bed TC predicted the seated pellet-sieve tear; ae.sieve.tear is a new channel at 22.800 ms, 16.660 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=840): 14 min sieve isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "14 min sieve isolate after the pellet-sieve tear. Safety head -0.64 prices "
                "the dump; task_progress stays +0.30 because the clamp completed.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "co.out.ppm (5.420 ms, 92 ppm)"),
                        ("loser", "tc.bed.C (5.608 ms, 178 C)"),
                        ("margin_us", 188),
                        (
                            "counterfactual_if_reversed",
                            "Bed-first by < 188 us inside the 380 us window would have kept "
                            "6.4 kg/h; predicted next-sample 74 ppm would have missed the 40 "
                            "cap even without the sieve tear. The MODIFY is still the correct "
                            "process. The tear is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22800),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.800 ms pellet-sieve tear (tick t_us=22800), inside "
                "the 42 ms raster. The correct MODIFY at 6.140 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=840 isolate tick.",
            ),
        ]
    )
    spikes = [
        spike("ft.feed.kgph", 1.160, 0.41),
        spike("co.out.ppm", 2.280, 0.58),
        spike("ft.feed.kgph", 3.620, 0.50),
        spike("co.out.ppm", 5.420, 1.31),
        spike("tc.bed.C", 5.608, 1.12),
        spike("ctrl.gate", 6.140, 0.97),
        spike("co.out.ppm", 8.050, 0.82),
        spike("ft.feed.kgph", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.sieve.tear", 22.800, 1.48),
        spike("ae.sieve.tear", 24.400, 0.93),
        spike("ft.feed.kgph", 30.100, 0.40),
        spike("co.out.ppm", 36.050, 0.55),
    ]
    ras = raster_core(
        42,
        72,
        24,
        73,
        routing(
            "thalamic-relay.mond-co",
            "spikenaut.policy.feed-clamp",
            [
                ("relay_co_ppm", "policy_feed_clamp", 0.68),
                ("relay_bed_tc", "policy_feed_hold", 0.29),
                ("relay_ae_sieve", "policy_feed_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at CO win (5.420 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.800 ms pellet-sieve tear",
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
                    pop("feed_clamp", 50, 0.50, 200.0, 4),
                    pop("feed_hold", 40, 0.80, 50.0, 1),
                    pop("sieve_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r67-351"),
            (
                "title",
                "Mond-Riggs MR-2 / Decomposer D-4: outlet CO beats bed T by 188 us; correct "
                "MODIFY still eats an in-window pellet-sieve tear (partnered negative total -0.48)",
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
                    "sieve isolate (abort_s=840) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "mond-nickel-carbonyl",
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
                    "14 min sieve isolate.",
                    1,
                ),
            ),
        ]
    )


def record_352():
    ticks = [
        tick(2210, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5480, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5662, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6020, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6400, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(540000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.bank.ctx", 1.050, 0.42),
        spike("o2.live.pct", 2.210, 0.57),
        spike("o2.idle.pct", 3.080, 0.88),
        spike("o2.live.pct", 5.480, 1.29),
        spike("o2.idle.pct", 5.662, 1.10),
        spike("ctrl.gate", 6.020, 0.96),
        spike("ft.air.idle", 6.400, 1.18),
        spike("o2.live.pct", 7.800, 0.80),
        spike("o2.idle.pct", 10.200, 0.63),
        spike("ctrl.gate", 13.500, 0.84),
        spike("enc.bank.ctx", 18.400, 0.41),
        spike("o2.live.pct", 22.100, 0.54),
        spike("o2.idle.pct", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(67352, 96, 30000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Oxidizer bank A at Quinone-Beck QB-6 is the live string: working-solution O2 "
                "is 8.4 percent over a 6.0 percent cap while idle bank B sits at 3.1 percent. "
                "Air on A is already filed at 14.0 Nm3/h. Live-first should MODIFY-cut air on "
                "A 14.0 -> 7.2; a weak supervisor binds the idle-string selector leftover from "
                "last week's B service and MODIFY-cuts air on parked B instead.",
            ),
            ("domain", "hydrogen-peroxide-AO"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Cut air on the live oxidizer string while O2 stays <= 6.0 percent; do not "
                "spend the clamp on the idle parallel bank.",
            ),
            ("t0_us", 1756850400000352),
            ("gate_latency_us", 540),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.4, 5.76]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "o2.live.pct 8.4 percent on live string A",
                                "o2.idle.pct 3.1 percent on parked string B",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-first should latch air-cut 14.0 -> 7.2 Nm3/h on string A; "
                            "idle-first is a false 'cut the last-serviced bank' bind on B.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one live-O2 sample versus the idle-bank publisher on this "
                            "AO oxidizer PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 182 us vs combined jitter 60 us (live 28 + idle 32). Order "
                            "is correctly live-first. The error is which string the MODIFY binds, "
                            "not the race order.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live-string paramagnetic O2, 2 s cycle, 28 us jitter on this packet",
                    "idle-string O2 register, 32 us jitter",
                    "bank-selector encoder (context)",
                    "working-solution PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("o2_cap_pct", 6.0),
                        ("live_o2_pct", 8.4),
                        ("idle_o2_pct", 3.1),
                        ("live_string", "A"),
                        ("idle_string", "B"),
                        ("proposed_air_nm3h", 14.0),
                        ("correct_air_nm3h", 7.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Oxidizer bank A live; air 14.0 Nm3/h armed; bank B parked.",
                    "2. Live O2 8.4 > 6.0 cap; idle O2 3.1 under cap.",
                    "3. Idle register sampled at 3.080 ms (selector leftover from B service).",
                    "4. Race window [5.400, 5.760] ms.",
                    "5. o2.live.pct 8.4 at 5.480 ms (winner).",
                    "6. o2.idle.pct 3.1 at 5.662 ms (loser by 182 us).",
                    "7. Gate at 6.020 ms: WRONG MODIFY air 14.0 -> 7.2 on idle string B.",
                    "8. bind_idle_string=true; executed.string=B != live A.",
                    "9. Live A stays 14.0 Nm3/h; O2 climbs toward 9.1 percent.",
                    "10. Delayed (abort_s=540): 9 min working-solution dump.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_live_air"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_nm3h", 14.0),
                        ("string", "A"),
                        ("bind_idle_string", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_o2_pct", 8.4),
                        ("o2_cap_pct", 6.0),
                        ("idle_o2_pct", 3.1),
                        ("live_string", "A"),
                        ("idle_string", "B"),
                        ("live_over_cap", True),
                        ("idle_under_cap", True),
                        ("race_margin_us", 182),
                        ("combined_jitter_us", 60),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping 14.0 Nm3/h on live A, treating 8.4 percent O2 as a "
                "still-wet cell. Idle B at 3.1 percent is not the actuator.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Idle-string O2 3.1 percent still looks like the last-serviced bank, so the "
                "supervisor cuts air 14.0 -> 7.2 Nm3/h on parked B to 'protect' the oxidizer. "
                "The live O2 that won the race reads 8.4 percent, over the 6.0 cap, on string "
                "A. The MODIFY is plausible to a weak supervisor that treats the idle selector "
                "as the live string.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "o2_pct",
                            OrderedDict(
                                [
                                    ("cap", 6.0),
                                    ("live", 8.4),
                                    ("idle_bound", 3.1),
                                    ("executed_string", "B"),
                                    ("executed_air_nm3h", 7.2),
                                ]
                            ),
                        ),
                        (
                            "string_bind",
                            OrderedDict(
                                [
                                    ("live_string", "A"),
                                    ("idle_string", "B"),
                                    ("executed_string", "B"),
                                    ("bind_idle_string", True),
                                    ("t_gate_us", 6020),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 182),
                                    ("combined_jitter_us", 60),
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
            ("name", "idle_string_air_cut"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_nm3h", 7.2),
                        ("string", "B"),
                        ("bind_idle_string", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "WRONG MODIFY: air 14.0 -> 7.2 Nm3/h bound to idle string B. Live A remains "
                "14.0 with O2 8.4 > 6.0. bind_idle_string=true.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-modify / wrong-string (live vs idle parallel bank). Live O2 8.4 stayed "
                "over the 6.0 cap on string A. The supervisor still cut air on parked B. Nine "
                "minutes of working-solution dump (abort_s=540).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("idle_B", "air cut to 7.2 Nm3/h on a parked bank"),
                        ("live_A", "still 14.0 Nm3/h; O2 8.4 climbing"),
                        ("selector", "bind_idle_string=true"),
                        ("mission", "QB-6 live oxidizer under-clamped"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live O2 winning a 182 us race did not prevent an idle-string MODIFY; reversing order would still have been a wrong bind if the supervisor keyed on the leftover B selector.",
                    "Delayed (abort_s=540): 9 min working-solution dump. Named un-netted loss.",
                ],
            ),
            (
                "recovery",
                "MODIFY air 14.0 -> 7.2 Nm3/h on live string A; leave idle B parked; clear "
                "bind_idle_string.",
            ),
            (
                "cost",
                OrderedDict(
                    [
                        ("actual_live_o2_pct", 8.4),
                        ("actual_cap_pct", 6.0),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("air_nm3h", 7.2), ("string", "B")]),
                        ),
                        (
                            "cost",
                            "9 min working-solution dump (task/efficiency); live 8.4 percent "
                            "left over cap while idle B ate the clamp (safety of a false string).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "o2.live.pct (5.480 ms, 8.4 percent, string A)"),
                        ("loser", "o2.idle.pct (5.662 ms, 3.1 percent, string B)"),
                        ("margin_us", 182),
                        (
                            "counterfactual_if_reversed",
                            "Idle-first by < 182 us would still leave live 8.4 over cap; a "
                            "correct gate binds o2.live.pct to policy_air_live either way. The "
                            "wrong MODIFY spent the live win on an idle-string air cut.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6020),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong MODIFY (6.020 ms, tick 4). "
                "The 9 min dump is delayed surprise, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        30,
        96,
        32,
        92,
        routing(
            "thalamic-relay.ao-o2",
            "spikenaut.policy.air-idle",
            [
                ("relay_o2_idle", "policy_air_idle", 0.73),
                ("relay_o2_live", "policy_air_idle", 0.22),
            ],
            "acetylcholine",
            0.08,
            "wrong_string_stdp; ACh tags the (wrong) air_idle bind at the live-O2 win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 540),
                ("delayed_surprise_s", 540),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("air_idle", 42, 0.45, 280.0, 4),
                    pop("air_live", 42, 0.90),
                    pop("o2_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r67-352"),
            (
                "title",
                "WRONG-MODIFY at Quinone-Beck QB-6 / Oxidizer A: live O2 8.4 over cap; air cut "
                "on idle string B (wrong-string / live vs idle parallel bank)",
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
                    "Wrong-modify / wrong-string. Sidecar arithmetic live 8.4 > 6.0 is true "
                    "and executed.string != live_string; MODIFY bound idle B. "
                    "total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "hydrogen-peroxide-AO",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-string",
                        "live-vs-idle",
                        "parallel-bank",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live-first race can still be a wrong gate "
                    "when routing.table[0].to is policy_air_idle and executed.string is the idle "
                    "bank. Convictable from live_o2 vs cap and string A vs B without AO physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_353():
    ticks = [
        tick(2810, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(7040, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7218, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7900, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(8200, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(360000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("ft.butane.ctx", 1.420, 0.43),
        spike("ae.hotspot.pps", 2.880, 0.61),
        spike("tc.bed.C", 4.550, 0.49),
        spike("ae.hotspot.pps", 7.040, 1.34),
        spike("tc.bed.C", 7.218, 1.11),
        spike("ctrl.gate", 7.900, 1.02),
        spike("ae.hotspot.pps", 10.200, 0.78),
        spike("ft.butane.ctx", 14.800, 0.44),
        spike("tc.bed.C", 19.400, 0.58),
        spike("ctrl.gate", 24.600, 0.81),
        spike("ae.hotspot.pps", 31.200, 0.53),
        spike("tc.bed.C", 38.800, 0.46),
        spike("ft.butane.ctx", 44.100, 0.37),
    ]
    excerpt = independent_excerpt(67353, 128, 48000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Hot-spot AE on Maleic-Croft MC-HIL bed B-2 is 55 pulses/s against a 12 pps "
                "move cap, even though the bed TC still prints 412 C under a 430 C look. A "
                "18.0 kNm3/h air raise is armed. AE-first latches REJECT hold; TC-first would "
                "commit the raise on an under-read bed.",
            ),
            ("domain", "maleic-anhydride-FBR"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Do not raise air on bed B-2 unless hot-spot AE <= 12 pps; keep 0.0 kNm3/h "
                "delta until the injected bed recovers.",
            ),
            ("t0_us", 1756850400000353),
            ("gate_latency_us", 860),
            ("race_window_us", 290),
            ("race_window_rel_ms", [6.95, 7.24]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.hotspot.pps 55 pps",
                                "tc.bed.C 412 C under 430",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches REJECT hold 0.0 kNm3/h delta; TC-first would commit "
                            "an 18.0 -> 22.0 kNm3/h raise on an apparent 412 C under-read.",
                        ),
                        (
                            "window_derivation",
                            "290 us = one AE burst versus bed-TC integration on this n-butane "
                            "FBR HIL bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 178 us vs combined jitter 56 us (AE 24 + TC 32): 3.2x over a "
                            "2.0x trust floor. Pad injects the TC lamp 120-160 us before the AE "
                            "(geometric lag, not a sensor fault); the 412 C packet is still the "
                            "loser in this 290 us window.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "hot-spot AE puck, 5 kHz burst, 24 us jitter",
                    "bed thermocouple tree, 200 Hz, 32 us jitter",
                    "n-butane FT (context)",
                    "HIL lamp-spectrum monitor (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 12.0),
                        ("observed_ae_pps", 55.0),
                        ("bed_C", 412.0),
                        ("bed_look_C", 430.0),
                        ("proposed_air_knm3h", 22.0),
                        ("hold_air_knm3h", 18.0),
                        ("lamp_inject_lead_us", [120, 160]),
                    ]
                ),
            ),
            (
                "hil",
                OrderedDict(
                    [
                        (
                            "pad",
                            "Maleic-Croft MC-HIL n-butane fluid-bed mockup with physical air header",
                        ),
                        ("injected", "hot-spot AE burst + bed-TC lamp spectrum"),
                        (
                            "note",
                            "Hardware-in-the-loop maleic FBR. Invented plant; not a live n-butane oxidizer.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Bed B-2 on the MC-HIL pad; 18.0 -> 22.0 kNm3/h air raise armed.",
                    "2. TC lamp injected 120-160 us before AE sees 55 pps.",
                    "3. Butane-FT precursor at 1.420 ms.",
                    "4. Race window [6.950, 7.240] ms.",
                    "5. ae.hotspot.pps 55 at 7.040 ms (winner).",
                    "6. tc.bed.C 412 C at 7.218 ms (loser by 178 us).",
                    "7. Gate at 7.900 ms: REJECT hold 18.0 kNm3/h; do not raise to 22.0.",
                    "8. AE remains over 12 pps this cycle; raise cap held.",
                    "9. Bed re-fluidize queued on the pad.",
                    "10. Delayed (abort_s=360): 6 min AE retune and lamp-spectrum retune.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "raise_fbr_air"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_knm3h", 22.0),
                        ("hold", False),
                        ("tc_authoritative", True),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 55.0),
                        ("ae_cap_pps", 12.0),
                        ("bed_C", 412.0),
                        ("bed_look_C", 430.0),
                        ("race_margin_us", 178),
                        ("combined_jitter_us", 56),
                        ("abort_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 22.0 kNm3/h air because bed 412 C looks under the 430 C "
                "travel look, treating 55 pps AE as a noisy bus echo.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Hot-spot AE 55 pps is over the 12 pps air-raise cap. Bed 412 C is a HIL lamp "
                "under-read, not a clearance. REJECT: hold 18.0 kNm3/h; do not commit a 22.0 "
                "kNm3/h raise.",
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
                                    ("observed", 55.0),
                                    ("bed_C", 412.0),
                                ]
                            ),
                        ),
                        (
                            "air_knm3h",
                            OrderedDict([("proposed", 22.0), ("executed", 18.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 178),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 3.18),
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
            ("name", "hold_for_ae_drop"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_knm3h", 18.0),
                        ("hold", True),
                        ("tc_authoritative", False),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: hold 18.0 kNm3/h; 22.0 raise cancelled. AE 55 > 12 pps cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held bed B-2 at 18.0 kNm3/h. AE over cap this cycle; raise "
                "cap held. Bed-TC apparent was not treated as a hot-spot clearance.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("air", "held; 18.0 kNm3/h"),
                        ("ae", "still over 12 pps this cycle"),
                        ("bed_tc", "412 C unused as clearance"),
                        ("mission", "raise deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Geometric lag: TC lamp was injected 120-160 us before the AE puck, yet AE still won the 290 us race.",
                    "Delayed (abort_s=360): pad policy update forbids treating bed TC as a hot-spot substitute after a 6 min re-prime.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.hotspot.pps (7.040 ms, 55 pps)"),
                        ("loser", "tc.bed.C (7.218 ms, 412 C)"),
                        ("margin_us", 178),
                        (
                            "counterfactual_if_reversed",
                            "TC-first by < 178 us inside the 290 us window would have committed "
                            "a 22.0 kNm3/h raise with AE 55 > 12 pps cap. Order, not amplitude, selected the hold.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7900),
            (
                "reward_inflection_note",
                "Safety and coherence step up at the REJECT gate (7.900 ms, tick 4) as the hold "
                "lands. The 6 min re-prime is delayed surprise bound to abort_s=360.",
            ),
        ]
    )
    ras = raster_core(
        48,
        128,
        18,
        111,
        routing(
            "thalamic-relay.maleic-ae",
            "spikenaut.policy.air-hold",
            [
                ("relay_ae_pps", "policy_air_hold", 0.70),
                ("relay_bed_tc", "policy_tc_raise", 0.24),
            ],
            "dopamine",
            0.15,
            "ae_hold_stdp; DA tags the air_hold bind at the hot-spot AE win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("abort_s", 360),
                ("delayed_surprise_s", 360),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.29),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("air_hold", 70, 0.48, 250.0, 5),
                    pop("tc_raise", 50, 0.85),
                    pop("ae_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r67-353"),
            (
                "title",
                "Maleic-Croft MC-HIL / Bed B-2: hot-spot AE 55 pps beats bed TC 412 C by 178 us; "
                "correct REJECT holds the air raise",
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
                    "Correct REJECT. AE over cap beats TC under-read. "
                    "total 0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06. Tick 6 binds abort_s=360.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "maleic-anhydride-FBR",
                    [
                        "reject",
                        "hil",
                        "hotspot-ae",
                        "tc-underread",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a HIL bed-TC under-read losing a 178 us race does not clear a "
                    "hot-spot AE over-rate. Hold is distillable from pps vs cap.",
                    3,
                ),
            ),
        ]
    )


def record_354():
    ticks = [
        tick(3220, 0.05, 0.04, 0.02, 0.01, 0.01),
        tick(8120, 0.08, 0.05, 0.04, 0.03, 0.02),
        tick(8310, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(8520, 0.12, 0.09, 0.05, 0.04, 0.02),
        tick(8980, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(120000000, 0.03, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.feed.ctx", 1.105, 0.43),
        spike("iv.chip.opt", 3.220, 0.59),
        spike("tc.n2.C", 5.010, 0.50),
        spike("iv.chip.opt", 8.120, 1.27),
        spike("tc.n2.C", 8.310, 1.09),
        spike("ctrl.gate", 8.520, 0.97),
        spike("iv.chip.opt", 11.200, 0.78),
        spike("tc.n2.C", 14.880, 0.61),
        spike("ctrl.gate", 18.400, 0.84),
        spike("iv.chip.opt", 22.050, 0.56),
        spike("enc.feed.ctx", 24.100, 0.40),
    ]
    excerpt = independent_excerpt(67354, 52, 26000, 13, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("feed_t_h", 4.2),
            ("iv_opt", 0.82),
            ("n2_C", 168.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "SSP column S-8 at Ester-Wold EW-3 already holds IV 0.82 above the 0.80 floor "
                "with nitrogen 168 C under the 185 C chip-weld cap and a 4.2 t/h chip feed "
                "already filed under the 5.0 t/h ceiling. Nitrogen-first would extra-clamp a "
                "legal column; IV-first ACCEPTS the filed 4.2 t/h solid-state pass.",
            ),
            ("domain", "polyester-SSP-column"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Hold the 4.2 t/h chip feed while IV stays >= 0.80 and nitrogen stays <= "
                "185 C; do not extra-clamp a legal SSP column.",
            ),
            ("t0_us", 1756850400000354),
            ("gate_latency_us", 400),
            ("race_window_us", 460),
            ("race_window_rel_ms", [8.0, 8.46]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "iv.chip.opt 0.82 over 0.80 floor",
                                "tc.n2.C 168 C smear under 185 weld look",
                            ],
                        ),
                        (
                            "semantics",
                            "IV-first ACCEPTS the already-legal 4.2 t/h feed. Nitrogen-first "
                            "would extra-clamp because 168 C looks under a 185 C weld look.",
                        ),
                        (
                            "window_derivation",
                            "460 us = one IV-opt slot versus nitrogen-TC group delay on this "
                            "SSP skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 190 us vs combined jitter 66 us (IV 32 + TC 34): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 190 us inside the 460 us "
                            "window would have extra-clamped a legal 0.82 IV / 4.2 t/h pass.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "chip IV viscometer, 1 kHz, 32 us jitter",
                    "nitrogen thermocouple tree, 2 kHz, 34 us jitter",
                    "feed encoder (context)",
                    "column DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("iv_floor", 0.80),
                        ("observed_iv", 0.82),
                        ("n2_C", 168.0),
                        ("n2_cap_C", 185.0),
                        ("feed_cap_t_h", 5.0),
                        ("proposed_feed_t_h", 4.2),
                    ]
                ),
            ),
            (
                "simulation",
                OrderedDict(
                    [
                        (
                            "solver",
                            "plug-flow SSP + discrete-chip diffusion, seed 67354; 8-tube "
                            "column; NOT lumped-capacity, NOT U-RANS, NOT a wet-stand",
                        ),
                        (
                            "fidelity_limits",
                            "Rigid column shell; no chip-bridge motion. Raster is kernelized events, "
                            "not an independent LIF.",
                        ),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Column S-8 in pass; 4.2 t/h chip feed armed.",
                    "2. IV 0.82 over 0.80 floor; N2 168 C under 185 C weld; feed 4.2 under 5.0.",
                    "3. Encoder precursor at 1.105 ms.",
                    "4. Race window [8.000, 8.460] ms.",
                    "5. iv.chip.opt 0.82 at 8.120 ms (winner).",
                    "6. tc.n2.C 168 C at 8.310 ms (loser by 190 us).",
                    "7. Gate at 8.520 ms: ACCEPT 4.2 t/h; executed identical to proposed.",
                    "8. IV stays 0.821 > 0.80; feed 4.21 t/h < 5.0.",
                    "9. Nitrogen remaining a cabinet glint did not require an extra clamp.",
                    "10. Delayed (survey_s=120): 120 s IV coupon on tube 3.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_ssp_feed"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("iv_opt", 0.82),
                        ("iv_floor", 0.80),
                        ("n2_C", 168.0),
                        ("n2_cap_C", 185.0),
                        ("feed_cap_t_h", 5.0),
                        ("race_margin_us", 190),
                        ("combined_jitter_us", 66),
                        ("survey_s", 120),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 4.2 t/h feed: IV 0.82 is over the 0.80 "
                "floor and 4.2 t/h is under 5.0 t/h.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "IV 0.82 won by 190 us and is over the 0.80 floor. Nitrogen 168 C is a cabinet "
                "glint, not a weld miss. ACCEPT the filed 4.2 t/h feed. Executed identical to "
                "proposed. An extra clamp is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "iv_opt",
                            OrderedDict(
                                [
                                    ("floor", 0.80),
                                    ("observed", 0.82),
                                    ("executed_feed_t_h", 4.2),
                                ]
                            ),
                        ),
                        (
                            "n2_C",
                            OrderedDict([("cap", 185.0), ("observed", 168.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 190),
                                    ("combined_jitter_us", 66),
                                    ("ratio", 2.88),
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
            ("name", "hold_ssp_feed"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 4.2 t/h feed. IV 0.82 > 0.80 floor.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 4.2 t/h chip feed. IV stayed 0.821 over 0.80. "
                "Nitrogen remaining a cabinet glint was the losing channel and did not justify "
                "an extra clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held; 4.2 t/h"),
                        ("iv", "0.821 > 0.80"),
                        ("n2", "168 C glint unused as weld miss"),
                        ("chips", "pass continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Nitrogen TC 168 C losing a 190 us race did not predict a weld miss; reversing 190 us would have extra-clamped a legal 0.82 IV pass.",
                    "Delayed (survey_s=120): 120 s IV coupon on tube 3; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "iv.chip.opt (8.120 ms, 0.82)"),
                        ("loser", "tc.n2.C (8.310 ms, 168 C)"),
                        ("margin_us", 190),
                        (
                            "counterfactual_if_reversed",
                            "Nitrogen-first by < 190 us inside the 460 us window would have extra-clamped "
                            "a legal pass. IV-first confirms the filed feed.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 8520),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (8.520 ms, tick 4). The 120 s IV coupon "
                "is delayed surprise bound to survey_s=120, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        26,
        52,
        44,
        59,
        routing(
            "thalamic-relay.ssp-iv",
            "spikenaut.policy.feed-accept",
            [
                ("relay_iv_opt", "policy_feed_accept", 0.66),
                ("relay_n2_tc", "policy_extra_clamp", 0.23),
            ],
            "serotonin",
            0.12,
            "ssp_confirm_stdp; 5-HT tags the feed_accept bind at the IV win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 120),
                ("delayed_surprise_s", 120),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.46),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("feed_accept", 50, 0.50, 175.0, 4),
                    pop("extra_clamp", 40, 0.85, 40.0, 1),
                    pop("n2_veto", 22, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r67-354"),
            (
                "title",
                "Ester-Wold EW-3 / Column S-8: IV 0.82 beats nitrogen 168 C by 190 us; "
                "ACCEPT already-legal 4.2 t/h SSP chip feed",
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
                    "Clean ACCEPT of an already-legal SSP chip feed. "
                    "total 1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08. Tick 6 binds survey_s=120.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "polyester-SSP-column",
                    [
                        "accept",
                        "simulated",
                        "iv-vs-n2",
                        "feed-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging nitrogen TC losing a 190 us race does not require an "
                    "extra clamp when chip IV is already over the floor.",
                    4,
                ),
            ),
        ]
    )


def record_355():
    ticks = [
        tick(1980, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5120, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(5300, 0.08, 0.05, 0.03, 0.02, 0.01),
        tick(5480, 0.12, 0.09, 0.06, 0.04, 0.02),
        tick(6020, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(240000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.pull.ctx", 0.880, 0.44),
        spike("tc.crown.C", 1.980, 0.61),
        spike("ir.throat.C", 3.410, 0.52),
        spike("tc.crown.C", 5.120, 1.30),
        spike("ir.throat.C", 5.300, 1.12),
        spike("ctrl.gate", 5.480, 0.99),
        spike("tc.crown.C", 8.050, 0.77),
        spike("ir.throat.C", 11.400, 0.58),
        spike("ctrl.gate", 14.900, 0.83),
        spike("tc.crown.C", 18.200, 0.54),
        spike("enc.pull.ctx", 21.100, 0.39),
    ]
    excerpt = independent_excerpt(67355, 84, 22000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("pull_t_d", 38.0),
            ("crown_C", 1540.0),
            ("throat_C", 1320.0),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Tank T-1 at Duran-Gill DG-5 already holds crown 1540 C under a 1580 C silica "
                "cap with a 38 t/d pull already filed under 44 t/d. Throat-IR-first would "
                "extra-clamp a legal tank; crown-first ACCEPTS the filed 38 t/d borosilicate "
                "pull.",
            ),
            ("domain", "borosilicate-tank-furnace"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold the 38 t/d pull while crown stays <= 1580 C and pull stays <= 44 t/d; "
                "do not extra-clamp a legal tank.",
            ),
            ("t0_us", 1756850400000355),
            ("gate_latency_us", 360),
            ("race_window_us", 320),
            ("race_window_rel_ms", [5.05, 5.37]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.crown.C 1540 under 1580",
                                "ir.throat.C 1320 smear under 1400 look",
                            ],
                        ),
                        (
                            "semantics",
                            "Crown-first ACCEPTS the already-legal 38 t/d pull. Throat-first would "
                            "extra-clamp because 1320 C looks under a 1400 C throat look.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one crown-TC slot versus throat-IR group delay on this "
                            "tank skid bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (TC 26 + IR 32): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have extra-clamped a legal 1540 C / 38 t/d pass.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "crown thermocouple tree, 4 kHz, 26 us jitter",
                    "throat IR pyrometer, 1 kHz, 32 us jitter",
                    "pull encoder (context)",
                    "regenerator DP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("crown_cap_C", 1580.0),
                        ("observed_crown_C", 1540.0),
                        ("throat_C", 1320.0),
                        ("pull_cap_t_d", 44.0),
                        ("proposed_pull_t_d", 38.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Tank T-1 in pass; 38 t/d pull armed.",
                    "2. Crown 1540 C under 1580 C silica; pull 38 under 44 t/d.",
                    "3. Pull precursor at 0.880 ms.",
                    "4. Race window [5.050, 5.370] ms.",
                    "5. tc.crown.C 1540 at 5.120 ms (winner).",
                    "6. ir.throat.C 1320 at 5.300 ms (loser by 180 us).",
                    "7. Gate at 5.480 ms: ACCEPT 38 t/d; executed identical to proposed.",
                    "8. Crown stays 1542 C < 1580; pull 38.1 t/d < 44.",
                    "9. Throat remaining a port glint did not require an extra clamp.",
                    "10. Delayed (survey_s=240): 4 min seed-bubble sample on the working end.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_tank_pull"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("crown_C", 1540.0),
                        ("crown_cap_C", 1580.0),
                        ("throat_C", 1320.0),
                        ("pull_cap_t_d", 44.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes keeping the filed 38 t/d pull: crown 1540 C is under the "
                "1580 C silica cap and 38 t/d is under 44 t/d.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Crown 1540 C won by 180 us and is under the 1580 C silica cap. Throat 1320 C "
                "is a port glint, not a pull miss. ACCEPT the filed 38 t/d pull. Executed "
                "identical to proposed. An extra clamp is not indicated.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "crown_C",
                            OrderedDict(
                                [
                                    ("cap", 1580.0),
                                    ("observed", 1540.0),
                                    ("executed_pull_t_d", 38.0),
                                ]
                            ),
                        ),
                        (
                            "throat_C",
                            OrderedDict([("look", 1400.0), ("observed", 1320.0)]),
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
            ("name", "hold_tank_pull"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: executed identical to proposed 38 t/d pull. Crown 1540 < 1580 cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT kept the filed 38 t/d pull. Crown stayed 1542 C under 1580. "
                "Throat remaining a port glint was the losing channel and did not justify an "
                "extra clamp.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("pull", "held; 38 t/d"),
                        ("crown", "1542 C < 1580"),
                        ("throat", "1320 C glint unused as pull miss"),
                        ("tank", "pass continues"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Throat IR 1320 C losing a 180 us race did not predict a pull miss; reversing 180 us would have extra-clamped a legal 1540 C tank.",
                    "Delayed (survey_s=240): 4 min seed-bubble sample on the working end; not a safety inflection.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.crown.C (5.120 ms, 1540 C)"),
                        ("loser", "ir.throat.C (5.300 ms, 1320 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Throat-first by < 180 us inside the 320 us window would have extra-clamped "
                            "a legal pull. Crown-first confirms the filed 38 t/d.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5480),
            (
                "reward_inflection_note",
                "Heads rise at the ACCEPT (5.480 ms, tick 4). The 4 min seed-bubble sample "
                "is delayed surprise bound to survey_s=240, not the inflection.",
            ),
        ]
    )
    ras = raster_core(
        22,
        84,
        26,
        48,
        routing(
            "thalamic-relay.crown-tc",
            "spikenaut.policy.pull-accept",
            [
                ("relay_crown_C", "policy_pull_accept", 0.69),
                ("relay_throat_IR", "policy_extra_clamp", 0.21),
            ],
            "octopamine",
            0.05,
            "crown_confirm_stdp; octopamine tags the pull_accept bind at the crown-TC win",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_s", 240),
                ("delayed_surprise_s", 240),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.32),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("pull_accept", 45, 0.50, 210.0, 3),
                    pop("extra_clamp", 40, 0.85, 40.0, 1),
                    pop("throat_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r67-355"),
            (
                "title",
                "Duran-Gill DG-5 / Tank T-1: crown 1540 C beats throat IR 1320 C by 180 us; "
                "ACCEPT already-legal 38 t/d borosilicate pull",
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
                    "Clean ACCEPT of an already-legal borosilicate pull. "
                    "total 1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08. Tick 6 binds survey_s=240.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "borosilicate-tank-furnace",
                    [
                        "accept",
                        "designed",
                        "crown-vs-throat",
                        "pull-legal",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a lagging throat IR losing a 180 us race does not require an "
                    "extra clamp when crown temperature is already under the silica cap.",
                    5,
                ),
            ),
        ]
    )

