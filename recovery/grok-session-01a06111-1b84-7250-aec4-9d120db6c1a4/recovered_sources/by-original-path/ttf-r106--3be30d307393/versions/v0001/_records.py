def lif_546_excerpt():
    n = 82
    dt_us = 100
    tau_m_ms = 16.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.88
    i_stim_peak = 2.48
    stim = (21400, 25000)
    seed = 106546
    window_us = 44000
    i_clamp_extra = 0.66
    clamp_n = 18
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
    early = [(t, nid) for t, nid in spikes if t < 21400]
    burst = [(t, nid) for t, nid in spikes if 21400 <= t < 25000]
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
            group = [1 for tt, _ in picked if (tt < 21400) == (pool[0][0] < 21400)]
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
    take(burst, 9, label_times=(22600, 23600, 24600))
    clamp = [(t, nid) for t, nid in picked if t < 21400][:7]
    pack = [(t, nid) for t, nid in picked if t >= 21400][:9]
    picked = sorted(clamp + pack, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(
            f"LIF excerpt too short {len(picked)} (early={len(early)} burst={len(burst)})"
        )
    channels = ["lif.clamp" if t < 21400 else "lif.relief" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 82),
            ("dt_us", 100),
            ("tau_m_ms", 16.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.88),
            ("i_stim_peak", 2.48),
            ("stim_t_us", [21400, 25000]),
            ("i_clamp_extra", 0.66),
            ("clamp_n", 18),
            ("seed", 106546),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-17 carry +0.66 CHP-clamp bias; stim 21.4-25.0 ms is the relief-disk blow.",
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


def record_546():
    excerpt, extra = lif_546_excerpt()
    ticks = [
        tick(2480, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6240, 0.07, -0.04, -0.03, 0.01, -0.01),
        tick(6424, 0.05, -0.03, -0.02, 0.00, 0.00),
        tick(7000, 0.08, -0.06, -0.03, 0.02, -0.01),
        tick(22600, 0.04, -0.38, -0.04, -0.01, -0.02),
        tick(960000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Splitter-S2 at Cleaver-Foss CF-4 is already dumping 8.4 t/h cumene hydroperoxide "
                "into a 118 C acid-side wall against a 105 C metal-temperature cap. An acid-first "
                "latch clamps the CHP; a feed-first story would keep the 8.4 t/h cruise. Stored "
                "relief-disk strain is not yet an observable of either race channel.",
            ),
            ("domain", "cumene-hydroperoxide-cleaver"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the CF-4 cleavage pass, keep acid-side wall <= 105 C, and leave the "
                "relief disk unmarked.",
            ),
            ("t0_us", 1756850400000546),
            ("gate_latency_us", 760),
            ("race_window_us", 400),
            ("race_window_rel_ms", [6.20, 6.60]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.acid.C 118 C pulse",
                                "ft.chp.tph 8.4 t/h cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Acid-first latches CHP 8.4 -> 4.6 t/h; feed-first keeps "
                            "cruise on a still-cooling disk model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one 2 kHz acid-side RTD sample minus CHP-orifice group "
                            "delay on this cleavage bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 184 us vs combined jitter ~62 us (acid 28 + CHP 34): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 184 us inside the 400 us window "
                            "would have kept 8.4 t/h cruise; predicted next-sample 112 C > 105 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "acid-side multiplex RTD, 2 kHz, 28 us timestamp jitter",
                    "CHP feed FT, 1 kHz, 34 us jitter",
                    "relief-disk AE puck (context until the blow)",
                    "sulfuric-acid analyzer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("wall_cap_C", 105.0),
                        ("observed_wall_C", 118.0),
                        ("proposed_chp_tph", 8.4),
                        ("acid_kgh", 22.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Splitter-S2 indexed on Cleaver-Foss CF-4; CHP armed at 8.4 t/h.",
                    "2. Cruise 8.4 t/h; acid-side 118 C against 105 C metal-temperature cap.",
                    "3. CHP precursor at 1.180 ms; acid-side warm-start 118 C.",
                    "4. Race window [6.200, 6.600] ms opens on the cleavage bus.",
                    "5. rtd.acid.C 118 C at 6.240 ms (winner).",
                    "6. ft.chp.tph 8.4 t/h at 6.424 ms (loser by 184 us).",
                    "7. Gate at 7.000 ms (winner + 760 us): MODIFY clamp 8.4 -> 4.6 t/h.",
                    "8. Clamp executes; next-sample wall 96 C < 105 cap.",
                    "9. At 22.600 ms stored strain still blows 12 mm of relief disk; AE burst.",
                    "10. Cleaver isolate 16 min (abort_s=960); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_chp_8p4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("chp_tph", 8.4),
                        ("acid_kgh", 22.0),
                        ("agitator_rpm", 42.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("wall_C", 118.0),
                        ("wall_cap_C", 105.0),
                        ("predicted_unclamped_next_C", 112.0),
                        ("chp_tph", 8.4),
                        ("race_margin_us", 184),
                        ("combined_jitter_us", 62),
                        ("abort_s", 960),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 8.4 t/h cruise: 118 C looks like an acid-analyzer spike, not "
                "lid contact, and S2 volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Acid-side 118 C won by 184 us, so the lid is loading heat, not still cooling. "
                "Holding 8.4 t/h predicts next-sample 112 C > 105 cap. MODIFY: CHP 8.4 -> "
                "4.6 t/h. Observed after clamp 96 C < 105. A full REJECT is not indicated: a "
                "sound cleavage pass accepts 4.6 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "wall_C",
                            OrderedDict(
                                [
                                    ("cap", 105.0),
                                    ("observed", 118.0),
                                    ("predicted_unclamped_next", 112.0),
                                    ("clamped_chp_tph", 4.6),
                                    ("observed_after_clamp", 96.0),
                                ]
                            ),
                        ),
                        (
                            "chp_tph",
                            OrderedDict([("proposed", 8.4), ("clamped", 4.6)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 184),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 2.97),
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
            ("name", "clamped_chp_4p6"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("chp_tph", 4.6),
                        ("acid_kgh", 22.0),
                        ("agitator_rpm", 42.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: CHP 8.4 -> 4.6 t/h. Process-correct vs the 105 C wall "
                "cap. Disk blow still occurs at 22.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held wall at 96 C. At 22.600 ms stored strain "
                "in the relief disk still blew a 12 mm face. Clamp reduced dump energy; "
                "it did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("chp", "clamp executed; peak 96 C < 105"),
                        ("disk", "12 mm blow at 22.600 ms"),
                        ("repair", "16 min cleaver isolate (abort_s=960)"),
                        ("mission", "CF-4 cleavage pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither acid RTD nor CHP FT predicted the disk charge; ae.relief.blow is a new channel at 22.600 ms, 15.600 ms after the gate, still inside the 44 ms raster.",
                    "Delayed (abort_s=960): 16 min cleaver isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "16 min cleaver isolate after a 12 mm relief-disk blow. Safety head -0.58 "
                "prices the split; task_progress stays +0.30 because the CHP clamp completed "
                "under the 105 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.acid.C (6.240 ms, 118 C)"),
                        ("loser", "ft.chp.tph (6.424 ms, 8.4 t/h)"),
                        ("margin_us", 184),
                        (
                            "counterfactual_if_reversed",
                            "Feed-first by < 184 us inside the 400 us window would have kept "
                            "8.4 t/h cruise; predicted next-sample 112 C would have exceeded "
                            "the 105 cap even without the disk charge. The MODIFY is still the "
                            "correct process. The blow is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22600),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.600 ms relief-disk blow (tick t_us=22600), inside "
                "the 44 ms raster. The correct MODIFY at 7.000 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=960 isolate tick.",
            ),
            ("delayed_surprise_s", 960.0),
            ("abort_s", 960),
        ]
    )
    spikes = [
        spike("enc.chp.ctx", 1.180, 0.42),
        spike("rtd.acid.C", 2.480, 0.61),
        spike("ft.chp.tph", 3.740, 0.50),
        spike("rtd.acid.C", 6.240, 1.32),
        spike("ft.chp.tph", 6.424, 1.14),
        spike("ctrl.gate", 7.000, 0.98),
        spike("rtd.acid.C", 8.720, 0.80),
        spike("ft.chp.tph", 11.400, 0.62),
        spike("ctrl.gate", 16.200, 0.84),
        spike("ae.relief.blow", 22.600, 1.46),
        spike("ae.relief.blow", 24.400, 0.91),
        spike("enc.chp.ctx", 32.100, 0.41),
        spike("rtd.acid.C", 41.200, 0.53),
    ]
    ras = raster_core(
        44,
        82,
        24,
        87,
        routing(
            "thalamic-relay.acid-disk",
            "spikenaut.policy.chp-clamp",
            [
                ("relay.rtd.acid", "policy.chp_clamp", 0.67),
                ("relay.ft.chp", "policy.chp_hold", 0.29),
                ("relay.ae.relief", "policy.chp_clamp", -0.44),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at acid win (6.240 ms) opens a 50 ms "
            "eligibility trace that still covers the 22.600 ms relief-disk blow",
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
                    pop("chp_clamp", 44, 0.50, 227.3, 4),
                    pop("chp_hold", 44, 0.50, 56.8, 1),
                    pop("wall_veto", 22, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r106-546",
        "Cleaver-Foss CF-4 / Splitter-S2: acid-side 118 C beats CHP feed by 184 us; correct "
        "MODIFY still eats an in-window relief-disk blow (partnered negative total -0.45)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "44 ms raster. total -0.45 = 0.30 + -0.58 + -0.16 + 0.04 + -0.05. Named cleaver "
        "isolate (abort_s=960) is not netted into task_progress.",
        ras,
        gate,
        "cumene-hydroperoxide-cleaver",
        [
            "modify",
            "partnered-negative",
            "independent-lif-raster",
            "sidecar-sim-only",
            "designed",
        ],
        "Teaches an in-window world charge after a process-correct clamp: LIF excerpt is "
        "membrane crossings, not a remap of spike_events; safety prices the disk, task stays honest.",
        1,
    )


def record_547():
    ticks = [
        tick(1880, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(4540, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(4700, -0.03, -0.01, -0.03, -0.02, 0.01),
        tick(5140, -0.07, -0.05, -0.08, -0.05, 0.02),
        tick(7320, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(1140000000, -0.02, -0.01, -0.04, -0.01, 0.00),
    ]
    spikes = [
        spike("ft.sevo.ctx", 0.880, 0.40),
        spike("live.rtd.eu", 1.880, 0.58),
        spike("dcs.sim.eu", 2.640, 0.51),
        spike("live.rtd.eu", 4.540, 1.32),
        spike("dcs.sim.eu", 4.700, 1.15),
        spike("ctrl.gate", 5.140, 1.00),
        spike("live.rtd.eu", 7.320, 0.74),
        spike("dcs.sim.eu", 8.480, 0.61),
        spike("ctrl.gate", 12.400, 0.82),
        spike("ft.sevo.ctx", 16.800, 0.42),
        spike("live.rtd.eu", 21.600, 0.53),
        spike("dcs.sim.eu", 25.900, 0.47),
    ]
    excerpt = independent_excerpt(106547, 94, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Still-ST3 on Sevoflur-Hope SH-7 is holding sevoflurane distillate at 2.4 t/h with "
                "live RTD 164 C against a 198 C trip. A leftover DCS MODE_SIMULATE tag from last "
                "night's reflux-model dry-run still prints 224 C. Live-RTD-first should ACCEPT "
                "the feed; a weak supervisor that binds the SIMULATE tag as process T will REJECT "
                "a legal rectifier.",
            ),
            ("domain", "sevoflurane-rectifier"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep 2.4 t/h sevoflurane on ST-3 while live RTD stays <= 198 C; "
                "do not spend a leftover MODE_SIMULATE tag on the hold.",
            ),
            ("t0_us", 1756850400000547),
            ("gate_latency_us", 600),
            ("race_window_us", 280),
            ("race_window_rel_ms", [4.48, 4.76]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "live.rtd.eu 164 C analog LIVE",
                                "dcs.sim.eu 224 C leftover MODE_SIMULATE tag",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-RTD-first should ACCEPT 2.4 t/h (164 C < 198 C trip). "
                            "Sim-tag-first tempts a weak supervisor to treat 224 C as live.",
                        ),
                        (
                            "window_derivation",
                            "280 us = one ST-3 RTD sample minus leftover MODE_SIMULATE publisher "
                            "group delay on this sevoflurane bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter ~54 us (live 24 + sim 30): 3.0x over "
                            "a 2.0x trust floor. Order is correctly live-RTD-first. The error is binding "
                            "the leftover MODE_SIMULATE tag, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "ST-3 kettle RTD, 4 kHz, 24 us jitter, analog LIVE",
                    "leftover DCS MODE_SIMULATE tag, 4 kHz, 30 us jitter, SIMULATE",
                    "sevoflurane distillate FT (context)",
                    "reflux analyzer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("trip_C", 198.0),
                        ("live_C", 164.0),
                        ("published_mode", "LIVE"),
                        ("bound_mode", "SIMULATE"),
                        ("sim_shadow_C", 224.0),
                        ("mode_simulate_is_pv", False),
                        ("proposed_feed_tph", 2.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. ST-3 latched on Sevoflur-Hope SH-7; sevoflurane 2.4 t/h armed.",
                    "2. Live RTD 164 C; leftover MODE_SIMULATE tag still prints 224 C.",
                    "3. Distillate-FT precursor at 0.880 ms.",
                    "4. Race window [4.480, 4.760] ms.",
                    "5. live.rtd.eu 164 C at 4.540 ms (winner).",
                    "6. dcs.sim.eu 224 C at 4.700 ms (loser by 160 us).",
                    "7. Gate at 5.140 ms: REJECT hold 0.0 t/h (incorrect).",
                    "8. Legal sevoflurane cancelled; live 164 C still < 198 C trip.",
                    "9. SIMULATE bind remains; leftover tag unused as a live sensor.",
                    "10. Delayed missed_window_s=1140 (19 min isomer window) while ST-3 waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "feed_2p4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 2.4),
                        ("hold", False),
                        ("bound_mode", "LIVE"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 164.0),
                        ("trip_C", 198.0),
                        ("published_mode", "LIVE"),
                        ("bound_mode", "LIVE"),
                        ("sim_shadow_C", 224.0),
                        ("mode_simulate_is_pv", False),
                        ("sim_tag_as_live", False),
                        ("pv_live", True),
                        ("proposed_feed_tph", 2.4),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 54),
                        ("missed_window_s", 1140),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 2.4 t/h feed because live RTD 164 C is under the "
                "198 C trip; 224 C is a leftover MODE_SIMULATE tag from last night's "
                "reflux-model dry-run, not the live EU.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Leftover DCS MODE_SIMULATE tag still prints 224 C, over the 198 C trip once "
                "the supervisor treats that simulation tag as live process T. REJECT: hold "
                "sevoflurane 0.0 t/h until the tag recovers under 198 so the rectifier does "
                "not see a kettle event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "sevo_kettle_C",
                            OrderedDict(
                                [
                                    ("published_live_trip", 198.0),
                                    ("observed_live", 164.0),
                                    ("misbound_mode", "SIMULATE"),
                                    ("sim_shadow_C", 224.0),
                                    ("mode_simulate_is_pv", False),
                                    ("sim_tag_as_live", True),
                                    ("executed_feed_tph", 0.0),
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
            ("name", "feed_hold_sim_tag"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 0.0),
                        ("hold", True),
                        ("bound_mode", "SIMULATE"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): feed 2.4 -> 0.0 t/h. Routing relay.dcs.sim -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live 164 C never "
                "violated the 198 C trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze ST-3 at 0.0 t/h while live RTD stayed 164 C under the "
                "198 C trip. 19 min isomer window missed. Correct gate was ACCEPT of "
                "the already-legal 2.4 t/h feed.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held at 0.0 t/h; 2.4 t/h abandoned"),
                        ("live_C", "still 164 C, under 198 C published trip"),
                        ("loop", "19 min isomer window missed"),
                        ("sim", "224 C leftover MODE_SIMULATE false positive, not a live over-trip"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 224 C reading is a leftover DCS MODE_SIMULATE tag from a reflux-model dry-run, not a published live over-trip.",
                    "Delayed (missed_window_s=1140): sister ST-4 ran the same 2.4 t/h isomer window after QA rebound the LIVE map; ST-3's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live 164 C < published 198 C trip; leave 2.4 t/h; bind LIVE analog; drop leftover MODE_SIMULATE tag.",
                        ),
                        ("correct_trip_C", 198.0),
                        ("wrong_sim_shadow_C", 224.0),
                        ("bound_mode_should_be", "LIVE"),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [("feed_tph", 0.0), ("hold", True), ("bound_mode", "SIMULATE")]
                            ),
                        ),
                        (
                            "cost",
                            "19 min missed isomer window (task/efficiency); live rectifier never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "live.rtd.eu (4.540 ms, 164 C analog LIVE)"),
                        ("loser", "dcs.sim.eu (4.700 ms, 224 C leftover MODE_SIMULATE)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Sim-tag-first by < 160 us would still show live 164 C < 198 C. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the live-RTD "
                            "win on a leftover MODE_SIMULATE tag.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5140),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (5.140 ms, tick 4). The 19 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 1140.0),
            ("missed_window_s", 1140),
        ]
    )
    ras = raster_core(
        28,
        94,
        32,
        84,
        routing(
            "relay.dcs.sim",
            "policy.hold_reject",
            [
                ("relay.dcs.sim", "policy.hold_reject", 0.75),
                ("relay.live.rtd", "policy.hold_reject", 0.18),
            ],
            "acetylcholine",
            0.06,
            "sim_tag_as_live_stdp; ACh tags the (wrong) hold_reject bind at the leftover MODE_SIMULATE shadow",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("missed_window_s", 1140),
                ("delayed_surprise_s", 1140),
                ("sim_tag_as_live", True),
                ("mode_simulate_is_pv", False),
                ("live_C", 164.0),
                ("bound_mode", "SIMULATE"),
                ("sim_shadow_C", 224.0),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.28),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 50, 0.50, 285.7, 4),
                    pop("go_accept", 50, 0.80, 7.1, 0),
                    pop("sim_ctx", 28, 0.55, 71.4, 1),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r106-547",
        "WRONG-REJECT at Sevoflur-Hope SH-7 / ST-3: live RTD 164 C < 198 C trip; "
        "supervisor bound leftover MODE_SIMULATE tag (224 C) as process T",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 164 < 198 on live RTD is true; clamp bound "
        "to a 224 C leftover MODE_SIMULATE tag. total -0.60 = -0.20 + -0.11 + -0.23 + -0.12 + 0.06.",
        ras,
        gate,
        "sevoflurane-rectifier",
        [
            "reject",
            "wrong-gate",
            "mode-simulate-as-pv",
            "simulation-tag-as-live",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live<trip RTD read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed on a leftover MODE_SIMULATE tag.",
        2,
        supervisor_error_type="wrong-reject",
    )


def record_548():
    ticks = [
        tick(2280, 0.01, 0.06, 0.01, 0.01, 0.01),
        tick(5480, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5672, 0.02, 0.07, 0.02, 0.02, 0.01),
        tick(6280, 0.03, 0.12, 0.04, 0.03, 0.02),
        tick(8160, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("ir.flame.ctx", 1.140, 0.43),
        spike("ae.refract.pps", 2.280, 0.62),
        spike("ir.flame.C", 3.780, 0.49),
        spike("ae.refract.pps", 5.480, 1.35),
        spike("ir.flame.C", 5.672, 1.12),
        spike("ctrl.gate", 6.280, 1.03),
        spike("ae.refract.pps", 8.160, 0.77),
        spike("ir.flame.ctx", 12.400, 0.44),
        spike("ir.flame.C", 16.800, 0.58),
        spike("ctrl.gate", 21.600, 0.81),
        spike("ae.refract.pps", 28.200, 0.50),
        spike("ir.flame.C", 33.400, 0.46),
        spike("ae.refract.ctx", 38.100, 0.40),
    ]
    excerpt = independent_excerpt(106548, 110, 40000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Reactor-R4 on Carbonex-Rake CR-HIL is armed for an 18 t/h carbon-black oil charge "
                "while refractory AE sits at 52 pps against a 16 pps crack floor. A flame pyrometer, "
                "lit by the pad lamp spectrum, still reports 718 C under an 850 C flame cap. AE-first "
                "holds the oil; IR-first would commit 18 t/h into a lining crack.",
            ),
            ("domain", "carbon-black-furnace"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Run R4 only if refractory AE stays <= 16 pps; otherwise hold so a lining crack is "
                "not loaded at 18 t/h.",
            ),
            ("t0_us", 1756850400000548),
            ("gate_latency_us", 800),
            ("race_window_us", 420),
            ("race_window_rel_ms", [5.44, 5.86]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.refract.pps 52 pps lining crack",
                                "ir.flame.C 718 C pad-lamp glint",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches oil hold 18 -> 0 t/h; IR-first would commit "
                            "18 t/h on a still-legal 718 C flame-cap story.",
                        ),
                        (
                            "window_derivation",
                            "420 us = one refractory-AE slot versus flame-IR decode on this HIL carbon-black bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 192 us vs combined jitter ~68 us (AE 32 + IR 36): 2.8x over "
                            "a 2.0x trust floor. Reversing order by < 192 us inside the 420 us "
                            "window would have committed 18 t/h into a 52 pps lining crack.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "reactor AE puck, 5 kHz, 32 us jitter",
                    "flame IR camera, 200 Hz, 36 us jitter",
                    "oil FT (context)",
                    "throat PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_crack_floor_pps", 16.0),
                        ("observed_ae_pps", 52.0),
                        ("flame_cap_C", 850.0),
                        ("observed_flame_C", 718.0),
                        ("proposed_oil_tph", 18.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Reactor-R4 indexed on Carbonex-Rake CR-HIL; oil 18 t/h armed.",
                    "2. Flame IR 718 C under 850 C cap; AE already 52 pps.",
                    "3. IR-context precursor at 1.140 ms.",
                    "4. Race window [5.440, 5.860] ms.",
                    "5. ae.refract.pps 52 pps at 5.480 ms (winner).",
                    "6. ir.flame.C 718 C at 5.672 ms (loser by 192 us).",
                    "7. Gate at 6.280 ms: REJECT hold oil 0 t/h.",
                    "8. Pass cancelled; lining crack not loaded.",
                    "9. HIL pad lamp spectrum remains the flame glint source.",
                    "10. Delayed (abort_s=480): 8 min brick survey before the next charge.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "oil_18"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("oil_tph", 18.0),
                        ("hold", False),
                        ("train", "R4"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 52.0),
                        ("ae_crack_floor_pps", 16.0),
                        ("flame_C", 718.0),
                        ("flame_cap_C", 850.0),
                        ("race_margin_us", 192),
                        ("combined_jitter_us", 68),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18 t/h because flame 718 C is under the 850 C "
                "cap and treats the AE puck as throat-PT noise.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Refractory AE 52 pps won by 192 us, so the lining is cracking, not still quiet. "
                "52 pps > 16 pps floor. REJECT: hold oil 18 -> 0 t/h. Flame 718 C < 850 C "
                "does not license the pass once AE is over floor.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "refract_ae_pps",
                            OrderedDict(
                                [
                                    ("floor", 16.0),
                                    ("observed", 52.0),
                                    ("executed_oil_tph", 0.0),
                                ]
                            ),
                        ),
                        (
                            "flame_C",
                            OrderedDict(
                                [
                                    ("cap", 850.0),
                                    ("observed", 718.0),
                                    ("does_not_license_pass", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 192),
                                    ("combined_jitter_us", 68),
                                    ("ratio", 2.82),
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
            ("name", "oil_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("oil_tph", 0.0),
                        ("hold", True),
                        ("train", "R4"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (correct): oil 18 -> 0 t/h. Routing relay.ae.refract -> "
                "policy.oil_hold. Lining crack is not loaded.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held R4 at 0 t/h. AE 52 pps beat flame 718 C; lining "
                "was already over the 16 pps crack floor. 8 min brick survey follows (abort_s=480).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("oil", "held at 0 t/h; 18 t/h abandoned"),
                        ("lining", "52 pps crack not loaded"),
                        ("flame", "718 C still under 850 C cap"),
                        ("survey", "8 min brick survey queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Flame IR 718 C was a HIL pad-lamp glint, not a flame-cap exceedance.",
                    "Delayed (abort_s=480): 8 min brick survey before the next charge on CR-HIL.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.refract.pps (5.480 ms, 52 pps)"),
                        ("loser", "ir.flame.C (5.672 ms, 718 C)"),
                        ("margin_us", 192),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 192 us would have committed 18 t/h into a lining "
                            "already at 52 pps. The REJECT is still the correct process; AE is the "
                            "licensing channel, not flame IR.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6280),
            (
                "reward_inflection_note",
                "Safety and task credit the correct REJECT at 6.280 ms (tick 4). The 8 min "
                "brick survey is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480.0),
            ("abort_s", 480),
        ]
    )
    ras = raster_core(
        40,
        110,
        22,
        97,
        routing(
            "thalamic-relay.refract-ae",
            "spikenaut.policy.oil-hold",
            [
                ("relay.ae.refract", "policy.oil_hold", 0.69),
                ("relay.ir.flame", "policy.oil_commit", 0.26),
                ("relay.ae.refract", "policy.oil_hold", 0.11),
            ],
            "dopamine",
            0.07,
            "ae_floor_stdp; DA at refractory win (5.480 ms) opens a 70 ms eligibility trace",
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
            ("decision_window_ms", 0.42),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("oil_hold", 56, 0.50, 212.6, 5),
                    pop("oil_commit", 56, 0.50, 42.5, 1),
                    pop("ae_veto", 28, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r106-548",
        "Carbonex-Rake CR-HIL / Reactor-R4: refractory AE 52 pps beats flame 718 C; correct "
        "REJECT holds the carbon-black oil charge",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 52 pps > 16 pps floor beats a legal flame IR. "
        "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "carbon-black-furnace",
        ["reject", "hil", "refract-ae", "carbon-black", "correct-gate"],
        "Teaches a refractory-AE vs pad-lamp-glint race on a HIL carbon-black furnace: the crack floor, "
        "not the flame cap, licenses the oil charge.",
        3,
    )


def record_549():
    ticks = [
        tick(1720, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(4280, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(4424, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(4820, 0.12, 0.09, 0.05, 0.03, 0.02),
        tick(6640, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(270000000, 0.03, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.ach.ctx", 0.760, 0.41),
        spike("rtd.reboil.C", 1.720, 0.58),
        spike("ir.condenser.C", 2.960, 0.47),
        spike("rtd.reboil.C", 4.280, 1.28),
        spike("ir.condenser.C", 4.424, 1.10),
        spike("ctrl.gate", 4.820, 0.97),
        spike("rtd.reboil.C", 6.640, 0.72),
        spike("enc.ach.ctx", 10.200, 0.44),
        spike("ir.condenser.C", 14.400, 0.55),
        spike("ctrl.gate", 18.600, 0.80),
        spike("rtd.reboil.C", 22.400, 0.49),
        spike("enc.ach.ctx", 25.200, 0.38),
    ]
    excerpt = independent_excerpt(106549, 58, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Column-C5 of Cyanohyd-Mire CM-2 is already at 64.0 C reboiler temperature while a "
                "condenser-coil IR smear still reports 89 C against an 82 C trip the live RTD has "
                "not crossed. Reboiler-first should ACCEPT 5.2 t/h acetone cyanohydrin; glint-first "
                "would invent a hold on an already-legal ACH pass.",
            ),
            ("domain", "acetone-cyanohydrin-column"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Run C5 at 5.2 t/h while reboiler stays <= 82 C; do not spend a condenser-coil "
                "IR smear on the ACH hold.",
            ),
            ("t0_us", 1756850400000549),
            ("gate_latency_us", 540),
            ("race_window_us", 300),
            ("race_window_rel_ms", [4.24, 4.54]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.reboil.C 64.0 C live",
                                "ir.condenser.C smear 89 C",
                            ],
                        ),
                        (
                            "semantics",
                            "Reboiler-first should ACCEPT 5.2 t/h (64.0 C < 82 C trip). "
                            "Glint-first would hold on a simulated condenser smear.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one reboiler RTD sample versus condenser-IR decode on this "
                            "ACH-column bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 144 us vs combined jitter ~50 us (RTD 22 + IR 28): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 144 us inside the 300 us "
                            "window would have invented a hold on an already-legal 64.0 C reboiler.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "reboiler RTD, 4 kHz, 22 us jitter",
                    "condenser IR camera, 200 Hz, 28 us jitter",
                    "ACH distillate FT (context)",
                    "HCN analyzer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("reboil_trip_C", 82.0),
                        ("observed_reboil_C", 64.0),
                        ("condenser_shadow_C", 89.0),
                        ("proposed_ach_tph", 5.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Column-C5 indexed on Cyanohyd-Mire CM-2; ACH 5.2 t/h armed.",
                    "2. Reboiler 64.0 C; condenser-IR smear 89 C over 82 C trip.",
                    "3. ACH-encoder precursor at 0.760 ms.",
                    "4. Race window [4.240, 4.540] ms.",
                    "5. rtd.reboil.C 64.0 C at 4.280 ms (winner).",
                    "6. ir.condenser.C smear at 4.424 ms (loser by 144 us).",
                    "7. Gate at 4.820 ms: ACCEPT leave 5.2 t/h.",
                    "8. Reboiler remains 64.0 C < 82 C; glint unused as a hold.",
                    "9. Simulated condenser scale remains the IR source.",
                    "10. Delayed (survey_hold_s=270): 4.5 min assay survey after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "ach_5p2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ach_tph", 5.2),
                        ("hold", False),
                        ("reflux_ratio", 1.8),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("reboil_C", 64.0),
                        ("reboil_trip_C", 82.0),
                        ("condenser_shadow_C", 89.0),
                        ("proposed_ach_tph", 5.2),
                        ("race_margin_us", 144),
                        ("combined_jitter_us", 50),
                        ("survey_hold_s", 270),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 5.2 t/h because reboiler 64.0 C is under the 82 C trip; "
                "89 C is a condenser-coil IR smear, not a reboiler temperature.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Reboiler 64.0 C won by 144 us and sits under the 82 C trip. Condenser smear "
                "89 C is a simulated coil scale, not a reboiler reading. ACCEPT: leave 5.2 t/h. "
                "A hold would idle a legal ACH pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "reboil_C",
                            OrderedDict(
                                [
                                    ("trip", 82.0),
                                    ("observed", 64.0),
                                    ("executed_ach_tph", 5.2),
                                ]
                            ),
                        ),
                        (
                            "condenser_shadow_C",
                            OrderedDict(
                                [
                                    ("observed", 89.0),
                                    ("not_a_reboiler_reading", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 144),
                                    ("combined_jitter_us", 50),
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
            ("name", "ach_5p2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ach_tph", 5.2),
                        ("hold", False),
                        ("reflux_ratio", 1.8),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 5.2 t/h. Routing relay.rtd.reboil -> policy.ach_go. "
                "Condenser-IR unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left C5 at 5.2 t/h. Reboiler 64.0 C beat condenser smear 89 C; "
                "the 82 C trip was never crossed. 4.5 min assay survey follows "
                "(survey_hold_s=270).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("ach", "5.2 t/h held as proposed"),
                        ("reboil", "64.0 C < 82 C trip"),
                        ("glint", "89 C smear unused"),
                        ("survey", "4.5 min assay survey queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "IR 89 C was a simulated condenser-coil smear, not a reboiler over-trip.",
                    "Delayed (survey_hold_s=270): 4.5 min assay survey after the pass on CM-2.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.reboil.C (4.280 ms, 64.0 C)"),
                        ("loser", "ir.condenser.C (4.424 ms, smear 89 C)"),
                        ("margin_us", 144),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 144 us would still be a condenser smear over the "
                            "82 C trip; a correct gate ACCEPTs either way. Reversing would only "
                            "have delayed confirmation of the same legal reboiler.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4820),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 4.820 ms (tick 4). The 4.5 min "
                "survey is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 270.0),
            ("survey_hold_s", 270),
        ]
    )
    ras = raster_core(
        26,
        58,
        36,
        54,
        routing(
            "thalamic-relay.reboil-rtd",
            "spikenaut.policy.ach-go",
            [
                ("relay.rtd.reboil", "policy.ach_go", 0.71),
                ("relay.ir.condenser", "policy.glint_hold", 0.21),
                ("relay.rtd.reboil", "policy.ach_go", 0.10),
            ],
            "serotonin",
            0.04,
            "already_legal_stdp; 5-HT at reboiler win (4.280 ms) tags the go bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_hold_s", 270),
                ("delayed_surprise_s", 270),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.30),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("ach_go", 36, 0.50, 277.8, 3),
                    pop("ir_hold", 36, 0.80, 9.3, 0),
                    pop("rtd_veto", 20, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r106-549",
        "Cyanohyd-Mire CM-2 / Column-C5: reboiler 64.0 C beats condenser smear; correct ACCEPT "
        "of an already-legal 5.2 t/h (total +1.10)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Reboiler 64.0 C < 82 C trip; condenser smear unused. "
        "total +1.10 = 0.42 + 0.30 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "acetone-cyanohydrin-column",
        ["accept", "simulated-smear", "reboil-vs-glint", "ach", "simulated"],
        "Teaches that a condenser-coil IR smear can lose to a legal reboiler RTD inside a "
        "300 us window; reversing 144 us would have invented a hold on an already-legal ACH column.",
        4,
    )


def record_550():
    ticks = [
        tick(1840, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(4920, 0.09, 0.06, 0.04, 0.03, 0.02),
        tick(5092, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(5540, 0.12, 0.09, 0.06, 0.03, 0.02),
        tick(7860, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(420000000, 0.04, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.feed.ctx", 0.880, 0.42),
        spike("kiln.bed.C", 1.840, 0.59),
        spike("wall.ir.C", 3.260, 0.48),
        spike("kiln.bed.C", 4.920, 1.30),
        spike("wall.ir.C", 5.092, 1.11),
        spike("ctrl.gate", 5.540, 0.99),
        spike("kiln.bed.C", 7.860, 0.74),
        spike("wall.ir.C", 11.200, 0.56),
        spike("ctrl.gate", 15.000, 0.82),
        spike("ft.feed.ctx", 17.400, 0.43),
        spike("kiln.bed.C", 20.200, 0.51),
    ]
    excerpt = independent_excerpt(106550, 50, 22000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Kiln-K8 at Baritia-Force BF-1 is calcining at 4.8 t/h with bed 918 C against a "
                "1040 C sinter cap. Wall-brick IR smear sits at 1120 C over that cap. Bed-first "
                "should ACCEPT the already-legal 4.8 t/h mix; smear-first would only delay "
                "confirmation of the same legal titanate kiln.",
            ),
            ("domain", "barium-titanate-calciner"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 4.8 t/h on K8 while bed stays <= 1040 C; do not spend a wall-brick IR "
                "smear on the kiln hold.",
            ),
            ("t0_us", 1756850400000550),
            ("gate_latency_us", 620),
            ("race_window_us", 340),
            ("race_window_rel_ms", [4.88, 5.22]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "kiln.bed.C 918 C live",
                                "wall.ir.C 1120 C smear",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first should ACCEPT 4.8 t/h (918 C < 1040 C cap). "
                            "Smear-first would only delay confirmation of the same legal kiln.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one bed-thermocouple slot versus wall-IR group delay on this "
                            "titanate-calciner bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 172 us vs combined jitter ~56 us (bed 24 + wall 32): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 172 us inside the 340 us "
                            "window would still show the live bed under cap; ACCEPT either way.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "kiln bed thermocouple, 2 kHz, 24 us jitter",
                    "wall-brick IR camera, 200 Hz, 32 us jitter",
                    "BaCO3/TiO2 feed FT (context)",
                    "oxygen analyzer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 1040.0),
                        ("observed_bed_C", 918.0),
                        ("wall_shadow_C", 1120.0),
                        ("proposed_tph", 4.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Kiln-K8 indexed on Baritia-Force BF-1; titanate mix 4.8 t/h armed.",
                    "2. Bed 918 C; wall IR smear 1120 C over 1040 C cap.",
                    "3. Feed-FT precursor at 0.880 ms.",
                    "4. Race window [4.880, 5.220] ms.",
                    "5. kiln.bed.C 918 C at 4.920 ms (winner).",
                    "6. wall.ir.C smear at 5.092 ms (loser by 172 us).",
                    "7. Gate at 5.540 ms: ACCEPT leave 4.8 t/h.",
                    "8. Bed remains 918 C < 1040 C; smear unused as a hold.",
                    "9. Titanate sendout continues.",
                    "10. Delayed (dwell_s=420): 7 min dielectric-quality dwell after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "kiln_4p8"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 4.8),
                        ("hold", False),
                        ("rpm", 1.6),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 918.0),
                        ("bed_cap_C", 1040.0),
                        ("wall_shadow_C", 1120.0),
                        ("proposed_tph", 4.8),
                        ("race_margin_us", 172),
                        ("combined_jitter_us", 56),
                        ("dwell_s", 420),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.8 t/h because bed 918 C is under the 1040 C cap "
                "and 1120 C is a wall-brick IR smear, not a bed temperature.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 918 C won by 172 us and sits under the 1040 C cap. Wall smear "
                "1120 C is not a bed reading. ACCEPT: leave 4.8 t/h. A hold would idle a "
                "legal barium-titanate calciner.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 1040.0),
                                    ("observed", 918.0),
                                    ("executed_tph", 4.8),
                                ]
                            ),
                        ),
                        (
                            "wall_shadow_C",
                            OrderedDict(
                                [
                                    ("observed", 1120.0),
                                    ("not_a_bed_reading", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 172),
                                    ("combined_jitter_us", 56),
                                    ("ratio", 3.07),
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
            ("name", "kiln_4p8"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 4.8),
                        ("hold", False),
                        ("rpm", 1.6),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 4.8 t/h. Routing relay.kiln.bed -> policy.kiln_go. "
                "Wall-IR unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left K8 at 4.8 t/h. Bed 918 C beat wall smear 1120 C; the "
                "1040 C cap held. 7 min dielectric-quality dwell follows (dwell_s=420).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("kiln", "4.8 t/h held as proposed"),
                        ("bed", "918 C < 1040 C cap"),
                        ("smear", "1120 C unused"),
                        ("survey", "7 min dielectric-quality dwell queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Wall IR 1120 C was never a trip; it only lost the race to a legal bed thermocouple.",
                    "Delayed (dwell_s=420): 7 min dielectric-quality dwell after the pass on BF-1.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "kiln.bed.C (4.920 ms, 918 C)"),
                        ("loser", "wall.ir.C (5.092 ms, smear 1120 C)"),
                        ("margin_us", 172),
                        (
                            "counterfactual_if_reversed",
                            "Smear-first by < 172 us would still be a wall-brick glint over the "
                            "1040 C cap; a correct gate ACCEPTs either way. Reversing would only "
                            "have delayed confirmation of the same legal kiln.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5540),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 5.540 ms (tick 4). The 7 min "
                "dwell is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 420.0),
            ("dwell_s", 420),
        ]
    )
    ras = raster_core(
        22,
        50,
        42,
        46,
        routing(
            "thalamic-relay.kiln-bed",
            "spikenaut.policy.kiln-go",
            [
                ("relay.kiln.bed", "policy.kiln_go", 0.70),
                ("relay.wall.ir", "policy.wall_hold", 0.23),
                ("relay.kiln.bed", "policy.kiln_go", 0.10),
            ],
            "adenosine",
            0.08,
            "already_legal_stdp; adenosine at bed win (4.920 ms) tags the go bind",
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
            ("decision_window_ms", 0.34),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("kiln_go", 32, 0.50, 275.7, 3),
                    pop("wall_hold", 32, 0.80, 9.2, 0),
                    pop("bed_veto", 16, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r106-550",
        "Baritia-Force BF-1 / Kiln-K8: 918 C beats wall smear 1120 C; correct ACCEPT "
        "of an already-legal 4.8 t/h (total +1.14)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Bed 918 C < 1040 C cap; wall smear unused. "
        "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
        ras,
        gate,
        "barium-titanate-calciner",
        ["accept", "designed", "bed-vs-wall", "already-legal", "titanate"],
        "Teaches an already-legal barium-titanate calciner: live bed sits under cap; "
        "wall-brick IR smear only confirms the ACCEPT.",
        5,
    )
