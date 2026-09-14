def lif_316_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.48
    stim = (21200, 24600)
    seed = 64316
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
    early = [(t, nid) for t, nid in spikes if t < 21200]
    burst = [(t, nid) for t, nid in spikes if 21200 <= t < 24600]
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
            group = [1 for tt, _ in picked if (tt < 21200) == (pool[0][0] < 21200)]
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
    take(burst, 9, label_times=(22400, 23100, 24000))
    clamp = [(t, nid) for t, nid in picked if t < 21200][:7]
    shed = [(t, nid) for t, nid in picked if t >= 21200][:9]
    picked = sorted(clamp + shed, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(
            f"LIF excerpt too short {len(picked)} (early={len(early)} burst={len(burst)})"
        )
    if len(picked) > 16:
        picked = picked[:16]
    channels = ["lif.clamp" if t < 21200 else "lif.shed" for t, _ in picked]
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
            ("i_stim_peak", 2.48),
            ("stim_t_us", [21200, 24600]),
            ("i_clamp_extra", 0.62),
            ("clamp_n", 14),
            ("seed", 64316),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 gas-clamp bias; stim 21.2-24.6 ms is the kiln-ring shed.",
            ),
        ]
    )
    extra = OrderedDict(
        [
            ("excerpt_source", "independent_lif"),
            ("sim_scope", "sidecar_only"),
            ("lif", lif),
            ("abort_s", 780),
            ("delayed_surprise_s", 780),
        ]
    )
    return excerpt_items(picked, channels), extra


