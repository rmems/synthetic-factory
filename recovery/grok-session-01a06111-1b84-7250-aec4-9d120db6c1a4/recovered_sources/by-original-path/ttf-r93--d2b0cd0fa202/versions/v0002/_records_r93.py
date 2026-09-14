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


def record_483():
    ticks = [
        tick(2736, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6840, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7020, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7640, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(7960, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("ir.slurry.C", 1.360, 0.40),
        spike("ae.imp.pps", 2.736, 0.56),
        spike("ir.slurry.C", 4.100, 0.48),
        spike("ae.imp.pps", 6.840, 1.34),
        spike("ir.slurry.C", 7.020, 1.11),
        spike("ctrl.gate", 7.640, 0.98),
        spike("ae.imp.pps", 10.400, 0.81),
        spike("ir.slurry.C", 14.800, 0.62),
        spike("ctrl.gate", 18.200, 0.84),
        spike("ae.imp.pps", 28.400, 0.52),
        spike("ir.slurry.C", 36.100, 0.39),
        spike("ae.imp.pps", 42.200, 0.44),
    ]
    excerpt = independent_excerpt(93483, 120, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Silica-Leat QM-HIL precipitator R-6 is throwing 48 acoustic pulses per second "
                "against a 12 pps hush floor even though slurry IR is a cool 74 C of 95. "
                "The 7.2 t/h silicate dispatch has to stay parked; an IR-trusting go would light a "
                "rattling impeller. This HIL stand does not inherit plant-furnace current as authority.",
            ),
            ("domain", "precipitated-silica-reactor"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep R-6 from dispatching a growling silicate impeller while slurry IR remains under "
                "its own cap.",
            ),
            ("t0_us", 1756850400000483),
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
                                "ae.imp.pps 48 over 12 cap",
                                "ir.slurry.C 74 under 95 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; IR-first dispatches 7.2 t/h silicate on a 'slurry still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one AE puck slot versus the slurry-IR publisher on this HIL silica-precipitator bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + IR 32): 3.10x over a "
                            "2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have dispatched 7.2 t/h into a growling impeller.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "impeller AE puck, 50 kHz, 26 us jitter",
                    "slurry IR pyrometer, 1 kHz, 32 us jitter",
                    "silicate feed Coriolis (context)",
                    "sulfuric acid FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 12.0),
                        ("observed_ae_pps", 48.0),
                        ("slurry_C", 74.0),
                        ("slurry_cap_C", 95.0),
                        ("proposed_silicate_tph", 7.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. R-6 HIL indexed; 7.2 t/h silicate armed.",
                    "2. Slurry 74 C under 95; AE 48 pps over 12.",
                    "3. IR precursor at 1.360 ms.",
                    "4. Race window [6.840, 7.160] ms.",
                    "5. ae.imp.pps 48 at 6.840 ms (winner).",
                    "6. ir.slurry.C 74 at 7.020 ms (loser by 180 us).",
                    "7. Gate at 7.640 ms: REJECT hold, do not dispatch.",
                    "8. Silicate 0 t/h; slurry left at 74 C.",
                    "9. Impeller inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min precipitator reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_silicate"),
            (
                "parameters",
                OrderedDict([("silicate_tph", 7.2), ("hold", False), ("slurry_C", 74.0)]),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 48.0),
                        ("ae_cap_pps", 12.0),
                        ("slurry_C", 74.0),
                        ("slurry_cap_C", 95.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 7.2 t/h silicate because slurry 74 C is under 95, treating the "
                "48 pps AE as mixer hash rather than a growling impeller.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Impeller AE 48 pps won by 180 us, so the precipitator is growling, not still "
                "a slurry-IR story. 74 C is under 95 and does not authorize dispatch. REJECT: "
                "hold silicate 7.2 -> 0 t/h. A MODIFY that only trims feed would leave the growl.",
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
                                    ("observed", 48.0),
                                    ("executed_silicate_tph", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 180), ("combined_jitter_us", 58), ("ratio", 3.1)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_precipitator"),
            (
                "parameters",
                OrderedDict([("silicate_tph", 0.0), ("hold", True), ("slurry_C", 74.0)]),
            ),
            (
                "gate_effect",
                "REJECT: silicate 7.2 -> 0 t/h. Slurry IR left at 74 C under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held R-6. AE 48 pps beat slurry 74 C by 180 us. IR was legal; "
                "the impeller was not. 8 min precipitator reset (abort_s=480) is delayed survey, not a "
                "process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held at 0 t/h silicate"),
                        ("slurry", "left 74 C < 95 cap"),
                        ("impeller", "8 min precipitator reset (abort_s=480)"),
                        ("mission", "HIL silica not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Slurry IR never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min precipitator reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.imp.pps (6.840 ms, 48 pps)"),
                        ("loser", "ir.slurry.C (7.020 ms, 74 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 180 us inside the 320 us window would have "
                            "dispatched 7.2 t/h into a growling silicate impeller. The REJECT is still "
                            "the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7640),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.640 ms, tick 4). The 8 min precipitator "
                "reset is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480),
        ]
    )
    ras = raster_core(
        46,
        120,
        20,
        110,
        routing(
            "thalamic-relay.silica-ae",
            "spikenaut.policy.silica-hold",
            [
                ("relay.ae.imp", "policy.silica_hold", 0.70),
                ("relay.ir.slurry", "policy.ir_go", 0.24),
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
            ("decision_window_ms", 0.32),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop_budget("silica_hold", 56, 0.45, 280.0, 0.32),
                    pop("ir_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r93-483",
        "Silica-Leat QM-HIL / Precipitator R-6: impeller AE 48 pps beats slurry IR 74 C by 180 us; "
        "correct REJECT holds silicate",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 48 > 12 cap beats legal slurry IR. total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "precipitated-silica-reactor",
        ["reject", "hil", "ae-vs-ir", "growling-impeller", "tick6-sidecar-bound"],
        "Teaches that a legal slurry-IR header can lose to impeller AE inside a 320 us "
        "window; reversing 180 us would have dispatched a growling silica precipitator.",
        3,
    )


def record_484():
    ticks = [
        tick(2880, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(7200, 0.08, 0.06, 0.04, 0.02, 0.02),
        tick(7380, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(7840, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(8200, 0.04, 0.04, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.02, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("tc.tank.C", 1.200, 0.40),
        spike("ph.slurry.eu", 2.880, 0.55),
        spike("tc.tank.C", 4.400, 0.48),
        spike("ph.slurry.eu", 7.200, 1.26),
        spike("tc.tank.C", 7.380, 1.08),
        spike("ctrl.gate", 7.840, 0.95),
        spike("ph.slurry.eu", 11.200, 0.78),
        spike("tc.tank.C", 14.800, 0.60),
        spike("ctrl.gate", 18.400, 0.82),
        spike("ph.slurry.eu", 22.600, 0.50),
        spike("tc.tank.C", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(93484, 48, 28000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("slurry_tph", 6.4),
            ("ph_eu", 11.2),
            ("tank_C", 52.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Precursor-Moss PM-4 coprecip tank T-2 shows slurry pH parked at 11.2 of "
                "an 11.8 drop-out with tank water at 52 C of a 70 C stop. The 6.4 t/h "
                "sulfate add is already inside both envelopes; a tank-only story would idle "
                "a quiet NMC batch.",
            ),
            ("domain", "nmc-precursor-coprecip"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Finish the PM-4 coprecip batch with pH <= 11.8 and tank <= 70 C.",
            ),
            ("t0_us", 1756850400000484),
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
                                "ph.slurry.eu 11.2 under 11.8 trip",
                                "tc.tank.C 52 under 70 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "pH-first confirms the already-legal 6.4 t/h sulfate feed; tank-first "
                            "would have treated the probe as a runaway echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one pH-probe slot versus the tank-TC publisher on this simulated NMC coprecip bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (pH 26 + TC 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us would not make the "
                            "proposed sulfate feed illegal; it would only have delayed confirmation.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "slurry pH probe, 26 us jitter",
                    "tank TC well, 32 us jitter",
                    "sulfate Coriolis (context)",
                    "D50 laser (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ph_cap_eu", 11.8),
                        ("observed_ph_eu", 11.2),
                        ("tank_cap_C", 70.0),
                        ("observed_tank_C", 52.0),
                        ("d50_um", 8.4),
                        ("d50_cap_um", 12.0),
                        ("proposed_slurry_tph", 6.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. T-2 indexed on Precursor-Moss PM-4; 6.4 t/h sulfate armed.",
                    "2. Caps: pH 11.8, tank 70 C, D50 12 um.",
                    "3. Tank-TC precursor at 1.200 ms.",
                    "4. Race window [7.200, 7.560] ms.",
                    "5. ph.slurry.eu 11.2 at 7.200 ms (winner).",
                    "6. tc.tank.C 52 at 7.380 ms (loser by 180 us).",
                    "7. Gate at 7.840 ms: ACCEPT 6.4 t/h already legal.",
                    "8. Sulfate continues; no extra hold.",
                    "9. 6 min survey confirms pH still under 11.8.",
                    "10. QA: ACCEPT params identical to proposed.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "feed_sulfate_64"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ph_eu", 11.2),
                        ("ph_cap_eu", 11.8),
                        ("tank_C", 52.0),
                        ("tank_cap_C", 70.0),
                        ("d50_um", 8.4),
                        ("d50_cap_um", 12.0),
                        ("slurry_tph", 6.4),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("survey_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes a 6.4 t/h sulfate feed because pH 11.2 is under "
                "11.8 and tank 52 C is under 70 C.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "pH 11.2 won by 180 us and is under 11.8. Tank 52 C is under 70 C. "
                "D50 8.4 um is under 12. ACCEPT the already-legal sulfate feed.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "ph_eu",
                            OrderedDict(
                                [
                                    ("cap", 11.8),
                                    ("observed", 11.2),
                                    ("executed_slurry_tph", 6.4),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 180), ("combined_jitter_us", 58), ("ratio", 3.1)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "feed_sulfate_64"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: 6.4 t/h sulfate and 11.2 pH unchanged. Routing relay.ph.slurry -> policy.nmc_go.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left T-2 on a 6.4 t/h / 11.2 pH sulfate feed. Tank "
                "hitch did not justify a hold. 6 min survey confirmed pH still under 11.8.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "still 6.4 t/h sulfate"),
                        ("ph", "11.2 under 11.8 trip"),
                        ("tank", "52 C under 70"),
                        ("hold", "none applied"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Tank TC 52 C hitch is residual, not a runaway trip.",
                    "Delayed (survey_s=360): 6 min survey restacks T-2 without a recovery hold.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ph.slurry.eu (7.200 ms, 11.2 pH)"),
                        ("loser", "tc.tank.C (7.380 ms, 52 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Tank-first by < 180 us would only delay confirmation. The sulfate feed "
                            "stays legal either way; ACCEPT is still required.",
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
    ras = raster_core(
        28,
        48,
        42,
        56,
        routing(
            "thalamic-relay.nmc-ph",
            "spikenaut.policy.nmc-go",
            [
                ("relay.ph.slurry", "policy.nmc_go", 0.68),
                ("relay.tc.tank", "policy.tank_hold", 0.21),
            ],
            "serotonin",
            0.07,
            "legal_nmc_stdp; 5-HT tags the nmc_go bind at the pH-probe win",
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
            ("decision_window_ms", 0.36),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("nmc_go", 40, 0.45, 250.0, 0.36),
                    pop("tank_hold", 32, 0.90),
                    pop("ph_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r93-484",
        "Precursor-Moss PM-4 / Tank T-2: pH 11.2 beats tank 52 C by 180 us; "
        "ACCEPT already-legal 6.4 t/h sulfate",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT of an already-legal NMC sulfate feed. total +1.06 = 0.40 + 0.28 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "nmc-precursor-coprecip",
        [
            "accept",
            "already-legal",
            "simulated-coprecip",
            "ph-vs-tank",
            "sidecar-convictable",
            "simulated",
        ],
        "Teaches that a pH probe under trip can confirm an already-legal sulfate feed "
        "without a tank-TC hitch becoming a hold.",
        4,
    )


def record_485():
    ticks = [
        tick(2016, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5040, 0.10, 0.06, 0.04, 0.02, 0.02),
        tick(5200, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.08, 0.05, 0.04, 0.02),
        tick(5920, 0.06, 0.05, 0.03, 0.01, 0.01),
        tick(240000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.speed.mpm", 0.980, 0.41),
        spike("tc.drum.C", 2.016, 0.60),
        spike("ft.speed.mpm", 3.200, 0.51),
        spike("tc.drum.C", 5.040, 1.30),
        spike("ft.speed.mpm", 5.200, 1.12),
        spike("ctrl.gate", 5.640, 0.97),
        spike("tc.drum.C", 8.100, 0.78),
        spike("ft.speed.mpm", 12.400, 0.62),
        spike("ctrl.gate", 16.200, 0.85),
        spike("tc.drum.C", 20.400, 0.54),
        spike("ft.speed.mpm", 22.800, 0.43),
    ]
    excerpt = independent_excerpt(93485, 80, 24000, 12, spike_avoid_us(spikes))
    params = OrderedDict(
        [
            ("speed_mpm", 4.2),
            ("drum_C", 62.0),
            ("hold", False),
        ]
    )
    state = OrderedDict(
        [
            (
                "description",
                "Foil-Crag FC-5 electrodeposition drum D-1 holds foil at 62 C of a 78 C drum stop and "
                "line speed at 4.2 m/min of a 5.5 envelope. The 4.2 m/min make can continue; "
                "treating the tachometer as the hotter channel would shut a legal ED foil drum.",
            ),
            ("domain", "copper-foil-electrodeposition"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Run D-1 at 4.2 m/min, keep drum <= 78 C and speed <= 5.5 m/min, and "
                "leave the foil make on schedule.",
            ),
            ("t0_us", 1756850400000485),
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
                                "tc.drum.C 62 under 78 cap",
                                "ft.speed.mpm 4.2 under 5.5 trip",
                            ],
                        ),
                        (
                            "semantics",
                            "Drum-first confirms the already-legal 4.2 m/min run; speed-first would "
                            "have treated the drum TC as a hitch echo and looked for an extra hold.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one drum-TC slot versus the line-speed publisher on this ED foil bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter 52 us (TC 22 + tach 30): 3.08x over a "
                            "2.0x trust floor. Reversing order by < 160 us inside the 280 us "
                            "window would have REJECTED an already-legal 4.2 m/min run.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "drum TC well, 2 kHz, 22 us jitter",
                    "line-speed tachometer, 1 kHz, 30 us jitter",
                    "foil thickness beta (context)",
                    "rectifier kA (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("drum_cap_C", 78.0),
                        ("observed_drum_C", 62.0),
                        ("speed_mpm", 4.2),
                        ("speed_cap_mpm", 5.5),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Drum D-1 indexed on Foil-Crag FC-5; 4.2 m/min armed.",
                    "2. Drum 62 C under 78; speed 4.2 m/min under 5.5.",
                    "3. Speed precursor at 0.980 ms.",
                    "4. Race window [5.040, 5.320] ms.",
                    "5. tc.drum.C 62 at 5.040 ms (winner).",
                    "6. ft.speed.mpm 4.2 at 5.200 ms (loser by 160 us).",
                    "7. Gate at 5.640 ms: ACCEPT 4.2 m/min.",
                    "8. Drum stays 62 C; speed stays 4.2 m/min.",
                    "9. Foil make on-spec.",
                    "10. Delayed (dwell_s=240): 4 min current reseq.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "hold_speed_mpm"),
            ("parameters", params),
            (
                "evidence",
                OrderedDict(
                    [
                        ("drum_C", 62.0),
                        ("drum_cap_C", 78.0),
                        ("speed_mpm", 4.2),
                        ("speed_cap_mpm", 5.5),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("dwell_s", 240),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.2 m/min because drum 62 C is under 78 and speed "
                "4.2 m/min is under 5.5.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Drum TC 62 C won by 160 us, so the foil cell is already legal, not still climbing. "
                "Speed 4.2 m/min is under 5.5. ACCEPT the 4.2 m/min run. A REJECT would idle a legal ED drum.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "drum_C",
                            OrderedDict(
                                [
                                    ("cap", 78.0),
                                    ("observed", 62.0),
                                    ("executed_speed_mpm", 4.2),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [("margin_us", 160), ("combined_jitter_us", 52), ("ratio", 3.08)]
                            ),
                        ),
                    ]
                ),
            ),
        ]
    )
    executed = OrderedDict(
        [
            ("name", "hold_speed_mpm"),
            ("parameters", params),
            (
                "gate_effect",
                "ACCEPT: leave 4.2 m/min; drum 62 C; speed legal.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT of an already-legal 4.2 m/min ED foil run. Drum 62 C beat speed "
                "4.2 m/min by 160 us. 4 min current reseq (dwell_s=240) is delayed, not a miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("speed", "4.2 m/min held"),
                        ("drum", "62 C < 78 cap"),
                        ("cell", "D-1 on-spec"),
                        ("reseq", "4 min current reseq (dwell_s=240)"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Speed never approached 5.5 m/min; drum was already under cap.",
                    "Delayed (dwell_s=240): 4 min current reseq after make.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "tc.drum.C (5.040 ms, 62 C)"),
                        ("loser", "ft.speed.mpm (5.200 ms, 4.2 m/min)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Speed-first by < 160 us inside the 280 us window would have "
                            "REJECTED an already-legal 4.2 m/min run. The ACCEPT is still the "
                            "correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5640),
            (
                "reward_inflection_note",
                "Task and safety rise at the correct ACCEPT (5.640 ms, tick 4). The 4 min reseq "
                "is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 240),
        ]
    )
    ras = raster_core(
        24,
        80,
        28,
        54,
        routing(
            "thalamic-relay.foil-drum",
            "spikenaut.policy.foil-go",
            [
                ("relay.tc.drum", "policy.foil_go", 0.67),
                ("relay.ft.speed", "policy.foil_hold", 0.25),
            ],
            "adenosine",
            0.07,
            "accept_stdp; adenosine tags the drum-TC win as an already-legal ED foil run",
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
            ("decision_window_ms", 0.28),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop_budget("foil_go", 40, 0.45, 250.0, 0.28),
                    pop("foil_hold", 32, 0.90),
                    pop("drum_veto", 16, 0.80),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r93-485",
        "Foil-Crag FC-5 / Drum D-1: drum 62 C beats speed 4.2 m/min by 160 us; correct "
        "ACCEPT of an already-legal 4.2 m/min run",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Drum 62 < 78; speed 4.2 < 5.5. total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
        ras,
        gate,
        "copper-foil-electrodeposition",
        ["accept", "designed", "drum-vs-speed", "already-legal-cell", "tick6-sidecar-bound"],
        "Teaches that a legal line-speed header can lose to drum TC inside a 280 us window; "
        "reversing 160 us would have REJECTED an already-legal ED foil run.",
        5,
    )

