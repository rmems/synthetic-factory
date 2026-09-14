def lif_371_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 19.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.91
    i_stim_peak = 2.42
    stim = (22000, 25000)
    seed = 71371
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
    take(burst, 9, label_times=(22600, 23100, 23800))
    clamp = [(t, nid) for t, nid in picked if t < 22000][:7]
    crack = [(t, nid) for t, nid in picked if t >= 22000][:9]
    picked = sorted(clamp + crack, key=lambda item: (item[0], item[1]))
    if len(picked) < 10:
        raise RuntimeError(f"LIF excerpt short: {len(picked)}")
    channels = ["lif.clamp" if t < 22000 else "lif.crack" for t, _ in picked]
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
            ("seed", 71371),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-13 carry +0.62 silane-MFC clamp bias; stim 22-25 ms is the susceptor crack.",
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


def record_371():
    excerpt, extra = lif_371_excerpt()
    ticks = [
        tick(2112, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(5280, 0.08, -0.04, -0.02, 0.01, -0.01),
        tick(5460, 0.04, -0.03, -0.02, 0.00, 0.00),
        tick(5980, 0.08, -0.05, -0.03, 0.02, -0.01),
        tick(22600, 0.06, -0.41, -0.04, -0.01, -0.01),
        tick(900000000, 0.02, -0.05, -0.03, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "Epitaxial chamber C-7 on Silane-Fleet SF-3 is dumping 48 sccm SiH4 while wafer "
                "pyrometry still sits a legal 1080 C under 1120. Silane-first clamps MFC 48 -> 22 "
                "sccm; pyrometer-first would keep cruise because skin is still under the wafer cap. "
                "A susceptor crack already seated under the pocket does not appear on MFC or TC "
                "until the AE dump.",
            ),
            ("domain", "silane-cvd-epitaxy"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep C-7 SiH4 <= 30 sccm and finish the 150 mm epi without dumping wafers "
                "through a cracked susceptor.",
            ),
            ("t0_us", 1756850400000371),
            ("gate_latency_us", 700),
            ("race_window_us", 360),
            ("race_window_rel_ms", [5.280, 5.640]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "mfc.sih4.sccm 48 over 30 cap",
                                "tc.wafer.C 1080 with skin under 1120",
                            ],
                        ),
                        (
                            "semantics",
                            "Silane-first latches MFC clamp 48 -> 22 sccm; pyrometer-first keeps 48 "
                            "on a 'still under wafer-skin cap' model.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one silane MFC slot versus the wafer-pyrometer publisher on "
                            "this CVD epi bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 62 us (MFC 28 + TC 34): 2.90x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would have kept 48 sccm; predicted next-sample 41 sccm "
                            "> 30 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "silane MFC, 2 kHz, 28 us jitter",
                    "wafer pyrometer + skin TC, 1 kHz, 34 us jitter",
                    "susceptor AE puck (context)",
                    "H2 carrier FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("sih4_cap_sccm", 30.0),
                        ("observed_sih4_sccm", 48.0),
                        ("wafer_C", 1080.0),
                        ("wafer_cap_C", 1120.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. C-7 indexed on Silane-Fleet SF-3; SiH4 48 sccm; wafer 1080 C.",
                    "2. Skin under 1120 C cap; epi armed.",
                    "3. Pyrometer precursor at 1.180 ms.",
                    "4. Race window [5.280, 5.640] ms.",
                    "5. mfc.sih4.sccm 48 at 5.280 ms (winner).",
                    "6. tc.wafer.C 1080 at 5.460 ms (loser by 180 us).",
                    "7. Gate at 5.980 ms: MODIFY clamp 48 -> 22 sccm.",
                    "8. After clamp SiH4 18 sccm <= 30; wafer still 1080 C.",
                    "9. At 22.600 ms a susceptor crack dumps 2 wafers.",
                    "10. 15 min chamber isolate (abort_s=900); named un-netted loss.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_sih4_mfc"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("sih4_sccm", 48.0),
                        ("wafer_C", 1080.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("sih4_sccm", 48.0),
                        ("sih4_cap_sccm", 30.0),
                        ("predicted_unclamped_next_sccm", 41.0),
                        ("wafer_C", 1080.0),
                        ("wafer_cap_C", 1120.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 62),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 48 sccm because wafer 1080 C is under 1120, treating the "
                "48 sccm SiH4 as a still-wet MFC rather than a silane-cap miss.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "SiH4 48 sccm won by 180 us, so the epi is over-cap, not still a wafer-skin "
                "story. Holding 48 sccm predicts next-sample 41 sccm > 30 cap. MODIFY: silane "
                "48 -> 22 sccm. Observed after clamp 18 sccm <= 30. A full REJECT is not "
                "indicated: a clean epi accepts 22 sccm.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "sih4_sccm",
                            OrderedDict(
                                [
                                    ("cap", 30.0),
                                    ("observed", 48.0),
                                    ("predicted_unclamped_next", 41.0),
                                    ("clamped_sih4_sccm", 22.0),
                                    ("observed_after_clamp", 18.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 62),
                                    ("ratio", 2.90),
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
            ("name", "clamped_sih4_mfc"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("sih4_sccm", 22.0),
                        ("wafer_C", 1080.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: silane 48 -> 22 sccm. Process-correct vs the 30 sccm SiH4 cap. "
                "Susceptor still cracks at 22.600 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held SiH4 at 18 sccm. At 22.600 ms a susceptor crack "
                "already seated under the pocket dumped 2 wafers. Clamp reduced dump energy; it "
                "did not prevent the crack. Partnered negative: process heads stay honest; world "
                "loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("silane", "clamp executed; peak 18 sccm <= 30 cap"),
                        ("susceptor", "cracked at 22.600 ms; 2 wafers dumped"),
                        ("repair", "15 min chamber isolate (abort_s=900)"),
                        ("mission", "SF-3 epi incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither silane MFC nor wafer pyrometer predicted the seated susceptor crack; ae.susc.crack is a new channel at 22.600 ms, 16.620 ms after the gate, still inside the 42 ms raster.",
                    "Delayed (abort_s=900): 15 min chamber isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min chamber isolate after the susceptor crack. Safety head -0.60 prices the "
                "dump; task_progress stays +0.32 because the MFC clamp completed under the 30 "
                "sccm cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "mfc.sih4.sccm (5.280 ms, 48 sccm)"),
                        ("loser", "tc.wafer.C (5.460 ms, 1080 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Pyrometer-first by < 180 us inside the 360 us window would have kept "
                            "48 sccm; predicted next-sample 41 sccm would have missed the 30 "
                            "cap even without the crack. The MODIFY is still the correct "
                            "process. The crack is a later world charge either way, cheaper with "
                            "the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22600),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.600 ms susceptor crack (tick t_us=22600), inside the "
                "42 ms raster. The correct MODIFY at 5.980 ms is in the same excerpt. Do not put "
                "inflection on the abort_s=900 isolation tick.",
            ),
            ("delayed_surprise_s", 900),
        ]
    )
    spikes = [
        spike("tc.wafer.C", 1.180, 0.41),
        spike("mfc.sih4.sccm", 2.112, 0.58),
        spike("tc.wafer.C", 3.400, 0.50),
        spike("mfc.sih4.sccm", 5.280, 1.31),
        spike("tc.wafer.C", 5.460, 1.12),
        spike("ctrl.gate", 5.980, 0.97),
        spike("mfc.sih4.sccm", 8.100, 0.82),
        spike("tc.wafer.C", 10.400, 0.64),
        spike("ctrl.gate", 14.200, 0.86),
        spike("ae.susc.crack", 22.600, 1.48),
        spike("ae.susc.crack", 24.100, 0.93),
        spike("tc.wafer.C", 30.200, 0.40),
        spike("mfc.sih4.sccm", 36.400, 0.55),
    ]
    dw = 0.36
    ras = raster_core(
        42,
        76,
        26,
        83,
        routing(
            "thalamic-relay.epi-sih4",
            "spikenaut.policy.mfc-clamp",
            [
                ("relay.mfc.sih4", "policy.sih4_clamp", 0.68),
                ("relay.tc.wafer", "policy.temp_hold", 0.29),
                ("relay.ae.susc", "policy.sih4_clamp", -0.42),
            ],
            "noradrenaline",
            0.04,
            "surprise-gated pre_post_stdp; NA at SiH4 win (5.280 ms) opens a 42 ms eligibility "
            "trace that still covers the 22.600 ms susceptor crack",
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
                    pop_budget("sih4_clamp", 50, 0.50, 220.0, dw),
                    pop_budget("temp_hold", 40, 0.80, 50.0, dw),
                    pop("crack_veto", 24, 0.75),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r71-371"),
            (
                "title",
                "Silane-Fleet SF-3 / Chamber C-7: SiH4 beats wafer pyrometer by 180 us; "
                "correct MODIFY still eats an in-window susceptor crack (partnered negative "
                "total -0.44)",
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
                    "42 ms raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named "
                    "chamber isolate (abort_s=900) is not netted into task_progress.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "silane-cvd-epitaxy",
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
                    "15 min chamber isolate.",
                    1,
                ),
            ),
        ]
    )


def record_372():
    ticks = [
        tick(2160, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(5400, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5580, -0.04, -0.04, -0.03, -0.02, 0.01),
        tick(5920, -0.08, -0.10, -0.06, -0.03, 0.02),
        tick(6260, -0.02, -0.02, -0.02, -0.01, 0.01),
        tick(720000000, -0.02, -0.02, -0.02, -0.01, 0.00),
    ]
    spikes = [
        spike("ft.nitric.tph", 1.080, 0.42),
        spike("tag.lagged.kgh", 2.160, 0.57),
        spike("ft.nitric.tph", 3.400, 0.49),
        spike("ft.nitric.tph", 5.400, 1.29),
        spike("tag.lagged.kgh", 5.580, 1.10),
        spike("ctrl.gate", 5.920, 0.96),
        spike("ft.nitric.tph", 8.200, 0.80),
        spike("tag.lagged.kgh", 10.200, 0.63),
        spike("ctrl.gate", 12.400, 0.84),
        spike("ft.nitric.tph", 16.400, 0.41),
        spike("tag.lagged.kgh", 22.100, 0.54),
        spike("ft.nitric.tph", 26.200, 0.38),
    ]
    excerpt = independent_excerpt(71372, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "DNT nitrator N-2 at Nitryl-Hope NH-9 reads live nitric 2.4 t/h under a 3.0 t/h "
                "cap, yet a lagged bus still publishes 2400 kg/h with tag_age_us=3120. Live-SI "
                "should ACCEPT 2.4 t/h; a weak supervisor treats 2400 as t/h and slams the feed.",
            ),
            ("domain", "dinitrotoluene-nitrator"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the NH-9 mixed-acid charge with live nitric <= 3.0 t/h, leave toluene at "
                "the planned 4.8 t/h, and bind the live SI t/h tag only.",
            ),
            ("t0_us", 1756850400000372),
            ("gate_latency_us", 520),
            ("race_window_us", 340),
            ("race_window_rel_ms", [5.400, 5.740]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ft.nitric.tph 2.4 t/h LIVE SI",
                                "tag.lagged.kgh 2400 kg/h stale",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-SI-first should latch ACCEPT of 2.4 t/h; lagged-kgh-first is a "
                            "false over-cap if 2400 is read as t/h instead of kg/h.",
                        ),
                        (
                            "window_derivation",
                            "340 us = one live Coriolis slot versus the lagged kg/h publisher on "
                            "this nitrator dual-unit PLC bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 60 us (live 28 + lagged 32). Order is "
                            "correctly live-first. The error is the unit on the lagged tag, not "
                            "the race winner: 2400 kg/h equals 2.4 t/h.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "live nitric Coriolis, 2 kHz, 28 us jitter, unit=t/h, status=LIVE",
                    "lagged kg/h alias tag, 1 kHz, 32 us jitter, peak_hold_fresh=false",
                    "toluene FT (context)",
                    "jacket TC (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("nitric_cap_tph", 3.0),
                        ("live_tph", 2.4),
                        ("published_value", 2400.0),
                        ("published_unit", "kg/h"),
                        ("legal_unit", "t/h"),
                        ("tag_age_us", 3120),
                        ("max_legal_tag_age_us", 800),
                        ("peak_hold_fresh", False),
                        ("toluene_tph", 4.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. N-2 LIVE already nitrating; nitric 2.4 t/h; toluene 4.8 t/h.",
                    "2. Lagged alias still prints 2400 kg/h; tag_age_us=3120 > 800.",
                    "3. Coriolis precursor at 1.080 ms.",
                    "4. Race window [5.400, 5.740] ms.",
                    "5. ft.nitric.tph 2.4 at 5.400 ms (winner).",
                    "6. tag.lagged.kgh 2400 at 5.580 ms (loser by 180 us).",
                    "7. Gate at 5.920 ms: WRONG-MODIFY binds lagged kg/h as t/h.",
                    "8. Nitric 2.4 -> 0.35 t/h; toluene left at 4.8 t/h; mixed acid dumps.",
                    "9. Under-feed stalls nitration; 2400 kg/h was already 2.4 t/h.",
                    "10. Delayed (abort_s=720): 12 min kettle dump while N-2 is quenched.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_live_nitric"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("nitric_tph", 2.4),
                        ("bind_lagged_kgh", False),
                        ("toluene_tph", 4.8),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_tph", 2.4),
                        ("cap_tph", 3.0),
                        ("published_value", 2400.0),
                        ("published_unit", "kg/h"),
                        ("legal_unit", "t/h"),
                        ("tag_age_us", 3120),
                        ("max_legal_tag_age_us", 800),
                        ("peak_hold_fresh", False),
                        ("converted_lagged_tph", 2.4),
                        ("toluene_tph", 4.8),
                        ("t_gate_us", 5920),
                        ("correct_nitric_tph", 2.4),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 720),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes continuing 2.4 t/h nitric because live SI is under the 3.0 t/h "
                "cap; the 2400 lagged alias is the same mass flow in kg/h.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Nitric 2400 exceeds the 3.0 cap (true if the number is t/h). Apply a 0.35 t/h "
                "feed cut on the highlighted lagged tag, because TAG.LAGGED.KGH is still in the "
                "mimic. Leave the live Coriolis unread as SI.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "nitric_flow",
                            OrderedDict(
                                [
                                    ("cap_tph", 3.0),
                                    ("live_tph", 2.4),
                                    ("published_value", 2400.0),
                                    ("published_unit", "kg/h"),
                                    ("executed_tph", 0.35),
                                    ("correct_tph", 2.4),
                                ]
                            ),
                        ),
                        (
                            "unit_bind",
                            OrderedDict(
                                [
                                    ("t_gate_us", 5920),
                                    ("bind_lagged_kgh", True),
                                    ("wrong_unit", True),
                                    ("tag_age_us", 3120),
                                    ("max_legal_tag_age_us", 800),
                                    ("peak_hold_fresh", False),
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
            ("name", "nitric_cut_wrong_unit"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("nitric_tph", 0.35),
                        ("bind_lagged_kgh", True),
                        ("toluene_tph", 4.8),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY (incorrect / wrong-unit lagged-bus): 0.35 t/h nitric cut applied because "
                "2400 kg/h was read as t/h. Routing relay.stale.kgh -> policy.wrong_unit_clamp; "
                "no positive weight to policy.live_hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-MODIFY clamped a legal nitrator feed. Live 2.4 t/h was under the 3.0 t/h "
                "cap at t_gate; 2400 kg/h was the same flow on a stale alias. Under-feed dumped "
                "mixed acid. 12 min kettle dump (abort_s=720). Correct gate was ACCEPT 2.4 t/h "
                "on the live SI tag at t_gate_us=5920.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("live_nitric", "cut 2.4 -> 0.35 t/h on a legal SI reading"),
                        ("lagged_alias", "2400 kg/h still equaled 2.4 t/h"),
                        ("dump", "12 min mixed-acid dump, N-2 quench"),
                        ("mission", "nitration deferred"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Live-first was the correct order and the SI number was under cap; the MODIFY spent that win on a lagged kg/h alias read as t/h.",
                    "Delayed (abort_s=720): NH-9 holds 12 min while N-2 is dumped and recharged; next batch 14 min late.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT nitric 2.4 t/h on LIVE SI at t_gate_us=5920; bind_lagged_kgh=false; leave toluene at 4.8 t/h.",
                        ),
                        ("correct_actuator", "N-2_nitric_tph"),
                        ("wrong_unit", "kg/h alias read as t/h"),
                        ("t_gate_us", 5920),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [
                                    ("nitric_tph", 0.35),
                                    ("bind_lagged_kgh", True),
                                ]
                            ),
                        ),
                        (
                            "cost",
                            "12 min mixed-acid dump (task/efficiency); legal 2.4 t/h was slammed because 2400 kg/h was treated as t/h on a tag older than 800 us.",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ft.nitric.tph (5.400 ms, 2.4 t/h LIVE SI)"),
                        ("loser", "tag.lagged.kgh (5.580 ms, 2400 kg/h stale)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Lagged-first by < 180 us would still be 2400 kg/h = 2.4 t/h under the "
                            "3.0 t/h cap; a correct gate binds ft.nitric.tph to policy.live_hold "
                            "at t_gate either way. The wrong MODIFY spent the live win on a "
                            "wrong-unit clamp.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5920),
            (
                "reward_inflection_note",
                "Task, safety, and efficiency drop at the wrong-unit bind (5.920 ms, tick 4). "
                "The 12 min kettle dump is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 720),
        ]
    )
    dw = 0.34
    ras = raster_core(
        28,
        88,
        34,
        84,
        routing(
            "thalamic-relay.dnt-lagged",
            "spikenaut.policy.wrong-unit-clamp",
            [
                ("relay.stale.kgh", "policy.wrong_unit_clamp", 0.74),
                ("relay.ft.nitric", "policy.wrong_unit_clamp", 0.21),
            ],
            "acetylcholine",
            0.08,
            "unit_cap_stdp; ACh tags the (wrong) wrong_unit_clamp bind at the live win",
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
            ("decision_window_ms", dw),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop_budget("wrong_unit_clamp", 48, 0.45, 300.0, dw),
                    pop("live_hold", 48, 0.90),
                    pop("unit_veto", 20, 0.80),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r71-372"),
            (
                "title",
                "WRONG-MODIFY at Nitryl-Hope NH-9 / Nitrator N-2: live 2.4 t/h read correctly; "
                "0.35 t/h cut applied because 2400 kg/h was treated as t/h (wrong-unit / lagged-bus)",
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
                    "Wrong-modify / wrong-unit lagged-bus. Sidecar arithmetic 2.4 < 3.0 on live "
                    "SI is true; MODIFY bound to wrong_unit_clamp. total -0.68 = -0.22 + -0.24 + "
                    "-0.18 + -0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "dinitrotoluene-nitrator",
                    [
                        "modify",
                        "wrong-gate",
                        "wrong-unit",
                        "lagged-bus",
                        "sidecar-convictable",
                        "designed",
                    ],
                    "Teaches a probe that a correct live-first race can still be a wrong gate "
                    "when the MODIFY clamps a lagged kg/h alias as t/h. Convictable from units, "
                    "tag_age_us, and routing without nitration physics.",
                    2,
                    supervisor_error_type="wrong-modify",
                ),
            ),
        ]
    )


def record_373():
    ticks = [
        tick(2736, 0.01, 0.04, 0.01, 0.01, 0.01),
        tick(6840, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(7020, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(7640, 0.04, 0.16, 0.04, 0.04, 0.02),
        tick(7960, 0.01, 0.05, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("pt.draft.kPa", 1.360, 0.40),
        spike("ae.shaft.pps", 2.736, 0.56),
        spike("pt.draft.kPa", 4.100, 0.48),
        spike("ae.shaft.pps", 6.840, 1.34),
        spike("pt.draft.kPa", 7.020, 1.11),
        spike("ctrl.gate", 7.640, 0.98),
        spike("ae.shaft.pps", 10.400, 0.81),
        spike("pt.draft.kPa", 14.800, 0.62),
        spike("ctrl.gate", 18.200, 0.84),
        spike("ae.shaft.pps", 28.400, 0.52),
        spike("pt.draft.kPa", 36.100, 0.39),
        spike("ae.shaft.pps", 42.200, 0.44),
    ]
    excerpt = independent_excerpt(71373, 120, 46000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "HIL shaft kiln K-5 at Periclase-Quoin PQ-HIL hears lining AE at 48 pps while "
                "the draft header remains 4.2 kPa under a 6.0 kPa cap. AE-first holds magnesite; "
                "draft-first would dispatch 22 t/h because the ID fan looks legal. The HIL "
                "kiln mockup is the authority, not the dead-burn floor.",
            ),
            ("domain", "magnesia-shaft-kiln"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Keep K-5 from dispatching a growling shaft while draft pressure remains under "
                "its own cap.",
            ),
            ("t0_us", 1756850400000373),
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
                                "ae.shaft.pps 48 over 12 cap",
                                "pt.draft.kPa 4.2 under 6.0 cap",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches hold; draft-first dispatches 22 t/h magnesite on a "
                            "'draft still legal' model.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one AE puck slot versus the draft-PT publisher on this "
                            "HIL shaft-kiln bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter 58 us (AE 26 + draft 32): 3.10x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 320 us "
                            "window would have dispatched 22 t/h into a growling lining.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "lining AE puck, 50 kHz, 26 us jitter",
                    "shaft draft PT, 1 kHz, 32 us jitter",
                    "magnesite weigh-belt (context)",
                    "hood IR (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_cap_pps", 12.0),
                        ("observed_ae_pps", 48.0),
                        ("draft_kPa", 4.2),
                        ("draft_cap_kPa", 6.0),
                        ("proposed_magnesite_tph", 22.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. K-5 HIL indexed; 22 t/h magnesite armed.",
                    "2. Draft 4.2 kPa under 6.0; AE 48 pps over 12.",
                    "3. Draft precursor at 1.360 ms.",
                    "4. Race window [6.840, 7.160] ms.",
                    "5. ae.shaft.pps 48 at 6.840 ms (winner).",
                    "6. pt.draft.kPa 4.2 at 7.020 ms (loser by 180 us).",
                    "7. Gate at 7.640 ms: REJECT hold, do not dispatch.",
                    "8. Feed 0 t/h; draft left at 4.2 kPa.",
                    "9. Lining inspected on the HIL stand.",
                    "10. Delayed (abort_s=480): 8 min kiln reset.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "dispatch_magnesite"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("magnesite_tph", 22.0),
                        ("hold", False),
                        ("draft_kPa", 4.2),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 48.0),
                        ("ae_cap_pps", 12.0),
                        ("draft_kPa", 4.2),
                        ("draft_cap_kPa", 6.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 22 t/h magnesite because draft 4.2 kPa is under 6.0, treating "
                "the 48 pps AE as igniter hash rather than a growling lining.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Lining AE 48 pps won by 180 us, so the shaft is growling, not still a draft "
                "story. Draft 4.2 kPa is under 6.0 and does not authorize dispatch. REJECT: hold "
                "feed 22 -> 0 t/h. A MODIFY that only trims the ID fan would leave the growl.",
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
                                    ("executed_magnesite_tph", 0.0),
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
            ("name", "hold_shaft_kiln"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("magnesite_tph", 0.0),
                        ("hold", True),
                        ("draft_kPa", 4.2),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT: magnesite 22 -> 0 t/h. Draft left at 4.2 kPa under its own cap.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held K-5. AE 48 pps beat draft 4.2 kPa by 180 us. Header was "
                "legal; the lining was not. 8 min kiln reset (abort_s=480) is delayed survey, "
                "not a process miss.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held at 0 t/h"),
                        ("draft", "left 4.2 kPa < 6.0 cap"),
                        ("lining", "8 min kiln reset (abort_s=480)"),
                        ("mission", "HIL magnesite not dispatched"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Draft PT never crossed its cap; AE was the only over-cap channel.",
                    "Delayed (abort_s=480): 8 min kiln reset on the HIL stand.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.shaft.pps (6.840 ms, 48 pps)"),
                        ("loser", "pt.draft.kPa (7.020 ms, 4.2 kPa)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Draft-first by < 180 us inside the 320 us window would have dispatched "
                            "22 t/h into a growling lining. The REJECT is still the correct gate.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 7640),
            (
                "reward_inflection_note",
                "Safety and task rise at the correct REJECT (7.640 ms, tick 4). The 8 min kiln "
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
            "thalamic-relay.shaft-ae",
            "spikenaut.policy.kiln-hold",
            [
                ("relay.ae.shaft", "policy.kiln_hold", 0.70),
                ("relay.pt.draft", "policy.draft_go", 0.24),
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
                    pop_budget("kiln_hold", 56, 0.45, 280.0, dw),
                    pop("draft_go", 40, 0.90),
                    pop("ae_veto", 24, 0.70),
                ],
            ),
        ]
    )
    return OrderedDict(
        [
            ("id", "ttf-r71-373"),
            (
                "title",
                "Periclase-Quoin PQ-HIL / Shaft kiln K-5: lining AE 48 pps beats draft 4.2 kPa "
                "by 180 us; correct REJECT holds magnesite",
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
                    "Correct REJECT. AE 48 > 12 cap beats legal draft header. "
                    "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
                ),
            ),
            ("raster", ras),
            ("gate_snn", gate),
            (
                "meta",
                meta_block(
                    "magnesia-shaft-kiln",
                    [
                        "reject",
                        "hil",
                        "ae-vs-draft",
                        "growling-lining",
                        "tick6-sidecar-bound",
                    ],
                    "Teaches that a legal draft header can lose to lining AE inside a 320 us "
                    "window; reversing 180 us would have dispatched a growling shaft kiln.",
                    3,
                ),
            ),
        ]
    )
