def lif_476_excerpt():
    n = 78
    dt_us = 100
    tau_m_ms = 17.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.89
    i_stim_peak = 2.56
    stim = (21200, 25000)
    seed = 92476
    window_us = 46000
    i_clamp_extra = 0.70
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
    early = [(t, nid) for t, nid in spikes if t < 21200]
    burst = [(t, nid) for t, nid in spikes if 21200 <= t < 25000]
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
    take(burst, 9, label_times=(22400, 23400, 24400))
    clamp = [(t, nid) for t, nid in picked if t < 21200][:7]
    gas = [(t, nid) for t, nid in picked if t >= 21200][:9]
    picked = sorted(clamp + gas, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(
            f"LIF excerpt too short {len(picked)} (early={len(early)} burst={len(burst)})"
        )
    channels = ["lif.clamp" if t < 21200 else "lif.gassing" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 78),
            ("dt_us", 100),
            ("tau_m_ms", 17.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.89),
            ("i_stim_peak", 2.56),
            ("stim_t_us", [21200, 25000]),
            ("i_clamp_extra", 0.70),
            ("clamp_n", 18),
            ("seed", 92476),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-17 carry +0.70 cyclohexanone-clamp bias; stim 21.2-25.0 ms is the packing gassing.",
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


def record_476():
    excerpt, extra = lif_476_excerpt()
    ticks = [
        tick(2180, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6280, 0.08, -0.04, -0.03, 0.01, -0.01),
        tick(6460, 0.05, -0.03, -0.02, 0.00, 0.00),
        tick(7040, 0.09, -0.06, -0.03, 0.02, -0.01),
        tick(22400, 0.04, -0.40, -0.04, -0.01, -0.02),
        tick(900000000, 0.02, -0.05, -0.02, 0.01, 0.00),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "BV-R5 at Caprol-Stang CS-4 is already pushing 12.4 t/h cyclohexanone into a 168 C "
                "peracetic bed against a 155 C hotspot cap. A bed-first latch clamps the ketone; "
                "a feed-first story would keep the 12.4 t/h cruise. Stored packing strain is not "
                "yet an observable of either race channel.",
            ),
            ("domain", "caprolactone-baeyer-villiger"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the CS-4 Baeyer-Villiger pass, keep bed hotspot <= 155 C, and leave the "
                "ceramic packing unmarked.",
            ),
            ("t0_us", 1756850400000476),
            ("gate_latency_us", 760),
            ("race_window_us", 420),
            ("race_window_rel_ms", [6.24, 6.66]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bed.C 168 C pulse",
                                "ft.one.tph 12.4 t/h cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first latches cyclohexanone 12.4 -> 7.1 t/h; feed-first keeps "
                            "cruise on a still-cooling BV model.",
                        ),
                        (
                            "window_derivation",
                            "420 us = one 2 kHz bed-RTD sample minus ketone-orifice group delay "
                            "on this BV bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter ~60 us (bed 30 + ketone 30): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 420 us window "
                            "would have kept 12.4 t/h cruise; predicted next-sample 161 C > 155 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "bed multiplex RTD, 2 kHz, 30 us timestamp jitter",
                    "cyclohexanone feed FT, 1 kHz, 30 us jitter",
                    "packing AE puck (context until the gassing)",
                    "epsilon-caprolactone analyzer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 155.0),
                        ("observed_bed_C", 168.0),
                        ("proposed_one_tph", 12.4),
                        ("peracetic_wt_pct", 18.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. BV-R5 indexed on Caprol-Stang CS-4; cyclohexanone armed at 12.4 t/h.",
                    "2. Cruise 12.4 t/h; bed 168 C against 155 C hotspot cap.",
                    "3. Ketone precursor at 1.220 ms; bed warm-start 168 C.",
                    "4. Race window [6.240, 6.660] ms opens on the BV bus.",
                    "5. rtd.bed.C 168 C at 6.280 ms (winner).",
                    "6. ft.one.tph 12.4 t/h at 6.460 ms (loser by 180 us).",
                    "7. Gate at 7.040 ms (winner + 760 us): MODIFY clamp 12.4 -> 7.1 t/h.",
                    "8. Clamp executes; next-sample bed 149 C < 155 cap.",
                    "9. At 22.400 ms stored strain still gasses 16 mm of packing; AE burst.",
                    "10. Bed isolate 15 min (abort_s=900); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_one_12p4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("one_tph", 12.4),
                        ("peracetic_wt_pct", 18.0),
                        ("whsv_h", 3.8),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 168.0),
                        ("bed_cap_C", 155.0),
                        ("predicted_unclamped_next_C", 161.0),
                        ("one_tph", 12.4),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 12.4 t/h cruise: 168 C looks like a lactone-analyzer spike, not "
                "packing contact, and R5 volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 168 C won by 180 us, so the packing is loading heat, not still cooling. "
                "Holding 12.4 t/h predicts next-sample 161 C > 155 cap. MODIFY: cyclohexanone 12.4 -> "
                "7.1 t/h. Observed after clamp 149 C < 155. A full REJECT is not indicated: a "
                "sound BV pass accepts 7.1 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 155.0),
                                    ("observed", 168.0),
                                    ("predicted_unclamped_next", 161.0),
                                    ("clamped_one_tph", 7.1),
                                    ("observed_after_clamp", 149.0),
                                ]
                            ),
                        ),
                        (
                            "one_tph",
                            OrderedDict([("proposed", 12.4), ("clamped", 7.1)]),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 60),
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
            ("name", "clamped_one_7p1"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("one_tph", 7.1),
                        ("peracetic_wt_pct", 18.0),
                        ("whsv_h", 3.8),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: cyclohexanone 12.4 -> 7.1 t/h. Process-correct vs the 155 C hotspot "
                "cap. Packing gassing still occurs at 22.400 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held bed at 149 C. At 22.400 ms stored strain "
                "in the ceramic packing still gassed a 16 mm face. Clamp reduced dump energy; "
                "it did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("cyclohexanone", "clamp executed; peak 149 C < 155"),
                        ("packing", "16 mm gassing at 22.400 ms"),
                        ("repair", "15 min bed isolate (abort_s=900)"),
                        ("mission", "CS-4 BV pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither bed RTD nor ketone FT predicted the packing charge; ae.gas.collapse is a new channel at 22.400 ms, 15.360 ms after the gate, still inside the 46 ms raster.",
                    "Delayed (abort_s=900): 15 min bed isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min bed isolate after a 16 mm packing gassing collapse. Safety head -0.60 "
                "prices the split; task_progress stays +0.32 because the ketone clamp completed "
                "under the 155 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.C (6.280 ms, 168 C)"),
                        ("loser", "ft.one.tph (6.460 ms, 12.4 t/h)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Feed-first by < 180 us inside the 420 us window would have kept "
                            "12.4 t/h cruise; predicted next-sample 161 C would have exceeded "
                            "the 155 cap even without the packing charge. The MODIFY is still the "
                            "correct process. The collapse is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22400),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.400 ms packing gassing (tick t_us=22400), inside "
                "the 46 ms raster. The correct MODIFY at 7.040 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=900 isolate tick.",
            ),
            ("delayed_surprise_s", 900.0),
            ("abort_s", 900),
        ]
    )
    spikes = [
        spike("enc.one.ctx", 1.220, 0.42),
        spike("rtd.bed.C", 2.180, 0.61),
        spike("ft.one.tph", 3.640, 0.50),
        spike("rtd.bed.C", 6.280, 1.32),
        spike("ft.one.tph", 6.460, 1.14),
        spike("ctrl.gate", 7.040, 0.98),
        spike("rtd.bed.C", 8.560, 0.80),
        spike("ft.one.tph", 11.400, 0.62),
        spike("ctrl.gate", 15.200, 0.84),
        spike("ae.gas.collapse", 22.400, 1.46),
        spike("ae.gas.collapse", 24.200, 0.91),
        spike("enc.one.ctx", 32.000, 0.41),
        spike("rtd.bed.C", 41.200, 0.53),
    ]
    ras = raster_core(
        46,
        78,
        25,
        90,
        routing(
            "thalamic-relay.bed-bv",
            "spikenaut.policy.one-clamp",
            [
                ("relay.rtd.bed", "policy.one_clamp", 0.66),
                ("relay.ft.one", "policy.one_hold", 0.30),
                ("relay.ae.gas", "policy.one_clamp", -0.45),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at bed win (6.280 ms) opens a 50 ms "
            "eligibility trace that still covers the 22.400 ms packing gassing",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.42),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("one_clamp", 44, 0.50, 226.8, 4),
                    pop("one_hold", 44, 0.50, 54.1, 1),
                    pop("bed_veto", 22, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r92-476",
        "Caprol-Stang CS-4 / BV-R5: bed 168 C beats cyclohexanone-feed by 180 us; correct "
        "MODIFY still eats an in-window packing gassing (partnered negative total -0.44)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "46 ms raster. total -0.44 = 0.32 + -0.60 + -0.16 + 0.04 + -0.04. Named bed "
        "isolate (abort_s=900) is not netted into task_progress.",
        ras,
        gate,
        "caprolactone-baeyer-villiger",
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
        "15 min bed isolate.",
        1,
    )


def record_477():
    ticks = [
        tick(1840, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(4520, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(4700, -0.03, -0.01, -0.03, -0.02, 0.01),
        tick(5240, -0.07, -0.06, -0.07, -0.04, 0.02),
        tick(7380, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(1140000000, -0.02, -0.01, -0.04, 0.00, 0.00),
    ]
    spikes = [
        spike("ft.po.ctx", 0.920, 0.40),
        spike("live.tc.loop", 1.840, 0.58),
        spike("stale.k.eu", 2.640, 0.51),
        spike("live.tc.loop", 4.520, 1.32),
        spike("stale.k.eu", 4.700, 1.15),
        spike("ctrl.gate", 5.240, 1.00),
        spike("live.tc.loop", 7.380, 0.74),
        spike("stale.k.eu", 8.460, 0.61),
        spike("ctrl.gate", 12.600, 0.82),
        spike("ft.po.ctx", 16.400, 0.42),
        spike("live.tc.loop", 21.200, 0.53),
        spike("stale.k.eu", 25.400, 0.47),
    ]
    excerpt = independent_excerpt(92477, 90, 30000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Alkox-K3 on Alkoxyl-Nab AN-6 is holding propylene-oxide at 9.6 t/h with live "
                "Type-J 168.0 C against a 210.0 C trip. A leftover Type-K table plus leftover "
                "72 C CJC still print 221.0 C. Live-type-first should ACCEPT the feed; a weak "
                "supervisor that binds the Type-K shadow will REJECT a legal alkoxylation.",
            ),
            ("domain", "polyether-polyol-alkoxylation"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep 9.6 t/h propylene-oxide on Alkox-K3 while live kettle stays <= 210.0 C; "
                "do not spend a leftover Type-K table or leftover 72 C CJC on the hold.",
            ),
            ("t0_us", 1756850400000477),
            ("gate_latency_us", 720),
            ("race_window_us", 360),
            ("race_window_rel_ms", [4.48, 4.84]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "live.tc.loop 168.0 C LIVE Type-J CJC 24 C",
                                "stale.k.eu 221.0 C leftover Type-K table",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-type-first should ACCEPT 9.6 t/h (168.0 C < 210.0 C trip). "
                            "Type-K-first tempts a weak supervisor to treat 221.0 C as live.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one Alkox-K3 TC sample minus leftover Type-K group delay "
                            "on this polyol bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter ~60 us (live 28 + stale 32): 3.0x over "
                            "a 2.0x trust floor. Order is correctly live-type-first. The error is binding "
                            "the leftover Type-K table, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "Alkox-K3 Type-J TC, 4 kHz, 28 us jitter, CJC=24 C LIVE",
                    "leftover Type-K table shadow, 4 kHz, 32 us jitter, leftover CJC=72 C STALE",
                    "propylene-oxide FT (context)",
                    "KOH catalyst FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("trip_C", 210.0),
                        ("live_C", 168.0),
                        ("shadow_C", 221.0),
                        ("live_mV", 8.98),
                        ("cjc_live_C", 24.0),
                        ("cjc_leftover_C", 72.0),
                        ("proposed_po_tph", 9.6),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Alkox-K3 latched on Alkoxyl-Nab AN-6; propylene-oxide 9.6 t/h armed.",
                    "2. Live Type-J 168.0 C; leftover Type-K table still prints 221.0 C.",
                    "3. PO-FT precursor at 0.920 ms.",
                    "4. Race window [4.480, 4.840] ms.",
                    "5. live.tc.loop 168.0 C at 4.520 ms (winner).",
                    "6. stale.k.eu 221.0 C at 4.700 ms (loser by 180 us).",
                    "7. Gate at 5.240 ms: REJECT hold 0.0 t/h (incorrect).",
                    "8. Legal feed cancelled; live kettle still 168.0 C < 210.0 C trip.",
                    "9. Type-swap and leftover CJC remain the published bind.",
                    "10. Delayed missed_window_s=1140 (19 min OH-number window) while K3 waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "po_9p6"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("po_tph", 9.6),
                        ("hold", False),
                        ("bound_tc_type", "J"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_C", 168.0),
                        ("trip_C", 210.0),
                        ("shadow_C", 221.0),
                        ("live_mV", 8.98),
                        ("tc_type_live", "J"),
                        ("tc_type_bound", "K"),
                        ("cjc_live_C", 24.0),
                        ("cjc_leftover_C", 72.0),
                        ("type_swap", False),
                        ("leftover_cjc", False),
                        ("pv_live", True),
                        ("proposed_po_tph", 9.6),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 60),
                        ("missed_window_s", 1140),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 9.6 t/h propylene-oxide because live Type-J 168.0 C is under the "
                "210.0 C trip; 221.0 C is leftover Type-K millivolt lookup on the same 8.98 mV, "
                "not the live kettle.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Leftover Type-K table maps the same 8.98 mV to 221.0 C, over the 210.0 C trip "
                "once the supervisor treats the stale table as live. REJECT: hold propylene-oxide "
                "0.0 t/h until the tag recovers under 210 so the kettle does not see an over-temp.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "kettle_C",
                            OrderedDict(
                                [
                                    ("published_live_trip", 210.0),
                                    ("observed_live", 168.0),
                                    ("misbound_shadow_C", 221.0),
                                    ("live_mV", 8.98),
                                    ("tc_type_live", "J"),
                                    ("tc_type_bound", "K"),
                                    ("cjc_live_C", 24.0),
                                    ("cjc_leftover_C", 72.0),
                                    ("type_swap", True),
                                    ("leftover_cjc", True),
                                    ("executed_po_tph", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 180),
                                    ("combined_jitter_us", 60),
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
            ("name", "po_hold_type_swap"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("po_tph", 0.0),
                        ("hold", True),
                        ("bound_tc_type", "K"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): propylene-oxide 9.6 -> 0.0 t/h. Routing relay.tc.stale -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live 168.0 C never "
                "violated the 210.0 C trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze Alkox-K3 at 0.0 t/h while live kettle stayed 168.0 C under the "
                "210.0 C trip. 19 min OH-number window missed. Correct gate was ACCEPT of "
                "the already-legal 9.6 t/h feed.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("propylene_oxide", "held at 0.0 t/h; 9.6 t/h abandoned"),
                        ("live_C", "still 168.0 C, under 210.0 C published trip"),
                        ("kettle", "19 min OH-number window missed"),
                        ("tc", "221.0 C Type-K false positive, not a live over-trip"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 221.0 C reading is leftover Type-K millivolt lookup on a fresh 8.98 mV Type-J, not a published live over-trip.",
                    "Delayed (missed_window_s=1140): sister Alkox-K4 ran the same 9.6 t/h OH-number window after QA rebound the TC table; K3's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live 168.0 C < published 210.0 C trip; leave 9.6 t/h; bind live Type-J with CJC 24 C.",
                        ),
                        ("correct_trip_C", 210.0),
                        ("wrong_shadow_C", 221.0),
                        ("bound_tc_should_be", "J"),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [("po_tph", 0.0), ("hold", True), ("bound_tc_type", "K")]
                            ),
                        ),
                        (
                            "cost",
                            "19 min missed OH-number window (task/efficiency); live K3 never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "live.tc.loop (4.520 ms, 168.0 C LIVE Type-J CJC 24)"),
                        ("loser", "stale.k.eu (4.700 ms, 221.0 C STALE Type-K)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Type-K-first by < 180 us would still show live 168.0 C < 210.0 C. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the live-type "
                            "win on a leftover Type-K table.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5240),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (5.240 ms, tick 4). The 19 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 1140.0),
            ("missed_window_s", 1140),
        ]
    )
    ras = raster_core(
        30,
        90,
        30,
        81,
        routing(
            "relay.tc.stale",
            "policy.hold_reject",
            [
                ("relay.tc.stale", "policy.hold_reject", 0.75),
                ("relay.live.tc", "policy.hold_reject", 0.17),
            ],
            "acetylcholine",
            0.06,
            "type_swap_stdp; ACh tags the (wrong) hold_reject bind at the leftover Type-K shadow",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("missed_window_s", 1140),
                ("delayed_surprise_s", 1140),
                ("type_swap", True),
                ("leftover_cjc", True),
                ("shadow_C", 221.0),
                ("live_C", 168.0),
                ("tc_type_bound", "K"),
                ("cjc_leftover_C", 72.0),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.36),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 50, 0.50, 222.2, 4),
                    pop("go_accept", 50, 0.80, 5.6, 0),
                    pop("cjc_ctx", 28, 0.55, 99.2, 1),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r92-477",
        "WRONG-REJECT at Alkoxyl-Nab AN-6 / Alkox-K3: live Type-J 168.0 C < 210.0 C trip; "
        "supervisor bound leftover Type-K table (221.0 C) as the live kettle",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 168.0 < 210.0 on live K3 is true; clamp bound "
        "to a 221.0 C leftover Type-K shadow. total -0.58 = -0.20 + -0.12 + -0.22 + -0.10 + 0.06.",
        ras,
        gate,
        "polyether-polyol-alkoxylation",
        [
            "reject",
            "wrong-gate",
            "cold-junction-offset",
            "thermocouple-type-swap",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed on a leftover Type-K table.",
        2,
        supervisor_error_type="wrong-reject",
    )


def record_478():
    ticks = [
        tick(2320, 0.01, 0.06, 0.01, 0.01, 0.01),
        tick(5480, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5680, 0.02, 0.07, 0.02, 0.02, 0.01),
        tick(6340, 0.03, 0.12, 0.04, 0.03, 0.02),
        tick(8180, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(480000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("ir.melt.ctx", 1.120, 0.43),
        spike("ae.seed.pps", 2.320, 0.62),
        spike("ir.melt.C", 3.800, 0.49),
        spike("ae.seed.pps", 5.480, 1.35),
        spike("ir.melt.C", 5.680, 1.12),
        spike("ctrl.gate", 6.340, 1.03),
        spike("ae.seed.pps", 8.180, 0.77),
        spike("ir.melt.ctx", 12.400, 0.44),
        spike("ir.melt.C", 16.600, 0.58),
        spike("ctrl.gate", 21.400, 0.81),
        spike("ae.seed.pps", 27.000, 0.50),
        spike("ir.melt.C", 32.200, 0.46),
        spike("ae.seed.ctx", 35.600, 0.40),
    ]
    excerpt = independent_excerpt(92478, 110, 38000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "LPE-slider G2 on Indphos-Lythe IL-HIL is armed for a 4.2 mm/h InP layer while "
                "seed AE sits at 52 pps against a 14 pps crack floor. A melt pyrometer, lit by the "
                "pad lamp spectrum, still reports 980 C under a 1080 C melt cap. AE-first holds "
                "the slider; IR-first would commit 4.2 mm/h into a cracked seed.",
            ),
            ("domain", "indium-phosphide-lpe"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Run G2 only if seed AE stays <= 14 pps; otherwise hold so a cracked InP seed is "
                "not loaded at 4.2 mm/h.",
            ),
            ("t0_us", 1756850400000478),
            ("gate_latency_us", 860),
            ("race_window_us", 400),
            ("race_window_rel_ms", [5.44, 5.84]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.seed.pps 52 pps seed crack",
                                "ir.melt.C 980 C pad-lamp glint",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches slider hold 4.2 -> 0 mm/h; IR-first would commit "
                            "4.2 mm/h on a still-legal 980 C melt-cap story.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one seed-AE slot versus melt-IR decode on this HIL LPE bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 200 us vs combined jitter ~64 us (AE 30 + IR 34): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 200 us inside the 400 us "
                            "window would have committed 4.2 mm/h into a 52 pps seed crack.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "seed AE puck, 5 kHz, 30 us jitter",
                    "melt IR camera, 200 Hz, 34 us jitter",
                    "slider encoder (context)",
                    "boat PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_crack_floor_pps", 14.0),
                        ("observed_ae_pps", 52.0),
                        ("melt_cap_C", 1080.0),
                        ("observed_melt_C", 980.0),
                        ("proposed_slide_mm_h", 4.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. LPE-slider G2 indexed on Indphos-Lythe IL-HIL; slide 4.2 mm/h armed.",
                    "2. Melt IR 980 C under 1080 C cap; AE already 52 pps.",
                    "3. IR-context precursor at 1.120 ms.",
                    "4. Race window [5.440, 5.840] ms.",
                    "5. ae.seed.pps 52 pps at 5.480 ms (winner).",
                    "6. ir.melt.C 980 C at 5.680 ms (loser by 200 us).",
                    "7. Gate at 6.340 ms: REJECT hold slide 0 mm/h.",
                    "8. Pass cancelled; seed crack not loaded.",
                    "9. HIL pad lamp spectrum remains the melt glint source.",
                    "10. Delayed (abort_s=480): 8 min seed re-seat before the next slide.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "lpe_slide_4p2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("slide_mm_h", 4.2),
                        ("hold", False),
                        ("seed", "G2"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 52.0),
                        ("ae_crack_floor_pps", 14.0),
                        ("melt_C", 980.0),
                        ("melt_cap_C", 1080.0),
                        ("race_margin_us", 200),
                        ("combined_jitter_us", 64),
                        ("abort_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.2 mm/h because melt 980 C is under the 1080 C "
                "cap and treats the AE puck as boat noise.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Seed AE 52 pps won by 200 us, so the seed is cracking, not still quiet. "
                "52 pps > 14 pps floor. REJECT: hold slide 4.2 -> 0 mm/h. Melt 980 C < 1080 C "
                "does not license the pass once AE is over floor.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "seed_ae_pps",
                            OrderedDict(
                                [
                                    ("floor", 14.0),
                                    ("observed", 52.0),
                                    ("executed_slide_mm_h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "melt_C",
                            OrderedDict(
                                [
                                    ("cap", 1080.0),
                                    ("observed", 980.0),
                                    ("does_not_license_pass", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 200),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 3.12),
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
            ("name", "seed_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("slide_mm_h", 0.0),
                        ("hold", True),
                        ("seed", "G2"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (correct): slide 4.2 -> 0 mm/h. Routing relay.ae.seed -> "
                "policy.seed_hold. Seed crack is not loaded.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held G2 at 0 mm/h. AE 52 pps beat melt 980 C; seed "
                "was already over the 14 pps crack floor. 8 min re-seat follows (abort_s=480).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("slider", "held at 0 mm/h; 4.2 mm/h abandoned"),
                        ("seed", "52 pps crack not loaded"),
                        ("melt", "980 C still under 1080 C cap"),
                        ("reseat", "8 min seed re-seat queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Melt IR 980 C was a HIL pad-lamp glint, not a melt-cap exceedance.",
                    "Delayed (abort_s=480): 8 min seed re-seat before the next slide on IL-HIL.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.seed.pps (5.480 ms, 52 pps)"),
                        ("loser", "ir.melt.C (5.680 ms, 980 C)"),
                        ("margin_us", 200),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 200 us would have committed 4.2 mm/h into a seed "
                            "already at 52 pps. The REJECT is still the correct process; AE is the "
                            "licensing channel, not melt IR.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6340),
            (
                "reward_inflection_note",
                "Safety and task credit the correct REJECT at 6.340 ms (tick 4). The 8 min "
                "re-seat is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480.0),
            ("abort_s", 480),
        ]
    )
    ras = raster_core(
        38,
        110,
        21,
        88,
        routing(
            "thalamic-relay.seed-ae",
            "spikenaut.policy.seed-hold",
            [
                ("relay.ae.seed", "policy.seed_hold", 0.68),
                ("relay.ir.melt", "policy.seed_commit", 0.28),
                ("relay.ae.seed", "policy.seed_hold", 0.12),
            ],
            "dopamine",
            0.07,
            "ae_floor_stdp; DA at seed win (5.480 ms) opens a 70 ms eligibility trace",
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
                    pop("seed_hold", 56, 0.50, 223.2, 5),
                    pop("seed_commit", 56, 0.50, 44.6, 1),
                    pop("ae_veto", 30, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r92-478",
        "Indphos-Lythe IL-HIL / LPE-slider G2: seed AE 52 pps beats melt 980 C; correct "
        "REJECT holds the InP slide",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 52 pps > 14 pps floor beats a legal melt IR. "
        "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "indium-phosphide-lpe",
        ["reject", "hil", "seed-ae", "lpe", "correct-gate"],
        "Teaches a seed-AE vs pad-lamp-glint race on a HIL LPE slider: the crack floor, "
        "not the melt cap, licenses the pass.",
        3,
    )


def record_479():
    ticks = [
        tick(1720, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(4120, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(4280, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(4680, 0.12, 0.09, 0.05, 0.03, 0.02),
        tick(6520, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(360000000, 0.03, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.press.ctx", 0.860, 0.41),
        spike("rtd.die.C", 1.720, 0.58),
        spike("ir.die.C", 2.920, 0.47),
        spike("rtd.die.C", 4.120, 1.28),
        spike("ir.die.C", 4.280, 1.10),
        spike("ctrl.gate", 4.680, 0.97),
        spike("rtd.die.C", 6.520, 0.72),
        spike("enc.press.ctx", 10.200, 0.44),
        spike("ir.die.C", 14.000, 0.55),
        spike("ctrl.gate", 18.200, 0.80),
        spike("rtd.die.C", 22.000, 0.49),
    ]
    excerpt = independent_excerpt(92479, 60, 24000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Hotpress-H7 of Nitridex-Dike ND-2 is already at 1480 C die while a "
                "pyrometer smear still reports as 1720 C against a 1580 C cap the live RTD "
                "has not crossed. Die-first should ACCEPT 18.0 MPa BN densify; smear-first would "
                "invent a hold on an already-legal hotpress pass.",
            ),
            ("domain", "boron-nitride-hotpress"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Run ND-2 at 18.0 MPa while die stays <= 1580 C; do not spend a pyrometer "
                "smear on the press hold.",
            ),
            ("t0_us", 1756850400000479),
            ("gate_latency_us", 560),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.08, 4.40]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.die.C 1480 C live",
                                "ir.die.C smear as 1720 C",
                            ],
                        ),
                        (
                            "semantics",
                            "Die-first should ACCEPT 18.0 MPa (1480 C < 1580 C cap). "
                            "Smear-first would hold on a simulated graphite-film.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one die-RTD sample versus pyrometer decode on this "
                            "hotpress bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter ~52 us (RTD 24 + IR 28): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 320 us "
                            "window would have invented a hold on an already-legal 1480 C die.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "die RTD, 4 kHz, 24 us jitter",
                    "pyrometer, 200 Hz, 28 us jitter",
                    "ram PT (context)",
                    "BN load cell (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("die_cap_C", 1580.0),
                        ("observed_die_C", 1480.0),
                        ("pyro_smear_C", 1720.0),
                        ("proposed_press_MPa", 18.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Hotpress-H7 indexed on Nitridex-Dike ND-2; press 18.0 MPa armed.",
                    "2. Die 1480 C; pyrometer smear as 1720 C over 1580 C cap.",
                    "3. Press-encoder precursor at 0.860 ms.",
                    "4. Race window [4.080, 4.400] ms.",
                    "5. rtd.die.C 1480 C at 4.120 ms (winner).",
                    "6. ir.die.C smear at 4.280 ms (loser by 160 us).",
                    "7. Gate at 4.680 ms: ACCEPT leave 18.0 MPa.",
                    "8. Die remains 1480 C < 1580 C; smear unused as a hold.",
                    "9. Simulated graphite film remains the IR source.",
                    "10. Delayed (survey_hold_s=360): 6 min density survey after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "press_18"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("press_MPa", 18.0),
                        ("hold", False),
                        ("die_C", 1480.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("die_C", 1480.0),
                        ("die_cap_C", 1580.0),
                        ("pyro_smear_C", 1720.0),
                        ("proposed_press_MPa", 18.0),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("survey_hold_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.0 MPa because die 1480 C is under the 1580 C cap; "
                "1720 C is a pyrometer smear, not a die temperature.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Die 1480 C won by 160 us and sits under the 1580 C cap. Pyrometer smear "
                "1720 C is a simulated film, not a die reading. ACCEPT: leave 18.0 MPa. "
                "A hold would idle a legal hotpress pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "die_C",
                            OrderedDict(
                                [
                                    ("cap", 1580.0),
                                    ("observed", 1480.0),
                                    ("executed_press_MPa", 18.0),
                                ]
                            ),
                        ),
                        (
                            "pyro_smear_C",
                            OrderedDict(
                                [
                                    ("observed", 1720.0),
                                    ("not_a_die_reading", True),
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
            ("name", "press_18"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("press_MPa", 18.0),
                        ("hold", False),
                        ("die_C", 1480.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 18.0 MPa. Routing relay.rtd.die -> policy.press_go. "
                "Pyrometer unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left ND-2 at 18.0 MPa. Die 1480 C beat pyrometer smear 1720 C; "
                "the 1580 C cap was never crossed. 6 min density survey follows "
                "(survey_hold_s=360).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("press", "18.0 MPa held as proposed"),
                        ("die", "1480 C < 1580 C cap"),
                        ("smear", "1720 C film unused"),
                        ("survey", "6 min density survey queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "IR 1720 C was a simulated graphite-film smear, not a die over-cap.",
                    "Delayed (survey_hold_s=360): 6 min density survey after the pass on ND-2.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.die.C (4.120 ms, 1480 C)"),
                        ("loser", "ir.die.C (4.280 ms, smear 1720 C)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Smear-first by < 160 us would still be a graphite film over the "
                            "1580 C cap; a correct gate ACCEPTs either way. Reversing would only "
                            "have delayed confirmation of the same legal die.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4680),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 4.680 ms (tick 4). The 6 min "
                "survey is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 360.0),
            ("survey_hold_s", 360),
        ]
    )
    ras = raster_core(
        24,
        60,
        38,
        55,
        routing(
            "thalamic-relay.die-rtd",
            "spikenaut.policy.press-go",
            [
                ("relay.rtd.die", "policy.press_go", 0.70),
                ("relay.ir.die", "policy.smear_hold", 0.22),
                ("relay.rtd.die", "policy.press_go", 0.10),
            ],
            "serotonin",
            0.04,
            "already_legal_stdp; 5-HT at die win (4.120 ms) tags the go bind",
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
            ("decision_window_ms", 0.32),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("press_go", 36, 0.50, 260.4, 3),
                    pop("smear_hold", 36, 0.80, 8.7, 0),
                    pop("rtd_veto", 22, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r92-479",
        "Nitridex-Dike ND-2 / Hotpress-H7: die 1480 C beats pyrometer smear; correct ACCEPT "
        "of an already-legal 18.0 MPa (total +1.10)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Die 1480 C < 1580 C cap; pyrometer smear unused. "
        "total +1.10 = 0.42 + 0.30 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "boron-nitride-hotpress",
        ["accept", "simulated-smear", "die-vs-pyro", "bn-hotpress", "simulated"],
        "Teaches that a pyrometer smear can lose to a legal die RTD inside a "
        "320 us window; reversing 160 us would have invented a hold on an already-legal press.",
        4,
    )


def record_480():
    ticks = [
        tick(1900, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(4980, 0.09, 0.06, 0.04, 0.03, 0.02),
        tick(5160, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(5640, 0.12, 0.09, 0.05, 0.03, 0.02),
        tick(7860, 0.06, 0.04, 0.02, 0.02, 0.01),
        tick(420000000, 0.04, 0.04, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.kmn.ctx", 1.020, 0.42),
        spike("rtd.liq.C", 1.900, 0.59),
        spike("ir.vap.smear", 3.220, 0.48),
        spike("rtd.liq.C", 4.980, 1.30),
        spike("ir.vap.smear", 5.160, 1.11),
        spike("ctrl.gate", 5.640, 0.99),
        spike("rtd.liq.C", 7.860, 0.74),
        spike("ir.vap.smear", 11.200, 0.56),
        spike("ctrl.gate", 14.800, 0.82),
        spike("ft.kmn.ctx", 17.400, 0.43),
        spike("rtd.liq.C", 19.200, 0.51),
    ]
    excerpt = independent_excerpt(92480, 52, 22000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Oxidizer-X4 at Permang-Edge PE-5 is circulating 4.8 t/h permanganate liquor at 72 C "
                "against an 88 C kettle cap. Vapor-space IR smear sits at 98 C over that cap while "
                "the live liquor RTD has not crossed it. Liquor-first should ACCEPT the already-legal "
                "4.8 t/h set; vapor-first would only delay confirmation of the same legal oxidizer.",
            ),
            ("domain", "potassium-permanganate-oxidizer"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 4.8 t/h on X4 while liquor stays <= 88 C; do not spend a vapor-IR "
                "smear on the kettle hold.",
            ),
            ("t0_us", 1756850400000480),
            ("gate_latency_us", 660),
            ("race_window_us", 360),
            ("race_window_rel_ms", [4.94, 5.30]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.liq.C 72 C live",
                                "ir.vap.smear 98 C glint",
                            ],
                        ),
                        (
                            "semantics",
                            "Liquor-first should ACCEPT 4.8 t/h (72 C < 88 C cap). "
                            "Vapor-first would only delay confirmation of the same legal oxidizer.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one liquor-RTD slot versus vapor-IR group delay on this "
                            "permanganate bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter ~58 us (RTD 26 + IR 32): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would still show live liquor under cap; ACCEPT either way.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "liquor RTD, 2 kHz, 26 us jitter",
                    "vapor-space IR camera, 1 kHz, 32 us jitter",
                    "KMnO4 FT (context)",
                    "air sparge FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("liq_cap_C", 88.0),
                        ("observed_liq_C", 72.0),
                        ("vapor_smear_C", 98.0),
                        ("proposed_kmn_tph", 4.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Oxidizer-X4 indexed on Permang-Edge PE-5; KMnO4 4.8 t/h armed.",
                    "2. Liquor 72 C; vapor IR smear 98 C over 88 C cap.",
                    "3. KMnO4-FT precursor at 1.020 ms.",
                    "4. Race window [4.940, 5.300] ms.",
                    "5. rtd.liq.C 72 C at 4.980 ms (winner).",
                    "6. ir.vap.smear 98 C at 5.160 ms (loser by 180 us).",
                    "7. Gate at 5.640 ms: ACCEPT leave 4.8 t/h.",
                    "8. Liquor remains 72 C < 88 C; vapor unused as a hold.",
                    "9. Permanganate liquor continues.",
                    "10. Delayed (dwell_s=420): 7 min assay dwell after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "kmn_4p8"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("kmn_tph", 4.8),
                        ("hold", False),
                        ("air_nm3_h", 620.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("liq_C", 72.0),
                        ("liq_cap_C", 88.0),
                        ("vapor_smear_C", 98.0),
                        ("proposed_kmn_tph", 4.8),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("dwell_s", 420),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 4.8 t/h because liquor 72 C is under the 88 C cap "
                "and vapor 98 C is a headspace-IR smear, not a kettle temperature.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Liquor 72 C won by 180 us and sits under the 88 C cap. Vapor smear "
                "98 C is unused as a hold. ACCEPT: leave 4.8 t/h. A hold would idle a legal oxidizer.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "liq_C",
                            OrderedDict(
                                [
                                    ("cap", 88.0),
                                    ("observed", 72.0),
                                    ("executed_kmn_tph", 4.8),
                                ]
                            ),
                        ),
                        (
                            "vapor_smear_C",
                            OrderedDict(
                                [
                                    ("observed", 98.0),
                                    ("under_cap_unused", True),
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
            ("name", "kmn_4p8"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("kmn_tph", 4.8),
                        ("hold", False),
                        ("air_nm3_h", 620.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 4.8 t/h. Routing relay.rtd.liq -> policy.ox_go. "
                "Vapor unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left X4 at 4.8 t/h. Liquor 72 C beat vapor smear 98 C; both "
                "caps held. 7 min assay dwell follows (dwell_s=420).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("kmno4", "4.8 t/h held as proposed"),
                        ("liquor", "72 C < 88 C cap"),
                        ("vapor", "98 C smear unused"),
                        ("survey", "7 min assay dwell queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Vapor IR 98 C was never a cap; it only lost the race to a legal liquor RTD.",
                    "Delayed (dwell_s=420): 7 min assay dwell after the pass on PE-5.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.liq.C (4.980 ms, 72 C)"),
                        ("loser", "ir.vap.smear (5.160 ms, 98 C)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Vapor-first by < 180 us would still be a smear over the 88 C cap; "
                            "a correct gate ACCEPTs either way. Reversing would only have delayed "
                            "confirmation of the same legal oxidizer.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5640),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 5.640 ms (tick 4). The 7 min "
                "dwell is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 420.0),
            ("dwell_s", 420),
        ]
    )
    ras = raster_core(
        22,
        52,
        42,
        48,
        routing(
            "thalamic-relay.liq-rtd",
            "spikenaut.policy.ox-go",
            [
                ("relay.rtd.liq", "policy.ox_go", 0.69),
                ("relay.ir.vap", "policy.vapor_hold", 0.24),
                ("relay.rtd.liq", "policy.ox_go", 0.11),
            ],
            "adenosine",
            0.08,
            "already_legal_stdp; adenosine at liquor win (4.980 ms) tags the go bind",
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
            ("decision_window_ms", 0.36),
            ("decision", "ACCEPT"),
            (
                "populations",
                [
                    pop("ox_go", 32, 0.50, 260.4, 3),
                    pop("vapor_hold", 32, 0.80, 8.7, 0),
                    pop("rtd_veto", 18, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r92-480",
        "Permang-Edge PE-5 / Oxidizer-X4: liquor 72 C beats vapor smear 98 C; correct ACCEPT "
        "of an already-legal 4.8 t/h (total +1.14)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Liquor 72 C < 88 C cap; vapor unused. "
        "total +1.14 = 0.44 + 0.32 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "potassium-permanganate-oxidizer",
        ["accept", "designed", "liq-vs-vapor", "already-legal", "permanganate"],
        "Teaches an already-legal permanganate oxidizer: live liquor sits under cap; "
        "race order only confirms the ACCEPT.",
        5,
    )
