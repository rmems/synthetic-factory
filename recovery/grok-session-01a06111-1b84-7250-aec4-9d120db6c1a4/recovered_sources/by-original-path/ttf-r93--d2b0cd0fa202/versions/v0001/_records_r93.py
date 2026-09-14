def lif_481_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.42
    stim = (22000, 25000)
    seed = 93481
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
    leak = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + leak, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.basket" for t, _ in picked]
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
            ("seed", 93481),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 ADN-feed clamp bias; stim 22-25 ms is the basket leak.",
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


def record_481():
    excerpt, extra = lif_481_excerpt()
    ticks = [
        tick(2080, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5200, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5380, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5900, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22400, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    spikes = [
        spike("pt.h2.bar", 1.040, 0.41),
        spike("tc.bed.C", 2.080, 0.58),
        spike("pt.h2.bar", 3.400, 0.50),
        spike("tc.bed.C", 5.200, 1.31),
        spike("pt.h2.bar", 5.380, 1.12),
        spike("ctrl.gate", 5.900, 0.97),
        spike("tc.bed.C", 8.100, 0.82),
        spike("pt.h2.bar", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.basket.leak", 22.400, 1.48),
        spike("ae.basket.leak", 24.100, 0.93),
        spike("pt.h2.bar", 30.200, 0.40),
        spike("tc.bed.C", 36.400, 0.55),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Diamine-Law DL-7 hydrogenator H-4 is sitting on 186 C bed metal against a 172 C "
                "hard stop while recycle hydrogen remains a legal 18.4 bar versus 24.0. "
                "Adiponitrile must drop 14.0 t/h to 8.2 because the bed is the over-cap channel; "
                "a hydrogen-header hold would keep cruise. A catalyst basket already torn on the "
                "pass stays dark until AE dumps.",
            ),
            ("domain", "hexamethylenediamine-hydrogenator"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep H-4 bed outlet <= 172 C and finish the HMD pass without dumping "
                "adiponitrile through a torn catalyst basket.",
            ),
            ("t0_us", 1756850400000481),
            ("gate_latency_us", 700),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.200, 5.560]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "tc.bed.C 186 over 172 cap",
                                "pt.h2.bar 18.4 with header under 24.0",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first latches ADN clamp 14.0 -> 8.2 t/h; hydrogen-first keeps 14.0 "
                            "on a 'still under header-cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one bed-TC slot versus the hydrogen-header PT publisher "
                            "on this HMD hydrogenator bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (bed 28 + hydrogen 34): 2.90x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 14.0 t/h; predicted next-sample 178 C "
                            "> 172 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "catalyst-bed TC, 2 kHz, 28 us jitter",
                    "recycle-hydrogen PT, 1 kHz, 34 us jitter",
                    "basket AE puck (context)",
                    "adiponitrile feed Coriolis (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 172.0),
                        ("observed_bed_C", 186.0),
                        ("adn_tph", 14.0),
                        ("h2_bar", 18.4),
                        ("h2_cap_bar", 24.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. H-4 indexed on Diamine-Law DL-7; ADN 14.0 t/h; bed 186 C.",
                    "2. Hydrogen 18.4 bar under 24.0 cap; HMD pass armed.",
                    "3. Hydrogen-PT precursor at 1.040 ms.",
                    "4. Race window [5.200, 5.560] ms.",
                    "5. tc.bed.C 186 at 5.200 ms (winner).",
                    "6. pt.h2.bar 18.4 at 5.380 ms (loser by 180 us).",
                    "7. Gate at 5.900 ms: MODIFY clamp ADN 14.0 -> 8.2 t/h.",
                    "8. After clamp bed 168 C <= 172; hydrogen still 18.4 bar.",
                    "9. At 22.400 ms a catalyst basket dumps 0.3 t ADN.",
                    "10. 15 min pass isolate (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_adn_feed"),
            (
                "parameters",
                OrderedDict(
                    [("adn_tph", 14.0), ("bed_C", 186.0), ("h2_bar", 18.4)]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 186.0),
                        ("bed_cap_C", 172.0),
                        ("predicted_unclamped_next_C", 178.0),
                        ("adn_tph", 14.0),
                        ("h2_bar", 18.4),
                        ("h2_cap_bar", 24.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 14.0 t/h ADN because hydrogen 18.4 bar is under 24.0, treating "
                "the 186 C bed as a still-wet TC rather than an outlet-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed outlet 186 C won by 180 us, so the hydrogenator is off-spec, not still "
                "a hydrogen-header story. Holding 14.0 t/h predicts next-sample 178 C > 172 "
                "cap. MODIFY: ADN 14.0 -> 8.2 t/h. Observed after clamp 168 C <= 172. "
                "A full REJECT is not indicated: a clean HMD pass accepts 8.2 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 172.0),
                                    ("observed", 186.0),
                                    ("predicted_unclamped_next", 178.0),
                                    ("clamped_adn_tph", 8.2),
                                    ("observed_after_clamp", 168.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 180), ("combined_jitter_us", 62), ("ratio", 2.9)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "clamped_adn_feed"),
            (
                "parameters",
                OrderedDict(
                    [("adn_tph", 8.2), ("bed_C", 168.0), ("h2_bar", 18.4)]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: ADN 14.0 -> 8.2 t/h. Process-correct vs the 172 C bed cap. "
                "Basket still leaks at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held bed outlet at 168 C. At 22.400 ms a catalyst "
                "basket already seated on the pass dumped 0.3 t of adiponitrile. Clamp "
                "reduced dump energy; it did not prevent the leak. Partnered negative: process "
                "heads stay honest; world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("bed", "clamp executed; peak 168 C <= 172 cap"),
                        ("basket", "leaked at 22.400 ms; 0.3 t ADN"),
                        ("repair", "15 min pass isolate (abort_s=900)"),
                        ("mission", "DL-7 HMD pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither bed TC nor hydrogen PT predicted the seated basket leak; ae.basket.leak is a new channel at 22.400 ms, 16.500 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min pass isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min pass isolate after the basket leak. Safety head -0.60 prices the dump; "
                "task_progress stays +0.32 because the ADN clamp completed under the 172 C "
                "cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.bed.C (5.200 ms, 186 C)"),
                        ("loser", "pt.h2.bar (5.380 ms, 18.4 bar)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Hydrogen-first by < 180 us inside the 360 us window would have kept "
                            "14.0 t/h; predicted next-sample 178 C would have missed "
                            "the 172 cap even without the leak. The MODIFY is still the correct "
                            "process. The leak is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms basket leak (tick t_us=22400), inside the "
                "42 ms raster. The correct MODIFY at 5.900 ms is in the same excerpt. Do not "
                "put inflection on the abort_s=900 isolation tick.",
            ),
            ("delayed_surprise_s", 900),
        ]
    )
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.diamine-bed",
            "spikenaut.policy.adn-clamp",
            [
                ("relay.tc.bed", "policy.adn_clamp", 0.68),
                ("relay.pt.h2", "policy.header_hold", 0.29),
                ("relay.ae.basket", "policy.adn_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at bed win (5.200 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.400 ms basket leak",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("adn_clamp", 50, 0.5, 220.0, 0.36),
                    pop_budget("header_hold", 40, 0.8, 50.0, 0.36),
                    pop("leak_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r93-481",
        "Diamine-Law DL-7 / Hydrogenator H-4: bed 186 C beats hydrogen header by 180 us; correct "
        "MODIFY still eats an in-window basket leak (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the 42 ms "
        "raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named pass isolate "
        "(abort_s=900) is not netted into task_progress.",
        ras,
        gate,
        "hexamethylenediamine-hydrogenator",
        [
            "modify",
            "partnered-negative-total",
            "independent-lif-raster",
            "sidecar-sim-only",
            "in-window-world-charge",
            "designed",
        ],
        "A critic can see the world-charge as a LIF burst inside the raster while process "
        "heads stay honest. Credit assignment is spikes, not prose across a 15 min pass isolate.",
        1,
    )


def record_482():
    ticks = [
        tick(2240, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5600, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5780, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(6120, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6460, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("enc.tph.cmd", 1.120, 0.42),
        spike("ft.live.tph", 2.240, 0.57),
        spike("enc.tph.cmd", 3.500, 0.49),
        spike("ft.live.tph", 5.600, 1.29),
        spike("zt.valve.pct", 5.780, 1.10),
        spike("ctrl.gate", 6.120, 0.96),
        spike("ft.live.tph", 8.400, 0.80),
        spike("enc.tph.cmd", 10.400, 0.63),
        spike("ctrl.gate", 12.600, 0.84),
        spike("ft.live.tph", 16.600, 0.41),
        spike("zt.valve.pct", 22.200, 0.54),
        spike("ft.live.tph", 26.400, 0.38),
    ]
    excerpt = independent_excerpt(93482, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Acetate-Glen AG-3 Tishchenko kettle K-8 already holds acetaldehyde at 8.4 t/h "
                "inside an 11.0 t/h envelope, but the feed-valve stem still prints 84 percent "
                "open. Binding the live Coriolis is the ACCEPT; treating stem travel as mass-flow "
                "via a leftover 0.2 t/h-per-percent orifice scale invents a 16.8 t/h over-cap.",
            ),
            ("domain", "ethyl-acetate-tishchenko"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the AG-3 ethyl-acetate make with live acetaldehyde <= 11.0 t/h and leave "
                "the feed valve where the Coriolis already says it is legal.",
            ),
            ("t0_us", 1756850400000482),
            ("gate_latency_us", 520),
            ("race_window_us", 340),
            ("race_window_rel_ms", [5.600, 5.940]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.live.tph 8.4 t/h on LIVE Coriolis",
                                "zt.valve.pct 84 percent stem travel",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-Coriolis-first should ACCEPT the already-legal 8.4 t/h; stem-first "
                            "is a false over-cap if travel is scaled as mass-flow.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live-FT slot versus the valve-travel ZT publisher on this "
                            "Tishchenko kettle dual-PV bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (live 28 + stem 32). Order is "
                            "correctly live-Coriolis-first. The error is binding stem travel as PV, "
                            "not the live magnitude: 8.4 t/h is under the 11.0 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "acetaldehyde Coriolis, 2 kHz, 28 us jitter, tag=ALD_FT.LIVE status=LIVE",
                    "feed-valve ZT, 1 kHz, 32 us jitter, tag=FV_ZT.STEM pct=84 scale_tph_per_pct=0.2 leftover",
                    "kettle pressure PT (context)",
                    "ethyl-acetate GC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cap_tph", 11.0),
                        ("live_tph", 8.4),
                        ("valve_pct", 84.0),
                        ("travel_as_flow_tph", 16.8),
                        ("scale_tph_per_pct", 0.2),
                        ("live_status", "LIVE"),
                        ("valve_status", "LIVE"),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. K-8 already making ethyl acetate; live 8.4 t/h acetaldehyde.",
                    "2. Stem 84 percent; leftover 0.2 t/h-per-percent scale still configured.",
                    "3. Encoder precursor at 1.120 ms.",
                    "4. Race window [5.600, 5.940] ms.",
                    "5. ft.live.tph 8.4 t/h at 5.600 ms (winner).",
                    "6. zt.valve.pct 84 at 5.780 ms (loser by 180 us).",
                    "7. Gate at 6.120 ms: WRONG-MODIFY binds stem travel as PV.",
                    "8. Acetaldehyde cut 8.4 -> 3.2 t/h; live Coriolis left unused as authority.",
                    "9. Kettle starves; aldol byproduct rises.",
                    "10. Delayed (abort_s=720): 12 min Tishchenko dump while feed is starved.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_acetaldehyde"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("acetaldehyde_tph", 8.4),
                        ("valve_pct", 84.0),
                        ("bind_valve_travel", False),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_tph", 8.4),
                        ("cap_tph", 11.0),
                        ("valve_pct", 84.0),
                        ("travel_as_flow_tph", 16.8),
                        ("scale_tph_per_pct", 0.2),
                        ("live_status", "LIVE"),
                        ("valve_status", "LIVE"),
                        ("t_gate_us", 6120),
                        ("correct_gate", "ACCEPT"),
                        ("correct_acetaldehyde_tph", 8.4),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 8.4 t/h acetaldehyde because live Coriolis is under "
                "the 11.0 t/h cap, treating the 84 percent stem as valve travel rather than mass-flow.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Stem 84 percent times leftover 0.2 t/h-per-percent equals 16.8 t/h, which exceeds "
                "the 11.0 cap (true only if travel is mass-flow). Cut acetaldehyde 8.4 -> 3.2 t/h "
                "because FV_ZT.STEM is the highlighted tag. Leave live Coriolis unused as authority.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "flow",
                            OrderedDict(
                                [
                                    ("cap_tph", 11.0),
                                    ("live_tph", 8.4),
                                    ("travel_as_flow_tph", 16.8),
                                    ("executed_acetaldehyde_tph", 3.2),
                                    ("correct_acetaldehyde_tph", 8.4),
                                    ("correct_gate", "ACCEPT"),
                                ]
                            ),
                        ),
                        (
                            "travel_bind",
                            OrderedDict(
                                [
                                    ("t_gate_us", 6120),
                                    ("bind_valve_travel", True),
                                    ("valve_pct", 84.0),
                                    ("scale_tph_per_pct", 0.2),
                                    ("live_status", "LIVE"),
                                    ("valve_status", "LIVE"),
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
            ("name", "cut_on_stem_travel"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("acetaldehyde_tph", 3.2),
                        ("valve_pct", 84.0),
                        ("bind_valve_travel", True),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / valve-travel as PV): 3.2 t/h cut applied because 84 percent "
                "stem times leftover 0.2 t/h-per-percent was treated as 16.8 t/h live flow. "
                "Routing relay.zt.travel -> policy.travel_clamp; no positive weight to policy.live_hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY cut acetaldehyde on a legal Tishchenko kettle. Live 8.4 t/h was under "
                "the 11.0 t/h cap at t_gate; 84 percent stem is valve travel, not mass-flow. "
                "12 min kettle dump (abort_s=720). Correct gate was ACCEPT; leave acetaldehyde at "
                "8.4 t/h and bind_valve_travel=false at t_gate_us=6120.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "acetaldehyde slammed 8.4 -> 3.2 t/h; Coriolis left unused"),
                        ("stem", "84 percent treated as 16.8 t/h via leftover 0.2 scale"),
                        ("dump", "12 min Tishchenko dump, aldol byproduct up"),
                        ("mission", "ethyl-acetate make deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-Coriolis-first was the correct order and the live t/h was under cap; the MODIFY spent that win on a stem-as-flow cut.",
                    "Delayed (abort_s=720): AG-3 holds 12 min while K-8 is starved and re-lined; next make 14 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT; leave acetaldehyde_tph=8.4 at t_gate_us=6120; bind_valve_travel=false; leave valve_pct=84 as travel only.",
                        ),
                        ("correct_actuator", "ALD_FT.LIVE"),
                        ("wrong_pv", "FV_ZT.STEM"),
                        ("t_gate_us", 6120),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("acetaldehyde_tph", 3.2),
                                    ("bind_valve_travel", True),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min Tishchenko dump (task/efficiency); live acetaldehyde never crossed 11.0 t/h while the cut was spent on stem travel as PV.",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.live.tph (5.600 ms, 8.4 t/h LIVE)"),
                        ("loser", "zt.valve.pct (5.780 ms, 84 percent stem)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Stem-first by < 180 us would still be valve travel, not mass-flow; "
                            "a correct gate binds ft.live.tph to policy.live_hold at t_gate either "
                            "way. The wrong MODIFY spent the live win on a stem-as-PV cut.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6120),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the stem-as-PV cut (6.120 ms, tick 4). "
                "The 12 min Tishchenko dump is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 720),
        ]
    )
    ras = raster_core(
        28,
        88,
        34,
        84,
        routing(
            "thalamic-relay.tishchenko-travel",
            "spikenaut.policy.travel-clamp",
            [
                ("relay.zt.travel", "policy.travel_clamp", 0.74),
                ("relay.ft.live", "policy.travel_clamp", 0.21),
            ],
            "acetylcholine",
            0.08,
            "travel_stdp; ACh tags the (wrong) stem-as-PV cut at the live Coriolis win",
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
            ("decision_window_ms", 0.34),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("travel_clamp", 48, 0.45, 300.0, 0.34),
                    pop("live_hold", 48, 0.90),
                    pop("travel_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r93-482",
        "WRONG-MODIFY at Acetate-Glen AG-3 / Kettle K-8: live 8.4 t/h read correctly; "
        "stem 84 percent treated as 16.8 t/h (valve-travel as PV)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-modify / valve-travel as PV. Sidecar arithmetic 8.4 < 11.0 on live t/h is "
        "true; MODIFY bound to travel_clamp. total -0.68 = -0.22 + -0.24 + -0.18 + -0.10 + 0.06.",
        ras,
        gate,
        "ethyl-acetate-tishchenko",
        [
            "modify",
            "wrong-gate",
            "valve-travel",
            "stem-as-pv",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live-Coriolis-first race can still be a wrong gate when the "
        "MODIFY treats stem travel as mass-flow. Convictable from live_tph vs cap_tph, "
        "valve_pct, bind_valve_travel, and routing without Tishchenko physics.",
        2,
        supervisor_error_type="wrong-modify",
    )