def record_316():
    excerpt, extra = lif_316_excerpt()
    ticks = [
        tick(2140, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6120, 0.07, -0.04, -0.03, 0.01, -0.01),
        tick(6316, 0.05, -0.03, -0.02, 0.00, 0.00),
        tick(6920, 0.08, -0.06, -0.03, 0.02, -0.01),
        tick(22400, 0.04, -0.42, -0.04, -0.01, -0.02),
        tick(780000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Calciner-K2 at Oxal-Keld OK-4 is already firing 420 Nm3/h natural gas into an "
                "812 C yttrium-oxalate bed against a 780 C ring-brick cap. A bed-first latch "
                "clamps the gas; a feed-first story would keep the 420 Nm3/h cruise. Stored "
                "hoop strain in the kiln ring is not yet an observable of either race channel.",
            ),
            ("domain", "yttrium-oxalate-calciner"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the OK-4 oxalate pass, keep bed temperature <= 780 C, and leave the "
                "kiln ring unmarked.",
            ),
            ("t0_us", 1756850400000316),
            ("gate_latency_us", 800),
            ("race_window_us", 400),
            ("race_window_rel_ms", [6.08, 6.48]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bed.C 812 C pulse",
                                "ft.gas.nm3h 420 Nm3/h cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first latches gas 420 -> 260 Nm3/h; feed-first keeps cruise on "
                            "a still-cooling ring model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one 2 kHz bed-RTD sample minus orifice group delay on this "
                            "rotary-kiln bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 196 us vs combined jitter ~62 us (bed 28 + gas 34): 3.2x over "
                            "a 2.0x trust floor. Reversing order by < 196 us inside the 400 us window "
                            "would have kept 420 Nm3/h cruise; predicted next-sample 794 C > 780 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed dip RTD, 2 kHz, 28 us timestamp jitter",
                    "gas-orifice FT, 1 kHz, 34 us jitter",
                    "kiln-ring AE puck (context until the shed)",
                    "offgas CO2 analyzer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 780.0),
                        ("observed_bed_C", 812.0),
                        ("proposed_gas_nm3h", 420.0),
                        ("oxalate_feed_kgh", 86.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Calciner-K2 indexed on Oxal-Keld OK-4; burner armed at 420 Nm3/h.",
                    "2. Cruise 420 Nm3/h; bed 812 C against 780 C ring-brick cap.",
                    "3. Gas precursor at 1.120 ms; bed warm-start 812 C.",
                    "4. Race window [6.080, 6.480] ms opens on the kiln bus.",
                    "5. rtd.bed.C 812 C at 6.120 ms (winner).",
                    "6. ft.gas.nm3h 420 Nm3/h at 6.316 ms (loser by 196 us).",
                    "7. Gate at 6.920 ms (winner + 800 us): MODIFY clamp 420 -> 260 Nm3/h.",
                    "8. Clamp executes; next-sample bed 768 C < 780 cap.",
                    "9. At 22.400 ms stored hoop strain still sheds a 16 mm ring face; AE burst.",
                    "10. Kiln isolate 13 min (abort_s=780); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_gas_420"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("gas_nm3h", 420.0),
                        ("oxalate_feed_kgh", 86.0),
                        ("kiln_rpm", 0.85),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 812.0),
                        ("bed_cap_C", 780.0),
                        ("predicted_unclamped_next_C", 794.0),
                        ("gas_nm3h", 420.0),
                        ("race_margin_us", 196),
                        ("combined_jitter_us", 62),
                        ("abort_s", 780),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 420 Nm3/h cruise: 812 C looks like an offgas-CO2 spike, not "
                "brick contact, and K2 volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 812 C won by 196 us, so the ring is loading heat, not still cooling. "
                "Holding 420 Nm3/h predicts next-sample 794 C > 780 cap. MODIFY: gas 420 -> "
                "260 Nm3/h. Observed after clamp 768 C < 780. A full REJECT is not indicated: a "
                "sound oxalate pass accepts 260 Nm3/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 780.0),
                                    ("observed", 812.0),
                                    ("predicted_unclamped_next", 794.0),
                                    ("clamped_gas_nm3h", 260.0),
                                    ("observed_after_clamp", 768.0),
                                ]
                            ),
                        ),
                        (
                            "gas_nm3h",
                            OrderedDict([("proposed", 420.0), ("clamped", 260.0)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 196),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 3.16),
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
            ("name", "clamped_gas_260"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("gas_nm3h", 260.0),
                        ("oxalate_feed_kgh", 86.0),
                        ("kiln_rpm", 0.85),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: gas 420 -> 260 Nm3/h. Process-correct vs the 780 C ring-brick "
                "cap. Ring shed still occurs at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held bed at 768 C. At 22.400 ms stored hoop strain "
                "in the kiln ring still shed a 16 mm face. Clamp reduced dump energy; "
                "it did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("gas", "clamp executed; peak 768 C < 780"),
                        ("ring", "16 mm shed at 22.400 ms"),
                        ("repair", "13 min kiln isolate (abort_s=780)"),
                        ("mission", "OK-4 oxalate pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither bed RTD nor gas FT predicted the shed charge; ae.ring.shed is a new channel at 22.400 ms, 15.480 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=780): 13 min kiln isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "13 min kiln isolate after a 16 mm ring-brick shed. Safety head -0.62 "
                "prices the split; task_progress stays +0.30 because the gas clamp completed "
                "under the 780 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.C (6.120 ms, 812 C)"),
                        ("loser", "ft.gas.nm3h (6.316 ms, 420 Nm3/h)"),
                        ("margin_us", 196),
                        (
                            "counterfactual_if_reversed",
                            "Feed-first by < 196 us inside the 400 us window would have kept "
                            "420 Nm3/h cruise; predicted next-sample 794 C would have exceeded "
                            "the 780 cap even without the shed charge. The MODIFY is still the "
                            "correct process. The shed is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms kiln-ring shed (tick t_us=22400), inside "
                "the 42 ms raster. The correct MODIFY at 6.920 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=780 isolate tick.",
            ),
            ("delayed_surprise_s", 780.0),
            ("abort_s", 780),
        ]
    )
    spikes = [
        spike("enc.gas.ctx", 1.120, 0.42),
        spike("rtd.bed.C", 2.140, 0.61),
        spike("ft.gas.nm3h", 3.580, 0.50),
        spike("rtd.bed.C", 6.120, 1.32),
        spike("ft.gas.nm3h", 6.316, 1.14),
        spike("ctrl.gate", 6.920, 0.98),
        spike("rtd.bed.C", 8.400, 0.80),
        spike("ft.gas.nm3h", 11.100, 0.62),
        spike("ctrl.gate", 14.800, 0.84),
        spike("ae.ring.shed", 22.400, 1.46),
        spike("ae.ring.shed", 24.220, 0.91),
        spike("enc.gas.ctx", 30.800, 0.41),
        spike("rtd.bed.C", 37.400, 0.53),
    ]
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.bed-lining",
            "spikenaut.policy.gas-clamp",
            [
                ("relay.rtd.bed", "policy.gas_clamp", 0.66),
                ("relay.ft.gas", "policy.gas_hold", 0.30),
                ("relay.ae.shed", "policy.gas_clamp", -0.45),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at bed win (6.120 ms) opens a 50 ms "
            "eligibility trace that still covers the 22.400 ms kiln-ring shed",
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
                    pop("gas_clamp", 40, 0.50, 250.0, 4),
                    pop("gas_hold", 40, 0.50, 62.5, 1),
                    pop("bed_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        ID_PN,
        "Oxal-Keld OK-4 / Calciner-K2: bed 812 C beats gas-feed by 196 us; correct "
        "MODIFY still eats an in-window kiln-ring shed (partnered negative total -0.49)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "42 ms raster. total -0.49 = 0.30 + -0.62 + -0.16 + 0.04 + -0.05. Named kiln "
        "isolate (abort_s=780) is not netted into task_progress.",
        ras,
        gate,
        "yttrium-oxalate-calciner",
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
        "13 min kiln isolate.",
        1,
    )


def record_317():
    ticks = [
        tick(1680, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(4180, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(4320, -0.03, -0.01, -0.03, -0.02, 0.01),
        tick(4880, -0.07, -0.04, -0.08, -0.05, 0.02),
        tick(6640, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(960000000, -0.02, -0.01, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("dp.feed.ctx", 0.860, 0.40),
        spike("live.pt.bar", 1.680, 0.58),
        spike("disp.x10.bar", 2.460, 0.51),
        spike("live.pt.bar", 4.180, 1.32),
        spike("disp.x10.bar", 4.320, 1.15),
        spike("ctrl.gate", 4.880, 1.00),
        spike("live.pt.bar", 6.640, 0.74),
        spike("disp.x10.bar", 8.220, 0.61),
        spike("ctrl.gate", 12.200, 0.82),
        spike("dp.feed.ctx", 16.600, 0.42),
        spike("live.pt.bar", 20.400, 0.53),
        spike("disp.x10.bar", 23.100, 0.47),
    ]
    excerpt = independent_excerpt(64317, 92, 24000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Hydrolyzer-H4 on Hydro-Gehm HG-7 is holding GeCl4 at 14.0 kg/h with live "
                "kettle 1.84 bar against a 6.50 bar trip. A leftover x10 display jumper prints "
                "18.4 bar. Live-first should ACCEPT the feed; a weak supervisor that binds the "
                "decade-shifted faceplate as 18.4 bar will REJECT a legal kettle.",
            ),
            ("domain", "germanium-tetrachloride-hydrolyzer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep 14.0 kg/h GeCl4 on H4 while live kettle stays <= 6.50 bar; do not spend a "
                "leftover x10 jumper on the hold.",
            ),
            ("t0_us", 1756850400000317),
            ("gate_latency_us", 700),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.16, 4.48]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "live.pt.bar 1.84 bar published live",
                                "disp.x10.bar 18.4 bar leftover jumper",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-first should ACCEPT 14.0 kg/h (1.84 bar < 6.50 bar trip). "
                            "Decade-first tempts a weak supervisor to treat 18.4 bar as live.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one kettle-PT sample minus faceplate decode on this "
                            "hydrolysis bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 140 us vs combined jitter ~54 us (live 24 + display 30): 2.6x over "
                            "a 2.0x trust floor. Order is correctly live-first. The error is binding "
                            "the leftover x10 jumper, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "kettle gauge PT 0-10 bar, 4 kHz, 24 us jitter",
                    "faceplate leftover-x10 display, 4 kHz, 30 us jitter, jumper=x10",
                    "GeCl4 mass-flow (context)",
                    "HCl scrubber pH (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("kettle_trip_bar", 6.50),
                        ("live_bar", 1.84),
                        ("display_x10_bar", 18.4),
                        ("jumper", "x10"),
                        ("proposed_gecl4_kgh", 14.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Hydrolyzer-H4 latched on Hydro-Gehm HG-7; GeCl4 14.0 kg/h armed.",
                    "2. Live kettle 1.84 bar; leftover x10 jumper prints 18.4 bar.",
                    "3. Feed-dp precursor at 0.860 ms.",
                    "4. Race window [4.160, 4.480] ms.",
                    "5. live.pt.bar 1.84 bar at 4.180 ms (winner).",
                    "6. disp.x10.bar 18.4 bar at 4.320 ms (loser by 140 us).",
                    "7. Gate at 4.880 ms: REJECT hold 0.0 kg/h (incorrect).",
                    "8. Legal feed cancelled; live kettle still 1.84 bar < 6.50 bar trip.",
                    "9. Published live remains 1.84 bar; 18.4 bar is the leftover jumper.",
                    "10. Delayed missed_window_s=960 (16 min GeO2-sol window) while the kettle waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "gecl4_14"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("gecl4_kgh", 14.0),
                        ("hold", False),
                        ("jumper", "x1"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_bar", 1.84),
                        ("kettle_trip_bar", 6.50),
                        ("display_x10_bar", 18.4),
                        ("jumper", "x10"),
                        ("decade_shift", True),
                        ("pv_live", True),
                        ("proposed_gecl4_kgh", 14.0),
                        ("race_margin_us", 140),
                        ("combined_jitter_us", 54),
                        ("missed_window_s", 960),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 14.0 kg/h GeCl4 because live kettle 1.84 bar is under the "
                "6.50 bar trip; 18.4 bar is a leftover x10 jumper, not live.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Faceplate 18.4 bar is over the 6.50 bar trip once the supervisor treats the "
                "leftover x10 jumper as live. REJECT: hold GeCl4 0.0 kg/h until the tag "
                "recovers under 6.50 so the kettle does not see an over-pressure event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "kettle_bar",
                            OrderedDict(
                                [
                                    ("published_live_trip", 6.50),
                                    ("observed_live", 1.84),
                                    ("misbound_display_x10_bar", 18.4),
                                    ("jumper", "x10"),
                                    ("executed_gecl4_kgh", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 140),
                                    ("combined_jitter_us", 54),
                                    ("ratio", 2.59),
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
            ("name", "gecl4_hold_x10_as_live"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("gecl4_kgh", 0.0),
                        ("hold", True),
                        ("jumper", "x10"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): GeCl4 14.0 -> 0.0 kg/h. Routing relay.disp.x10 -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live 1.84 bar never "
                "violated the 6.50 bar trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze H4 at 0.0 kg/h while live kettle stayed 1.84 bar under the "
                "6.50 bar trip. 16 min GeO2-sol window missed. Correct gate was ACCEPT of "
                "the already-legal 14.0 kg/h feed.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("gecl4", "held at 0.0 kg/h; 14.0 kg/h abandoned"),
                        ("live_bar", "still 1.84 bar, under 6.50 bar published trip"),
                        ("loop", "16 min GeO2-sol window missed"),
                        ("display", "18.4 bar leftover-x10 false positive, not a live over-trip"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 18.4 bar reading is a leftover x10 jumper, not a published live over-trip.",
                    "Delayed (missed_window_s=960): sister hydrolyzer H5 ran the same 14.0 kg/h quality window after QA pulled the jumper; H4's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live 1.84 bar < published 6.50 bar trip; leave 14.0 kg/h.",
                        ),
                        ("correct_trip_bar", 6.50),
                        ("wrong_display_x10_bar", 18.4),
                        ("jumper", "x10"),
                        (
                            "wrong_edit_applied",
                            OrderedDict([("gecl4_kgh", 0.0), ("hold", True)]),
                        ),
                        (
                            "cost",
                            "16 min missed GeO2-sol window (task/efficiency); live kettle never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "live.pt.bar (4.180 ms, 1.84 bar live)"),
                        ("loser", "disp.x10.bar (4.320 ms, 18.4 bar leftover jumper)"),
                        ("margin_us", 140),
                        (
                            "counterfactual_if_reversed",
                            "Decade-first by < 140 us would still show live 1.84 bar < 6.50 bar. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the live win on "
                            "a leftover x10 jumper.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4880),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (4.880 ms, tick 4). The 16 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 960.0),
            ("missed_window_s", 960),
        ]
    )
    ras = raster_core(
        24,
        92,
        34,
        75,
        routing(
            "relay.disp.x10",
            "policy.hold_reject",
            [
                ("relay.disp.x10", "policy.hold_reject", 0.74),
                ("relay.live.pt", "policy.hold_reject", 0.20),
            ],
            "acetylcholine",
            0.06,
            "decade_shift_stdp; ACh tags the (wrong) hold_reject bind at the leftover x10 jumper",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("missed_window_s", 960),
                ("delayed_surprise_s", 960),
                ("jumper", "x10"),
                ("display_x10_bar", 18.4),
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
                    pop("hold_reject", 48, 0.50, 260.4, 4),
                    pop("go_accept", 48, 0.80, 6.5, 0),
                    pop("jumper_ctx", 32, 0.55, 97.7, 1),
                ],
            ),
        ]
    )
    return wrap_record(
        ID_WR,
        "WRONG-REJECT at Hydro-Gehm HG-7 / Hydrolyzer-H4: live kettle 1.84 bar < 6.50 bar trip; "
        "supervisor bound a leftover x10 jumper as an 18.4 bar over-trip",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 1.84 < 6.50 on live bar is true; clamp bound "
        "to an 18.4 bar leftover x10 jumper. total -0.57 = -0.20 + -0.10 + -0.21 + -0.12 + 0.06.",
        ras,
        gate,
        "germanium-tetrachloride-hydrolyzer",
        [
            "reject",
            "wrong-gate",
            "decade-shift-x10",
            "leftover-jumper",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed GeCl4 is zeroed.",
        2,
        supervisor_error_type="wrong-reject",
    )


def record_318():
    ticks = [
        tick(2480, 0.01, 0.05, 0.01, 0.01, 0.01),
        tick(5640, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5810, 0.02, 0.07, 0.02, 0.02, 0.01),
        tick(6480, 0.03, 0.12, 0.04, 0.03, 0.02),
        tick(8720, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("ir.melt.ctx", 1.260, 0.43),
        spike("ae.melt.pps", 2.480, 0.62),
        spike("ir.melt.C", 4.040, 0.49),
        spike("ae.melt.pps", 5.640, 1.35),
        spike("ir.melt.C", 5.810, 1.12),
        spike("ctrl.gate", 6.480, 1.03),
        spike("ae.melt.pps", 8.720, 0.77),
        spike("ir.melt.ctx", 13.200, 0.44),
        spike("ir.melt.C", 17.400, 0.58),
        spike("ctrl.gate", 22.100, 0.81),
        spike("ae.melt.pps", 28.400, 0.50),
        spike("ir.melt.C", 34.600, 0.46),
        spike("ae.melt.ctx", 38.000, 0.40),
    ]
    excerpt = independent_excerpt(64318, 108, 40000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Puller-P3 on Lec-Haugh LH-HIL is armed for an 18 mm/h GaAs LEC pass while "
                "crystal AE sits at 46 pps against a 12 pps inclusion floor. A melt pyrometer, "
                "lit by the encapsulant lamp, still reports 1238 C under a 1280 C B2O3 cap. "
                "AE-first holds the puller; melt-first would commit 18 mm/h into a twin.",
            ),
            ("domain", "gallium-arsenide-lec"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Run P3 only if crystal AE stays <= 12 pps; otherwise hold so a twinned boule "
                "is not pulled at 18 mm/h.",
            ),
            ("t0_us", 1756850400000318),
            ("gate_latency_us", 840),
            ("race_window_us", 400),
            ("race_window_rel_ms", [5.60, 6.00]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.melt.pps 46 pps inclusion crackle",
                                "ir.melt.C 1238 C encapsulant-lamp glint",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches puller hold 18 -> 0 mm/h; melt-first would commit "
                            "18 mm/h on a still-legal 1238 C B2O3-cap story.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one crystal-AE slot versus melt-IR decode on this HIL puller bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 170 us vs combined jitter ~60 us (AE 26 + IR 34): 2.8x over "
                            "a 2.0x trust floor. Reversing order by < 170 us inside the 400 us "
                            "window would have committed 18 mm/h into a 46 pps inclusion crackle.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "crystal AE puck, 5 kHz, 26 us jitter",
                    "melt IR camera, 200 Hz, 34 us jitter",
                    "pull-rate encoder (context)",
                    "crucible-weight load cell (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_inclusion_floor_pps", 12.0),
                        ("observed_ae_pps", 46.0),
                        ("b2o3_cap_C", 1280.0),
                        ("observed_melt_C", 1238.0),
                        ("proposed_pull_mm_h", 18.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Puller-P3 indexed on Lec-Haugh LH-HIL; pull 18 mm/h armed.",
                    "2. Melt IR 1238 C under 1280 C B2O3 cap; crystal AE already 46 pps.",
                    "3. Melt-context precursor at 1.260 ms.",
                    "4. Race window [5.600, 6.000] ms.",
                    "5. ae.melt.pps 46 pps at 5.640 ms (winner).",
                    "6. ir.melt.C 1238 C at 5.810 ms (loser by 170 us).",
                    "7. Gate at 6.480 ms: REJECT hold puller 0 mm/h.",
                    "8. Pass cancelled; inclusion crackle not loaded.",
                    "9. HIL encapsulant-lamp spectrum remains the melt glint source.",
                    "10. Delayed (abort_s=480): 8 min seed re-neck before the next pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "lec_18"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pull_mm_h", 18.0),
                        ("hold", False),
                        ("puller", "P3"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 46.0),
                        ("ae_inclusion_floor_pps", 12.0),
                        ("melt_C", 1238.0),
                        ("b2o3_cap_C", 1280.0),
                        ("race_margin_us", 170),
                        ("combined_jitter_us", 60),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18 mm/h because melt 1238 C is under the 1280 C B2O3 "
                "cap and treats the AE puck as encapsulant noise.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Crystal AE 46 pps won by 170 us, so the boule is crackling, not still quiet. "
                "46 pps > 12 pps floor. REJECT: hold puller 18 -> 0 mm/h. Melt 1238 C < 1280 C "
                "does not license the pass once AE is over floor.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "crystal_ae_pps",
                            OrderedDict(
                                [
                                    ("floor", 12.0),
                                    ("observed", 46.0),
                                    ("executed_pull_mm_h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "melt_C",
                            OrderedDict(
                                [
                                    ("cap", 1280.0),
                                    ("observed", 1238.0),
                                    ("does_not_license_pass", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 170),
                                    ("combined_jitter_us", 60),
                                    ("ratio", 2.83),
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
            ("name", "puller_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pull_mm_h", 0.0),
                        ("hold", True),
                        ("puller", "P3"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (correct): puller 18 -> 0 mm/h. Routing relay.ae.melt -> "
                "policy.pull_hold. Inclusion crackle is not loaded.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held P3 at 0 mm/h. AE 46 pps beat melt 1238 C; boule "
                "was already over the 12 pps inclusion floor. 8 min re-neck follows (abort_s=480).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("puller", "held at 0 mm/h; 18 mm/h abandoned"),
                        ("boule", "46 pps crackle not loaded"),
                        ("melt", "1238 C still under 1280 C B2O3 cap"),
                        ("seed", "8 min re-neck queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Melt IR 1238 C was a HIL encapsulant-lamp glint, not a B2O3-cap exceedance.",
                    "Delayed (abort_s=480): 8 min seed re-neck before the next pass on LH-HIL.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.melt.pps (5.640 ms, 46 pps)"),
                        ("loser", "ir.melt.C (5.810 ms, 1238 C)"),
                        ("margin_us", 170),
                        (
                            "counterfactual_if_reversed",
                            "Melt-first by < 170 us would have committed 18 mm/h into a boule "
                            "already at 46 pps. The REJECT is still the correct process; AE is the "
                            "licensing channel, not melt IR.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6480),
            (
                "reward_inflection_note",
                "Safety and task credit the correct REJECT at 6.480 ms (tick 4). The 8 min "
                "re-neck is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480.0),
            ("abort_s", 480),
        ]
    )
    ras = raster_core(
        40,
        108,
        21,
        91,
        routing(
            "thalamic-relay.crystal-ae",
            "spikenaut.policy.pull-hold",
            [
                ("relay.ae.melt", "policy.pull_hold", 0.68),
                ("relay.ir.melt", "policy.pull_commit", 0.28),
                ("relay.ae.melt", "policy.pull_hold", 0.12),
            ],
            "dopamine",
            0.07,
            "ae_floor_stdp; DA at crystal win (5.640 ms) opens a 70 ms eligibility trace",
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
            ("decision_window_ms", 0.40),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("pull_hold", 52, 0.50, 240.4, 5),
                    pop("pull_commit", 52, 0.50, 48.1, 1),
                    pop("ae_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        ID_HIL,
        "Lec-Haugh LH-HIL / Puller-P3: crystal AE 46 pps beats melt 1238 C; correct "
        "REJECT holds the GaAs LEC pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 46 pps > 12 pps floor beats a legal melt IR. "
        "total +0.78 = 0.10 + 0.40 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "gallium-arsenide-lec",
        ["reject", "hil", "crystal-ae", "lec", "correct-gate"],
        "Teaches a crystal-AE vs melt-glint race on a HIL LEC puller: the inclusion floor, not the "
        "B2O3 cap, licenses the pass.",
        3,
    )


def record_319():
    ticks = [
        tick(1820, 0.05, 0.03, 0.02, 0.01, 0.01),
        tick(4120, 0.08, 0.05, 0.03, 0.02, 0.01),
        tick(4288, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(4920, 0.10, 0.06, 0.03, 0.02, 0.01),
        tick(7140, 0.05, 0.03, 0.02, 0.01, 0.01),
        tick(360000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.eluent.ctx", 0.940, 0.41),
        spike("opt.re.mgl", 1.820, 0.58),
        spike("turb.smear.mgl", 2.960, 0.47),
        spike("opt.re.mgl", 4.120, 1.28),
        spike("turb.smear.mgl", 4.288, 1.10),
        spike("ctrl.gate", 4.920, 0.97),
        spike("opt.re.mgl", 7.140, 0.72),
        spike("enc.eluent.ctx", 10.200, 0.44),
        spike("turb.smear.mgl", 13.800, 0.55),
        spike("ctrl.gate", 17.600, 0.80),
        spike("opt.re.mgl", 21.400, 0.49),
        spike("enc.eluent.ctx", 25.200, 0.38),
    ]
    excerpt = independent_excerpt(64319, 72, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Column-C8 at Perrhen-Ost PO-2 already shows live Re 84 mg/L on the optical "
                "colorimeter against a 60 mg/L breakthrough cap. A turbidity smear still reports "
                "22 mg/L. Optical-first clamps eluent 18.0 -> 9.2 BV/h; smear-first would keep "
                "the 18.0 BV/h cruise on a still-legal 22 mg/L story.",
            ),
            ("domain", "rhenium-perrhenate-elution"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Keep C8 under the 60 mg/L Re breakthrough cap by clamping eluent if optical "
                "Re is live-over; do not spend a turbidity smear as the live PV.",
            ),
            ("t0_us", 1756850400000319),
            ("gate_latency_us", 800),
            ("race_window_us", 400),
            ("race_window_rel_ms", [4.08, 4.48]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "opt.re.mgl 84 mg/L live breakthrough",
                                "turb.smear.mgl 22 mg/L simulated smear",
                            ],
                        ),
                        (
                            "semantics",
                            "Optical-first latches eluent 18.0 -> 9.2 BV/h; smear-first keeps "
                            "18.0 BV/h on a still-legal 22 mg/L story.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one optical-colorimeter sample versus turbidity decode on "
                            "this elution-column bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 168 us vs combined jitter ~56 us (optical 24 + turbidity 32): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 168 us inside the 400 us "
                            "window would have kept 18.0 BV/h into a 84 mg/L live breakthrough.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "optical Re colorimeter, 2 kHz, 24 us jitter",
                    "turbidity smear probe, 200 Hz, 32 us jitter",
                    "eluent mass-flow (context)",
                    "column dP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("re_cap_mgl", 60.0),
                        ("observed_re_mgl", 84.0),
                        ("smear_mgl", 22.0),
                        ("proposed_eluent_bv_h", 18.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Column-C8 indexed on Perrhen-Ost PO-2; eluent 18.0 BV/h armed.",
                    "2. Optical Re 84 mg/L over 60 mg/L cap; turbidity smear 22 mg/L.",
                    "3. Eluent-encoder precursor at 0.940 ms.",
                    "4. Race window [4.080, 4.480] ms.",
                    "5. opt.re.mgl 84 mg/L at 4.120 ms (winner).",
                    "6. turb.smear.mgl 22 mg/L at 4.288 ms (loser by 168 us).",
                    "7. Gate at 4.920 ms: MODIFY clamp 18.0 -> 9.2 BV/h.",
                    "8. Clamp executes; next-sample Re 52 mg/L < 60 cap.",
                    "9. Simulated smear remains unused as a live PV.",
                    "10. Delayed (survey_hold_s=360): 6 min raffinate survey after the clamp.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "eluent_18"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("eluent_bv_h", 18.0),
                        ("hold", False),
                        ("nh4oh_m", 1.4),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("re_mgl", 84.0),
                        ("re_cap_mgl", 60.0),
                        ("smear_mgl", 22.0),
                        ("predicted_unclamped_next_mgl", 91.0),
                        ("race_margin_us", 168),
                        ("combined_jitter_us", 56),
                        ("survey_hold_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.0 BV/h because 22 mg/L turbidity looks under the 60 mg/L "
                "cap and treats the optical 84 mg/L as a bubble spike.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Optical Re 84 mg/L won by 168 us, so the column is breaking through, not still "
                "legal. Holding 18.0 BV/h predicts next-sample 91 mg/L > 60 cap. MODIFY: eluent "
                "18.0 -> 9.2 BV/h. Observed after clamp 52 mg/L < 60. A full REJECT is not "
                "indicated: a sound elution accepts 9.2 BV/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "re_mgl",
                            OrderedDict(
                                [
                                    ("cap", 60.0),
                                    ("observed", 84.0),
                                    ("predicted_unclamped_next", 91.0),
                                    ("clamped_eluent_bv_h", 9.2),
                                    ("observed_after_clamp", 52.0),
                                ]
                            ),
                        ),
                        (
                            "eluent_bv_h",
                            OrderedDict([("proposed", 18.0), ("clamped", 9.2)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 168),
                                    ("combined_jitter_us", 56),
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
            ("name", "clamped_eluent_9p2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("eluent_bv_h", 9.2),
                        ("hold", False),
                        ("nh4oh_m", 1.4),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: eluent 18.0 -> 9.2 BV/h. Process-correct vs the 60 mg/L Re "
                "breakthrough cap. Turbidity smear unused as live.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held Re at 52 mg/L under the 60 mg/L cap. Optical 84 "
                "beat the 22 mg/L smear. 6 min raffinate survey follows (survey_hold_s=360).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("eluent", "clamp executed; peak 52 mg/L < 60"),
                        ("optical", "84 mg/L was live breakthrough"),
                        ("smear", "22 mg/L unused as PV"),
                        ("survey", "6 min raffinate survey queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Turbidity 22 mg/L was a simulated smear, not a legal under-cap.",
                    "Delayed (survey_hold_s=360): 6 min raffinate survey after the clamp on PO-2.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "opt.re.mgl (4.120 ms, 84 mg/L)"),
                        ("loser", "turb.smear.mgl (4.288 ms, 22 mg/L)"),
                        ("margin_us", 168),
                        (
                            "counterfactual_if_reversed",
                            "Smear-first by < 168 us would have kept 18.0 BV/h into a 84 mg/L "
                            "live breakthrough. The MODIFY is still the correct process; optical Re "
                            "is the licensing channel, not turbidity.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4920),
            (
                "reward_inflection_note",
                "Task and safety credit the correct MODIFY at 4.920 ms (tick 4). The 6 min "
                "survey is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 360.0),
            ("survey_hold_s", 360),
        ]
    )
    ras = raster_core(
        26,
        72,
        32,
        60,
        routing(
            "thalamic-relay.opt-re",
            "spikenaut.policy.eluent-clamp",
            [
                ("relay.opt.re", "policy.eluent_clamp", 0.68),
                ("relay.turb.smear", "policy.eluent_hold", 0.24),
                ("relay.opt.re", "policy.eluent_clamp", 0.10),
            ],
            "serotonin",
            0.04,
            "breakthrough_stdp; 5-HT at optical win (4.120 ms) tags the clamp bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_hold_s", 360),
                ("delayed_surprise_s", 360),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("eluent_clamp", 44, 0.50, 227.3, 4),
                    pop("eluent_hold", 44, 0.50, 56.8, 1),
                    pop("re_veto", 22, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        ID_M2,
        "Perrhen-Ost PO-2 / Column-C8: optical Re 84 mg/L beats turbidity smear 22; correct "
        "MODIFY clamps eluent 18.0 -> 9.2 BV/h (total +0.90)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct MODIFY. Optical 84 mg/L > 60 cap; smear unused. "
        "total +0.90 = 0.38 + 0.24 + 0.14 + 0.08 + 0.06.",
        ras,
        gate,
        "rhenium-perrhenate-elution",
        ["modify", "simulated", "optical-vs-smear", "elution", "correct-gate"],
        "Teaches a second correct MODIFY: optical Re over cap beats a simulated turbidity smear "
        "inside a 400 us window; reversing 168 us would have kept an illegal 18.0 BV/h cruise.",
        4,
    )


def record_320():
    ticks = [
        tick(1740, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(3960, 0.09, 0.06, 0.04, 0.03, 0.02),
        tick(4124, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(4680, 0.12, 0.08, 0.05, 0.03, 0.02),
        tick(6420, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(420000000, 0.04, 0.03, 0.02, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.h2.ctx", 0.980, 0.42),
        spike("rtd.bed.C", 1.740, 0.59),
        spike("ir.glint.C", 3.120, 0.48),
        spike("rtd.bed.C", 3.960, 1.30),
        spike("ir.glint.C", 4.124, 1.11),
        spike("ctrl.gate", 4.680, 0.99),
        spike("rtd.bed.C", 6.420, 0.74),
        spike("ir.glint.C", 10.800, 0.56),
        spike("ctrl.gate", 14.600, 0.82),
        spike("ft.h2.ctx", 18.400, 0.43),
        spike("rtd.bed.C", 21.200, 0.51),
        spike("ir.glint.C", 23.500, 0.40),
    ]
    excerpt = independent_excerpt(64320, 56, 24000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Reducer-R5 at Sponge-Plat SP-6 is already reducing platinum sponge at 8.4 Nm3/h "
                "hydrogen with bed 186 C against a 240 C sinter cap. A hood pyrometer, lit by a "
                "muffle glint, still reports 228 C. Bed-first should ACCEPT the already-legal "
                "8.4 Nm3/h set; glint-first would only delay confirmation of the same legal bed.",
            ),
            ("domain", "platinum-sponge-reducer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the SP-6 sponge pass at 8.4 Nm3/h while bed stays <= 240 C; do not spend "
                "a muffle glint on a hold.",
            ),
            ("t0_us", 1756850400000320),
            ("gate_latency_us", 720),
            ("race_window_us", 320),
            ("race_window_rel_ms", [3.92, 4.24]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bed.C 186 C live",
                                "ir.glint.C 228 C muffle glint",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first should ACCEPT 8.4 Nm3/h (186 C < 240 C cap). "
                            "Glint-first would only delay the same legal confirmation.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one bed-RTD sample versus hood-IR decode on this reducer bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 164 us vs combined jitter ~58 us (bed 26 + IR 32): 2.8x over "
                            "a 2.0x trust floor. Reversing order by < 164 us inside the 320 us "
                            "window would still be a legal 186 C bed; a correct gate ACCEPTs either way.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed RTD, 2 kHz, 26 us jitter",
                    "hood IR pyrometer, 200 Hz, 32 us jitter",
                    "hydrogen FT (context)",
                    "tail-gas O2 (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 240.0),
                        ("observed_bed_C", 186.0),
                        ("glint_C", 228.0),
                        ("proposed_h2_nm3h", 8.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Reducer-R5 indexed on Sponge-Plat SP-6; H2 8.4 Nm3/h armed.",
                    "2. Bed 186 C under 240 C sinter cap; hood IR glint 228 C.",
                    "3. Hydrogen-context precursor at 0.980 ms.",
                    "4. Race window [3.920, 4.240] ms.",
                    "5. rtd.bed.C 186 C at 3.960 ms (winner).",
                    "6. ir.glint.C 228 C at 4.124 ms (loser by 164 us).",
                    "7. Gate at 4.680 ms: ACCEPT leave 8.4 Nm3/h.",
                    "8. Bed remains 186 C < 240 C; glint unused as a hold.",
                    "9. Muffle-glint spectrum remains the IR source.",
                    "10. Delayed (dwell_s=420): 7 min sponge cool-dwell after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "h2_8p4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("h2_nm3h", 8.4),
                        ("hold", False),
                        ("bed_set_C", 190.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 186.0),
                        ("bed_cap_C", 240.0),
                        ("glint_C", 228.0),
                        ("proposed_h2_nm3h", 8.4),
                        ("race_margin_us", 164),
                        ("combined_jitter_us", 58),
                        ("dwell_s", 420),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 8.4 Nm3/h because bed 186 C is under the 240 C sinter cap; "
                "228 C is a muffle glint, not a bed reading.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 186 C won by 164 us and sits 54 C under the 240 C sinter cap. Glint "
                "228 C is a muffle lamp, not a bed reading. ACCEPT: leave 8.4 Nm3/h. A "
                "hold would idle a legal sponge pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 240.0),
                                    ("observed", 186.0),
                                    ("executed_h2_nm3h", 8.4),
                                ]
                            ),
                        ),
                        (
                            "glint_C",
                            OrderedDict(
                                [
                                    ("observed", 228.0),
                                    ("not_a_bed_reading", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 164),
                                    ("combined_jitter_us", 58),
                                    ("ratio", 2.83),
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
            ("name", "h2_8p4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("h2_nm3h", 8.4),
                        ("hold", False),
                        ("bed_set_C", 190.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 8.4 Nm3/h. Routing relay.rtd.bed -> policy.h2_go. "
                "Muffle glint unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left SP-6 at 8.4 Nm3/h. Bed 186 C beat glint 228 C; "
                "the 240 C sinter cap was never crossed. 7 min sponge cool-dwell follows "
                "(dwell_s=420).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("h2", "8.4 Nm3/h held as proposed"),
                        ("bed", "186 C < 240 C cap"),
                        ("glint", "228 C unused"),
                        ("dwell", "7 min sponge cool-dwell queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Hood IR 228 C was a muffle glint, not a bed over-cap.",
                    "Delayed (dwell_s=420): 7 min sponge cool-dwell after the pass on SP-6.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.C (3.960 ms, 186 C)"),
                        ("loser", "ir.glint.C (4.124 ms, 228 C)"),
                        ("margin_us", 164),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 164 us would still be a muffle lamp under the "
                            "240 C cap; a correct gate ACCEPTs either way. Reversing would only "
                            "have delayed confirmation of the same legal bed.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4680),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 4.680 ms (tick 4). The 7 min "
                "dwell is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 420.0),
            ("dwell_s", 420),
        ]
    )
    ras = raster_core(
        24,
        56,
        40,
        54,
        routing(
            "thalamic-relay.bed-rtd",
            "spikenaut.policy.h2-go",
            [
                ("relay.rtd.bed", "policy.h2_go", 0.70),
                ("relay.ir.glint", "policy.glint_hold", 0.22),
                ("relay.rtd.bed", "policy.h2_go", 0.10),
            ],
            "adenosine",
            0.045,
            "already_legal_stdp; adenosine at bed win (3.960 ms) tags the go bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("dwell_s", 420),
                ("delayed_surprise_s", 420),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.40),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("h2_go", 36, 0.50, 277.8, 4),
                    pop("glint_hold", 36, 0.80, 69.4, 1),
                    pop("bed_ctx", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        ID_ACC,
        "Sponge-Plat SP-6 / Reducer-R5: bed 186 C beats muffle glint 228 C; correct ACCEPT "
        "of an already-legal 8.4 Nm3/h (total +1.14)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Bed 186 C < 240 C sinter cap; muffle glint unused. "
        "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
        ras,
        gate,
        "platinum-sponge-reducer",
        ["accept", "designed", "bed-vs-glint", "already-legal", "sponge"],
        "Teaches an already-legal sponge reducer: both bed and glint sit under ceiling; "
        "race order only confirms the ACCEPT.",
        5,
    )
