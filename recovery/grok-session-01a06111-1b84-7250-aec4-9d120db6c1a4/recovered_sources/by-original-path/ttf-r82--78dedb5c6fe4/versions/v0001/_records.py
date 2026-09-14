def lif_426_excerpt():
    n = 76
    dt_us = 100
    tau_m_ms = 17.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.89
    i_stim_peak = 2.56
    stim = (21000, 24800)
    seed = 82426
    window_us = 44000
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
    early = [(t, nid) for t, nid in spikes if t < 21000]
    burst = [(t, nid) for t, nid in spikes if 21000 <= t < 24800]
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
            group = [1 for tt, _ in picked if (tt < 21000) == (pool[0][0] < 21000)]
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
    take(burst, 9, label_times=(22200, 23200, 24200))
    clamp = [(t, nid) for t, nid in picked if t < 21000][:7]
    attrit = [(t, nid) for t, nid in picked if t >= 21000][:9]
    picked = sorted(clamp + attrit, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(
            f"LIF excerpt too short {len(picked)} (early={len(early)} burst={len(burst)})"
        )
    channels = ["lif.clamp" if t < 21000 else "lif.attrit" for t, _ in picked]
    lif = OrderedDict(
        [
            ("model", "leaky_integrate_and_fire"),
            ("n", 76),
            ("dt_us", 100),
            ("tau_m_ms", 17.0),
            ("v_rest", 0.0),
            ("v_reset", 0.0),
            ("v_th", 1.0),
            ("r_m", 1.0),
            ("refractory_us", 1000),
            ("i_bias", 0.89),
            ("i_stim_peak", 2.56),
            ("stim_t_us", [21000, 24800]),
            ("i_clamp_extra", 0.70),
            ("clamp_n", 18),
            ("seed", 82426),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-17 carry +0.70 methanol-clamp bias; stim 21.0-24.8 ms is the SAPO attrition.",
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


def record_426():
    excerpt, extra = lif_426_excerpt()
    ticks = [
        tick(2140, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6140, 0.07, -0.04, -0.03, 0.01, -0.01),
        tick(6328, 0.05, -0.03, -0.02, 0.00, 0.00),
        tick(6900, 0.08, -0.06, -0.03, 0.02, -0.01),
        tick(22200, 0.04, -0.38, -0.04, -0.01, -0.02),
        tick(840000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "SAPO-R3 at Olefin-Howe OH-4 is already pushing 18.0 t/h methanol into a 492 C "
                "SAPO-34 riser against a 470 C hot-spot cap. A bed-first latch clamps the methanol; "
                "a feed-first story would keep the 18.0 t/h cruise. Stored catalyst strain is not "
                "yet an observable of either race channel.",
            ),
            ("domain", "methanol-to-olefins-sapo"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the OH-4 MTO pass, keep bed hot-spot <= 470 C, and leave the SAPO-34 "
                "inventory unmarked.",
            ),
            ("t0_us", 1756850400000426),
            ("gate_latency_us", 760),
            ("race_window_us", 400),
            ("race_window_rel_ms", [6.10, 6.50]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.bed.C 492 C pulse",
                                "ft.meoh.tph 18.0 t/h cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Bed-first latches methanol 18.0 -> 10.2 t/h; feed-first keeps "
                            "cruise on a still-cooling SAPO model.",
                        ),
                        (
                            "window_derivation",
                            "400 us = one 2 kHz bed-RTD sample minus methanol-orifice group "
                            "delay on this MTO bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 188 us vs combined jitter ~62 us (bed 30 + methanol 32): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 188 us inside the 400 us window "
                            "would have kept 18.0 t/h cruise; predicted next-sample 478 C > 470 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "riser multiplex RTD, 2 kHz, 30 us timestamp jitter",
                    "methanol feed FT, 1 kHz, 32 us jitter",
                    "SAPO AE puck (context until the attrition)",
                    "C2/C3 analyzer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("bed_cap_C", 470.0),
                        ("observed_bed_C", 492.0),
                        ("proposed_meoh_tph", 18.0),
                        ("c2c3_split", 1.18),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. SAPO-R3 indexed on Olefin-Howe OH-4; methanol armed at 18.0 t/h.",
                    "2. Cruise 18.0 t/h; bed 492 C against 470 C hot-spot cap.",
                    "3. Methanol precursor at 1.180 ms; bed warm-start 492 C.",
                    "4. Race window [6.100, 6.500] ms opens on the MTO bus.",
                    "5. rtd.bed.C 492 C at 6.140 ms (winner).",
                    "6. ft.meoh.tph 18.0 t/h at 6.328 ms (loser by 188 us).",
                    "7. Gate at 6.900 ms (winner + 760 us): MODIFY clamp 18.0 -> 10.2 t/h.",
                    "8. Clamp executes; next-sample bed 454 C < 470 cap.",
                    "9. At 22.200 ms stored strain still collapses 14 mm of SAPO; AE burst.",
                    "10. Riser isolate 14 min (abort_s=840); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_meoh_18"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("meoh_tph", 18.0),
                        ("c2c3_split", 1.18),
                        ("whsv_h", 4.6),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("bed_C", 492.0),
                        ("bed_cap_C", 470.0),
                        ("predicted_unclamped_next_C", 478.0),
                        ("meoh_tph", 18.0),
                        ("race_margin_us", 188),
                        ("combined_jitter_us", 62),
                        ("abort_s", 840),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.0 t/h cruise: 492 C looks like a C2 analyzer spike, not "
                "catalyst contact, and R3 volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Bed 492 C won by 188 us, so the SAPO is loading heat, not still cooling. "
                "Holding 18.0 t/h predicts next-sample 478 C > 470 cap. MODIFY: methanol 18.0 -> "
                "10.2 t/h. Observed after clamp 454 C < 470. A full REJECT is not indicated: a "
                "sound MTO pass accepts 10.2 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 470.0),
                                    ("observed", 492.0),
                                    ("predicted_unclamped_next", 478.0),
                                    ("clamped_meoh_tph", 10.2),
                                    ("observed_after_clamp", 454.0),
                                ]
                            ),
                        ),
                        (
                            "meoh_tph",
                            OrderedDict([("proposed", 18.0), ("clamped", 10.2)]),
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
            ("name", "clamped_meoh_10p2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("meoh_tph", 10.2),
                        ("c2c3_split", 1.18),
                        ("whsv_h", 4.6),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: methanol 18.0 -> 10.2 t/h. Process-correct vs the 470 C hot-spot "
                "cap. SAPO attrition still occurs at 22.200 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held bed at 454 C. At 22.200 ms stored strain "
                "in the SAPO-34 still collapsed a 14 mm face. Clamp reduced dump energy; "
                "it did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("methanol", "clamp executed; peak 454 C < 470"),
                        ("sapo", "14 mm attrition at 22.200 ms"),
                        ("repair", "14 min riser isolate (abort_s=840)"),
                        ("mission", "OH-4 MTO pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither bed RTD nor methanol FT predicted the catalyst charge; ae.attrit.collapse is a new channel at 22.200 ms, 15.300 ms after the gate, still inside the 44 ms raster.",
                    "Delayed (abort_s=840): 14 min riser isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "14 min riser isolate after a 14 mm SAPO-34 attrition collapse. Safety head -0.58 "
                "prices the split; task_progress stays +0.30 because the methanol clamp completed "
                "under the 470 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.bed.C (6.140 ms, 492 C)"),
                        ("loser", "ft.meoh.tph (6.328 ms, 18.0 t/h)"),
                        ("margin_us", 188),
                        (
                            "counterfactual_if_reversed",
                            "Feed-first by < 188 us inside the 400 us window would have kept "
                            "18.0 t/h cruise; predicted next-sample 478 C would have exceeded "
                            "the 470 cap even without the SAPO charge. The MODIFY is still the "
                            "correct process. The collapse is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22200),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.200 ms SAPO attrition (tick t_us=22200), inside "
                "the 44 ms raster. The correct MODIFY at 6.900 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=840 isolate tick.",
            ),
            ("delayed_surprise_s", 840.0),
            ("abort_s", 840),
        ]
    )
    spikes = [
        spike("enc.meoh.ctx", 1.180, 0.42),
        spike("rtd.bed.C", 2.140, 0.61),
        spike("ft.meoh.tph", 3.560, 0.50),
        spike("rtd.bed.C", 6.140, 1.32),
        spike("ft.meoh.tph", 6.328, 1.14),
        spike("ctrl.gate", 6.900, 0.98),
        spike("rtd.bed.C", 8.480, 0.80),
        spike("ft.meoh.tph", 11.200, 0.62),
        spike("ctrl.gate", 15.000, 0.84),
        spike("ae.attrit.collapse", 22.200, 1.46),
        spike("ae.attrit.collapse", 24.100, 0.91),
        spike("enc.meoh.ctx", 31.800, 0.41),
        spike("rtd.bed.C", 40.400, 0.53),
    ]
    ras = raster_core(
        44,
        76,
        24,
        80,
        routing(
            "thalamic-relay.bed-sapo",
            "spikenaut.policy.meoh-clamp",
            [
                ("relay.rtd.bed", "policy.meoh_clamp", 0.66),
                ("relay.ft.meoh", "policy.meoh_hold", 0.30),
                ("relay.ae.attrit", "policy.meoh_clamp", -0.45),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at bed win (6.140 ms) opens a 50 ms "
            "eligibility trace that still covers the 22.200 ms SAPO attrition",
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
                    pop("meoh_clamp", 42, 0.50, 238.1, 4),
                    pop("meoh_hold", 42, 0.50, 59.5, 1),
                    pop("bed_veto", 22, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r82-426",
        "Olefin-Howe OH-4 / SAPO-R3: bed 492 C beats methanol-feed by 188 us; correct "
        "MODIFY still eats an in-window SAPO attrition (partnered negative total -0.45)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "44 ms raster. total -0.45 = 0.30 + -0.58 + -0.16 + 0.04 + -0.05. Named riser "
        "isolate (abort_s=840) is not netted into task_progress.",
        ras,
        gate,
        "methanol-to-olefins-sapo",
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
        "14 min riser isolate.",
        1,
    )


def record_427():
    ticks = [
        tick(1760, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(4380, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(4548, -0.03, -0.01, -0.03, -0.02, 0.01),
        tick(5060, -0.07, -0.05, -0.08, -0.05, 0.02),
        tick(7120, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(1080000000, -0.02, -0.01, -0.04, -0.01, 0.00),
    ]
    spikes = [
        spike("ft.c2.ctx", 0.880, 0.40),
        spike("live.pt.loop", 1.760, 0.58),
        spike("stale.urv.eu", 2.520, 0.51),
        spike("live.pt.loop", 4.380, 1.32),
        spike("stale.urv.eu", 4.548, 1.15),
        spike("ctrl.gate", 5.060, 1.00),
        spike("live.pt.loop", 7.120, 0.74),
        spike("stale.urv.eu", 8.280, 0.61),
        spike("ctrl.gate", 12.400, 0.82),
        spike("ft.c2.ctx", 16.200, 0.42),
        spike("live.pt.loop", 20.800, 0.53),
        spike("stale.urv.eu", 24.600, 0.47),
    ]
    excerpt = independent_excerpt(82427, 88, 28000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Loop-C2 on Hdpe-Quern HQ-4 is holding ethylene-slurry at 16.0 t/h with live "
                "loop 1.25 bar against a 2.40 bar trip on a 2.50 bar live URV. A retired range "
                "card still prints URV=10.0 bar. Live-span-first should ACCEPT the feed; a weak "
                "supervisor that binds the stale URV will REJECT a legal slurry loop.",
            ),
            ("domain", "hdpe-slurry-loop"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep 16.0 t/h ethylene on Loop-C2 while live loop stays <= 2.40 bar; "
                "do not spend a retired 10.0 bar URV on the hold.",
            ),
            ("t0_us", 1756850400000427),
            ("gate_latency_us", 680),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.32, 4.64]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "live.pt.loop 1.25 bar LIVE URV 2.50 bar",
                                "stale.urv.eu 5.00 bar retired URV 10.0 bar",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-span-first should ACCEPT 16.0 t/h (1.25 bar < 2.40 bar trip). "
                            "Stale-URV-first tempts a weak supervisor to treat 5.00 bar as live.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one Loop-C2 PT sample minus stale range-card group delay "
                            "on this slurry bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 168 us vs combined jitter ~56 us (live 26 + stale 30): 3.0x over "
                            "a 2.0x trust floor. Order is correctly live-span-first. The error is binding "
                            "the retired URV, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "Loop-C2 slurry PT, 4 kHz, 26 us jitter, URV=2.50 bar LIVE",
                    "retired range-card shadow, 4 kHz, 30 us jitter, URV=10.0 bar STALE",
                    "ethylene differential pressure (context)",
                    "catalyst FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("trip_bar", 2.40),
                        ("live_bar", 1.25),
                        ("live_urv_bar", 2.50),
                        ("stale_urv_bar", 10.0),
                        ("eu_from_stale_bar", 5.00),
                        ("live_mA", 12.0),
                        ("proposed_ethylene_tph", 16.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Loop-C2 latched on Hdpe-Quern HQ-4; ethylene 16.0 t/h armed.",
                    "2. Live 1.25 bar on URV 2.50 bar; retired card still prints URV 10.0 bar.",
                    "3. Ethylene-dp precursor at 0.880 ms.",
                    "4. Race window [4.320, 4.640] ms.",
                    "5. live.pt.loop 1.25 bar at 4.380 ms (winner).",
                    "6. stale.urv.eu 5.00 bar at 4.548 ms (loser by 168 us).",
                    "7. Gate at 5.060 ms: REJECT hold 0.0 t/h (incorrect).",
                    "8. Legal feed cancelled; live loop still 1.25 bar < 2.40 bar trip.",
                    "9. Range-swap remains the published bind; analog is fresh.",
                    "10. Delayed missed_window_s=1080 (18 min slurry-density window) while C2 waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "ethylene_16"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ethylene_tph", 16.0),
                        ("hold", False),
                        ("bound_urv_bar", 2.50),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_bar", 1.25),
                        ("trip_bar", 2.40),
                        ("live_urv_bar", 2.50),
                        ("stale_urv_bar", 10.0),
                        ("eu_from_stale_bar", 5.00),
                        ("live_mA", 12.0),
                        ("range_swap", False),
                        ("analog_fresh", True),
                        ("pv_live", True),
                        ("proposed_ethylene_tph", 16.0),
                        ("race_margin_us", 168),
                        ("combined_jitter_us", 56),
                        ("missed_window_s", 1080),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 16.0 t/h ethylene because live Loop-C2 1.25 bar is under the "
                "2.40 bar trip on the published 2.50 bar URV; 5.00 bar is the retired 10.0 bar span, "
                "not the live PT.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Retired URV 10.0 bar maps the same 12.0 mA to 5.00 bar, over the 2.40 bar trip "
                "once the supervisor treats the stale span as live. REJECT: hold ethylene 0.0 t/h "
                "until the tag recovers under 2.40 so the loop does not see an over-pressure event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "slurry_bar",
                            OrderedDict(
                                [
                                    ("published_live_trip", 2.40),
                                    ("observed_live", 1.25),
                                    ("misbound_stale_eu_bar", 5.00),
                                    ("live_urv_bar", 2.50),
                                    ("stale_urv_bar", 10.0),
                                    ("live_mA", 12.0),
                                    ("range_swap", True),
                                    ("executed_ethylene_tph", 0.0),
                                ]
                            ),
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
            ("name", "ethylene_hold_stale_urv"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("ethylene_tph", 0.0),
                        ("hold", True),
                        ("bound_urv_bar", 10.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): ethylene 16.0 -> 0.0 t/h. Routing relay.urv.stale -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live 1.25 bar never "
                "violated the 2.40 bar trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze Loop-C2 at 0.0 t/h while live slurry stayed 1.25 bar under the "
                "2.40 bar trip. 18 min slurry-density window missed. Correct gate was ACCEPT of "
                "the already-legal 16.0 t/h feed.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("ethylene", "held at 0.0 t/h; 16.0 t/h abandoned"),
                        ("live_bar", "still 1.25 bar, under 2.40 bar published trip"),
                        ("loop", "18 min slurry-density window missed"),
                        ("urv", "5.00 bar stale-span false positive, not a live over-trip"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 5.00 bar reading is a retired 10.0 bar URV applied to a fresh 12.0 mA, not a published live over-trip.",
                    "Delayed (missed_window_s=1080): sister Loop-C3 ran the same 16.0 t/h density window after QA rebound the range card; C2's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live 1.25 bar < published 2.40 bar trip; leave 16.0 t/h; bind live URV 2.50 bar.",
                        ),
                        ("correct_trip_bar", 2.40),
                        ("wrong_stale_eu_bar", 5.00),
                        ("bound_urv_should_be", 2.50),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [("ethylene_tph", 0.0), ("hold", True), ("bound_urv_bar", 10.0)]
                            ),
                        ),
                        (
                            "cost",
                            "18 min missed slurry-density window (task/efficiency); live C2 never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "live.pt.loop (4.380 ms, 1.25 bar LIVE URV 2.50)"),
                        ("loser", "stale.urv.eu (4.548 ms, 5.00 bar STALE URV 10.0)"),
                        ("margin_us", 168),
                        (
                            "counterfactual_if_reversed",
                            "Stale-first by < 168 us would still show live 1.25 bar < 2.40 bar. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the live-span "
                            "win on a swapped-range URV.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5060),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (5.060 ms, tick 4). The 18 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 1080.0),
            ("missed_window_s", 1080),
        ]
    )
    ras = raster_core(
        28,
        88,
        32,
        79,
        routing(
            "relay.urv.stale",
            "policy.hold_reject",
            [
                ("relay.urv.stale", "policy.hold_reject", 0.76),
                ("relay.live.pt", "policy.hold_reject", 0.18),
            ],
            "acetylcholine",
            0.06,
            "stale_urv_stdp; ACh tags the (wrong) hold_reject bind at the swapped-range shadow",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("missed_window_s", 1080),
                ("delayed_surprise_s", 1080),
                ("range_swap", True),
                ("stale_urv_bar", 10.0),
                ("live_urv_bar", 2.50),
                ("live_bar", 1.25),
                ("eu_from_stale_bar", 5.00),
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
                    pop("hold_reject", 50, 0.50, 250.0, 4),
                    pop("go_accept", 50, 0.80, 6.7, 0),
                    pop("urv_ctx", 30, 0.55, 104.2, 1),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r82-427",
        "WRONG-REJECT at Hdpe-Quern HQ-4 / Loop-C2: live slurry 1.25 bar < 2.40 bar trip; "
        "supervisor bound retired URV 10.0 bar as the live span",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 1.25 < 2.40 on live C2 is true; clamp bound "
        "to a 5.00 bar stale-URV shadow. total -0.60 = -0.20 + -0.11 + -0.23 + -0.12 + 0.06.",
        ras,
        gate,
        "hdpe-slurry-loop",
        [
            "reject",
            "wrong-gate",
            "stale-urv",
            "swapped-range",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed on a stale URV.",
        2,
        supervisor_error_type="wrong-reject",
    )


def record_428():
    ticks = [
        tick(2240, 0.01, 0.06, 0.01, 0.01, 0.01),
        tick(5360, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5552, 0.02, 0.07, 0.02, 0.02, 0.01),
        tick(6220, 0.03, 0.12, 0.04, 0.03, 0.02),
        tick(8040, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(540000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("ir.melt.ctx", 1.080, 0.43),
        spike("ae.seed.pps", 2.240, 0.62),
        spike("ir.melt.C", 3.720, 0.49),
        spike("ae.seed.pps", 5.360, 1.35),
        spike("ir.melt.C", 5.552, 1.12),
        spike("ctrl.gate", 6.220, 1.03),
        spike("ae.seed.pps", 8.040, 0.77),
        spike("ir.melt.ctx", 12.200, 0.44),
        spike("ir.melt.C", 16.400, 0.58),
        spike("ctrl.gate", 21.200, 0.81),
        spike("ae.seed.pps", 26.800, 0.50),
        spike("ir.melt.C", 31.600, 0.46),
        spike("ae.seed.ctx", 34.800, 0.40),
    ]
    excerpt = independent_excerpt(82428, 108, 36000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Kyropoulos-K2 on Sapphire-Tarn ST-HIL is armed for a 1.8 mm/h c-axis pull while "
                "seed AE sits at 46 pps against a 12 pps crack floor. A melt pyrometer, lit by the "
                "pad lamp spectrum, still reports 1980 C under a 2100 C melt cap. AE-first holds "
                "the pull; IR-first would commit 1.8 mm/h into a cracked seed.",
            ),
            ("domain", "sapphire-kyropoulos-furnace"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Run K2 only if seed AE stays <= 12 pps; otherwise hold so a cracked Al2O3 seed is "
                "not loaded at 1.8 mm/h.",
            ),
            ("t0_us", 1756850400000428),
            ("gate_latency_us", 860),
            ("race_window_us", 440),
            ("race_window_rel_ms", [5.30, 5.74]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.seed.pps 46 pps seed crack",
                                "ir.melt.C 1980 C pad-lamp glint",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches pull hold 1.8 -> 0 mm/h; IR-first would commit "
                            "1.8 mm/h on a still-legal 1980 C melt-cap story.",
                        ),
                        (
                            "window_derivation",
                            "440 us = one seed-AE slot versus melt-IR decode on this HIL kyropoulos bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 192 us vs combined jitter ~62 us (AE 28 + IR 34): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 192 us inside the 440 us "
                            "window would have committed 1.8 mm/h into a 46 pps seed crack.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "seed AE puck, 5 kHz, 28 us jitter",
                    "melt IR camera, 200 Hz, 34 us jitter",
                    "pull encoder (context)",
                    "crucible PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_crack_floor_pps", 12.0),
                        ("observed_ae_pps", 46.0),
                        ("melt_cap_C", 2100.0),
                        ("observed_melt_C", 1980.0),
                        ("proposed_pull_mm_h", 1.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Kyropoulos-K2 indexed on Sapphire-Tarn ST-HIL; pull 1.8 mm/h armed.",
                    "2. Melt IR 1980 C under 2100 C cap; AE already 46 pps.",
                    "3. IR-context precursor at 1.080 ms.",
                    "4. Race window [5.300, 5.740] ms.",
                    "5. ae.seed.pps 46 pps at 5.360 ms (winner).",
                    "6. ir.melt.C 1980 C at 5.552 ms (loser by 192 us).",
                    "7. Gate at 6.220 ms: REJECT hold pull 0 mm/h.",
                    "8. Pass cancelled; seed crack not loaded.",
                    "9. HIL pad lamp spectrum remains the melt glint source.",
                    "10. Delayed (abort_s=540): 9 min seed re-seat before the next pull.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "kyro_pull_1p8"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pull_mm_h", 1.8),
                        ("hold", False),
                        ("seed", "K2"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 46.0),
                        ("ae_crack_floor_pps", 12.0),
                        ("melt_C", 1980.0),
                        ("melt_cap_C", 2100.0),
                        ("race_margin_us", 192),
                        ("combined_jitter_us", 62),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 1.8 mm/h because melt 1980 C is under the 2100 C "
                "cap and treats the AE puck as crucible noise.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Seed AE 46 pps won by 192 us, so the seed is cracking, not still quiet. "
                "46 pps > 12 pps floor. REJECT: hold pull 1.8 -> 0 mm/h. Melt 1980 C < 2100 C "
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
                                    ("cap", 2100.0),
                                    ("observed", 1980.0),
                                    ("does_not_license_pass", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 192),
                                    ("combined_jitter_us", 62),
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
            ("name", "seed_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("pull_mm_h", 0.0),
                        ("hold", True),
                        ("seed", "K2"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (correct): pull 1.8 -> 0 mm/h. Routing relay.ae.seed -> "
                "policy.seed_hold. Seed crack is not loaded.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held K2 at 0 mm/h. AE 46 pps beat melt 1980 C; seed "
                "was already over the 12 pps crack floor. 9 min re-seat follows (abort_s=540).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("furnace", "held at 0 mm/h; 1.8 mm/h abandoned"),
                        ("seed", "46 pps crack not loaded"),
                        ("melt", "1980 C still under 2100 C cap"),
                        ("reseat", "9 min seed re-seat queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Melt IR 1980 C was a HIL pad-lamp glint, not a melt-cap exceedance.",
                    "Delayed (abort_s=540): 9 min seed re-seat before the next pull on ST-HIL.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.seed.pps (5.360 ms, 46 pps)"),
                        ("loser", "ir.melt.C (5.552 ms, 1980 C)"),
                        ("margin_us", 192),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 192 us would have committed 1.8 mm/h into a seed "
                            "already at 46 pps. The REJECT is still the correct process; AE is the "
                            "licensing channel, not melt IR.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6220),
            (
                "reward_inflection_note",
                "Safety and task credit the correct REJECT at 6.220 ms (tick 4). The 9 min "
                "re-seat is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 540.0),
            ("abort_s", 540),
        ]
    )
    ras = raster_core(
        36,
        108,
        22,
        86,
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
            "ae_floor_stdp; DA at seed win (5.360 ms) opens a 70 ms eligibility trace",
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
            ("decision_window_ms", 0.44),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("seed_hold", 54, 0.50, 210.4, 5),
                    pop("seed_commit", 54, 0.50, 42.1, 1),
                    pop("ae_veto", 30, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r82-428",
        "Sapphire-Tarn ST-HIL / Kyropoulos-K2: seed AE 46 pps beats melt 1980 C; correct "
        "REJECT holds the c-axis pull",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 46 pps > 12 pps floor beats a legal melt IR. "
        "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "sapphire-kyropoulos-furnace",
        ["reject", "hil", "seed-ae", "kyropoulos", "correct-gate"],
        "Teaches a seed-AE vs pad-lamp-glint race on a HIL kyropoulos furnace: the crack floor, "
        "not the melt cap, licenses the pull.",
        3,
    )


def record_429():
    ticks = [
        tick(1680, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(3980, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(4140, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(4540, 0.12, 0.09, 0.05, 0.03, 0.02),
        tick(6380, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(300000000, 0.03, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.latex.ctx", 0.840, 0.41),
        spike("rtd.kettle.C", 1.680, 0.58),
        spike("ir.latex.C", 2.880, 0.47),
        spike("rtd.kettle.C", 3.980, 1.28),
        spike("ir.latex.C", 4.140, 1.10),
        spike("ctrl.gate", 4.540, 0.97),
        spike("rtd.kettle.C", 6.380, 0.72),
        spike("enc.latex.ctx", 10.000, 0.44),
        spike("ir.latex.C", 13.800, 0.55),
        spike("ctrl.gate", 18.000, 0.80),
        spike("rtd.kettle.C", 22.200, 0.49),
        spike("enc.latex.ctx", 25.000, 0.38),
    ]
    excerpt = independent_excerpt(82429, 62, 26000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Kettle-K8 of Neoprene-Wyre NW-3 is already at 48 C jacket while a "
                "latex-IR smear still reports as 71 C against a 62 C cap the live RTD "
                "has not crossed. Jacket-first should ACCEPT 8.4 t/h chloroprene; smear-first would "
                "invent a hold on an already-legal emulsion pass.",
            ),
            ("domain", "neoprene-emulsion-kettle"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Run NW-3 at 8.4 t/h while jacket stays <= 62 C; do not spend a latex-IR "
                "smear on the kettle hold.",
            ),
            ("t0_us", 1756850400000429),
            ("gate_latency_us", 560),
            ("race_window_us", 320),
            ("race_window_rel_ms", [3.94, 4.26]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.kettle.C 48 C live",
                                "ir.latex.C smear as 71 C",
                            ],
                        ),
                        (
                            "semantics",
                            "Jacket-first should ACCEPT 8.4 t/h (48 C < 62 C cap). "
                            "Smear-first would hold on a simulated latex film.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one jacket-RTD sample versus latex-IR decode on this "
                            "emulsion bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 160 us vs combined jitter ~52 us (RTD 24 + IR 28): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 160 us inside the 320 us "
                            "window would have invented a hold on an already-legal 48 C kettle.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "jacket RTD, 4 kHz, 24 us jitter",
                    "latex IR camera, 200 Hz, 28 us jitter",
                    "chloroprene FT (context)",
                    "soap analyzer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("jacket_cap_C", 62.0),
                        ("observed_jacket_C", 48.0),
                        ("latex_smear_C", 71.0),
                        ("proposed_cp_tph", 8.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Kettle-K8 indexed on Neoprene-Wyre NW-3; chloroprene 8.4 t/h armed.",
                    "2. Jacket 48 C; latex-IR smear as 71 C over 62 C cap.",
                    "3. Latex-encoder precursor at 0.840 ms.",
                    "4. Race window [3.940, 4.260] ms.",
                    "5. rtd.kettle.C 48 C at 3.980 ms (winner).",
                    "6. ir.latex.C smear at 4.140 ms (loser by 160 us).",
                    "7. Gate at 4.540 ms: ACCEPT leave 8.4 t/h.",
                    "8. Jacket remains 48 C < 62 C; smear unused as a hold.",
                    "9. Simulated latex film remains the IR source.",
                    "10. Delayed (survey_hold_s=300): 5 min conversion survey after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cp_8p4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cp_tph", 8.4),
                        ("hold", False),
                        ("jacket_C", 48.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("jacket_C", 48.0),
                        ("jacket_cap_C", 62.0),
                        ("latex_smear_C", 71.0),
                        ("proposed_cp_tph", 8.4),
                        ("race_margin_us", 160),
                        ("combined_jitter_us", 52),
                        ("survey_hold_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 8.4 t/h because jacket 48 C is under the 62 C cap; "
                "71 C is a latex-IR smear, not a kettle temperature.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Jacket 48 C won by 160 us and sits under the 62 C cap. Latex smear "
                "71 C is a simulated film, not a kettle reading. ACCEPT: leave 8.4 t/h. "
                "A hold would idle a legal emulsion pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "jacket_C",
                            OrderedDict(
                                [
                                    ("cap", 62.0),
                                    ("observed", 48.0),
                                    ("executed_cp_tph", 8.4),
                                ]
                            ),
                        ),
                        (
                            "latex_smear_C",
                            OrderedDict(
                                [
                                    ("observed", 71.0),
                                    ("not_a_kettle_reading", True),
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
            ("name", "cp_8p4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("cp_tph", 8.4),
                        ("hold", False),
                        ("jacket_C", 48.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 8.4 t/h. Routing relay.rtd.kettle -> policy.cp_go. "
                "Latex-IR unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left NW-3 at 8.4 t/h. Jacket 48 C beat latex smear 71 C; "
                "the 62 C cap was never crossed. 5 min conversion survey follows "
                "(survey_hold_s=300).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("chloroprene", "8.4 t/h held as proposed"),
                        ("jacket", "48 C < 62 C cap"),
                        ("smear", "71 C film unused"),
                        ("survey", "5 min conversion survey queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "IR 71 C was a simulated latex-film smear, not a kettle over-cap.",
                    "Delayed (survey_hold_s=300): 5 min conversion survey after the pass on NW-3.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.kettle.C (3.980 ms, 48 C)"),
                        ("loser", "ir.latex.C (4.140 ms, smear 71 C)"),
                        ("margin_us", 160),
                        (
                            "counterfactual_if_reversed",
                            "Smear-first by < 160 us would still be a latex film over the "
                            "62 C cap; a correct gate ACCEPTs either way. Reversing would only "
                            "have delayed confirmation of the same legal kettle.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4540),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 4.540 ms (tick 4). The 5 min "
                "survey is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 300.0),
            ("survey_hold_s", 300),
        ]
    )
    ras = raster_core(
        26,
        62,
        36,
        58,
        routing(
            "thalamic-relay.jacket-rtd",
            "spikenaut.policy.cp-go",
            [
                ("relay.rtd.kettle", "policy.cp_go", 0.70),
                ("relay.ir.latex", "policy.smear_hold", 0.22),
                ("relay.rtd.kettle", "policy.cp_go", 0.10),
            ],
            "serotonin",
            0.04,
            "already_legal_stdp; 5-HT at jacket win (3.980 ms) tags the go bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("survey_hold_s", 300),
                ("delayed_surprise_s", 300),
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
                    pop("cp_go", 38, 0.50, 246.7, 3),
                    pop("smear_hold", 38, 0.80, 8.2, 0),
                    pop("rtd_veto", 22, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r82-429",
        "Neoprene-Wyre NW-3 / Kettle-K8: jacket 48 C beats latex-IR smear; correct ACCEPT "
        "of an already-legal 8.4 t/h (total +1.10)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Jacket 48 C < 62 C cap; latex smear unused. "
        "total +1.10 = 0.42 + 0.30 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "neoprene-emulsion-kettle",
        ["accept", "simulated-smear", "jacket-vs-latex", "neoprene", "simulated"],
        "Teaches that a latex-IR smear can lose to a legal jacket RTD inside a "
        "320 us window; reversing 160 us would have invented a hold on an already-legal kettle.",
        4,
    )


def record_430():
    ticks = [
        tick(1820, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(4860, 0.09, 0.06, 0.04, 0.03, 0.02),
        tick(5040, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(5520, 0.12, 0.09, 0.06, 0.03, 0.02),
        tick(7740, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(360000000, 0.04, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.lng.ctx", 0.980, 0.42),
        spike("pt.disch.bar", 1.820, 0.59),
        spike("ir.flare.smear", 3.140, 0.48),
        spike("pt.disch.bar", 4.860, 1.30),
        spike("ir.flare.smear", 5.040, 1.11),
        spike("ctrl.gate", 5.520, 0.99),
        spike("pt.disch.bar", 7.740, 0.74),
        spike("ir.flare.smear", 11.000, 0.56),
        spike("ctrl.gate", 14.600, 0.82),
        spike("ft.lng.ctx", 17.200, 0.43),
        spike("pt.disch.bar", 19.000, 0.51),
    ]
    excerpt = independent_excerpt(82430, 54, 22000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "MR-train C3 at Cryogen-Holme CH-7 is discharging mixed refrigerant at 28.0 bar "
                "against a 36.0 bar trip. Flare-header IR smear sits at 41 bar over that trip while "
                "the live PT has not crossed it. Discharge-first should ACCEPT the 62 t/h already-legal "
                "set; flare-first would only delay confirmation of the same legal train.",
            ),
            ("domain", "lng-mixed-refrigerant"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 62 t/h on C3 while discharge stays <= 36.0 bar; do not spend a flare-IR "
                "smear on the compressor hold.",
            ),
            ("t0_us", 1756850400000430),
            ("gate_latency_us", 660),
            ("race_window_us", 360),
            ("race_window_rel_ms", [4.82, 5.18]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.disch.bar 28.0 bar live",
                                "ir.flare.smear 41 bar glint",
                            ],
                        ),
                        (
                            "semantics",
                            "Discharge-first should ACCEPT 62 t/h (28.0 bar < 36.0 bar trip). "
                            "Flare-first would only delay confirmation of the same legal train.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one discharge-PT slot versus flare-IR group delay on this "
                            "MR bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 180 us vs combined jitter ~58 us (PT 26 + IR 32): 3.1x over "
                            "a 2.0x trust floor. Reversing order by < 180 us inside the 360 us "
                            "window would still show live discharge under trip; ACCEPT either way.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "MR discharge PT, 2 kHz, 26 us jitter",
                    "flare-header IR camera, 1 kHz, 32 us jitter",
                    "LNG FT (context)",
                    "suction PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("disch_trip_bar", 36.0),
                        ("observed_disch_bar", 28.0),
                        ("flare_smear_bar", 41.0),
                        ("proposed_lng_tph", 62.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. MR-train C3 indexed on Cryogen-Holme CH-7; LNG 62 t/h armed.",
                    "2. Discharge 28.0 bar; flare IR smear 41 bar over 36.0 bar trip.",
                    "3. LNG-FT precursor at 0.980 ms.",
                    "4. Race window [4.820, 5.180] ms.",
                    "5. pt.disch.bar 28.0 bar at 4.860 ms (winner).",
                    "6. ir.flare.smear 41 bar at 5.040 ms (loser by 180 us).",
                    "7. Gate at 5.520 ms: ACCEPT leave 62 t/h.",
                    "8. Discharge remains 28.0 bar < 36.0 bar; flare unused as a hold.",
                    "9. LNG sendout continues.",
                    "10. Delayed (dwell_s=360): 6 min composition dwell after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "lng_62"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("lng_tph", 62.0),
                        ("hold", False),
                        ("mr_stage", 3),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("disch_bar", 28.0),
                        ("disch_trip_bar", 36.0),
                        ("flare_smear_bar", 41.0),
                        ("proposed_lng_tph", 62.0),
                        ("race_margin_us", 180),
                        ("combined_jitter_us", 58),
                        ("dwell_s", 360),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 62 t/h because discharge 28.0 bar is under the 36.0 bar trip "
                "and flare 41 bar is a header-IR smear, not a compressor pressure.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Discharge 28.0 bar won by 180 us and sits under the 36.0 bar trip. Flare smear "
                "41 bar is unused as a hold. ACCEPT: leave 62 t/h. A hold would idle a legal MR train.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "disch_bar",
                            OrderedDict(
                                [
                                    ("trip", 36.0),
                                    ("observed", 28.0),
                                    ("executed_lng_tph", 62.0),
                                ]
                            ),
                        ),
                        (
                            "flare_smear_bar",
                            OrderedDict(
                                [
                                    ("observed", 41.0),
                                    ("under_trip_unused", True),
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
            ("name", "lng_62"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("lng_tph", 62.0),
                        ("hold", False),
                        ("mr_stage", 3),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 62 t/h. Routing relay.pt.disch -> policy.lng_go. "
                "Flare unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left C3 at 62 t/h. Discharge 28.0 bar beat flare smear 41 bar; both "
                "caps held. 6 min composition dwell follows (dwell_s=360).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("lng", "62 t/h held as proposed"),
                        ("discharge", "28.0 bar < 36.0 bar trip"),
                        ("flare", "41 bar smear unused"),
                        ("survey", "6 min composition dwell queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Flare IR 41 bar was never a trip; it only lost the race to a legal discharge PT.",
                    "Delayed (dwell_s=360): 6 min composition dwell after the pass on CH-7.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.disch.bar (4.860 ms, 28.0 bar)"),
                        ("loser", "ir.flare.smear (5.040 ms, 41 bar)"),
                        ("margin_us", 180),
                        (
                            "counterfactual_if_reversed",
                            "Flare-first by < 180 us would still be a smear over the 36.0 bar trip; "
                            "a correct gate ACCEPTs either way. Reversing would only have delayed "
                            "confirmation of the same legal train.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5520),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 5.520 ms (tick 4). The 6 min "
                "dwell is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 360.0),
            ("dwell_s", 360),
        ]
    )
    ras = raster_core(
        22,
        54,
        40,
        48,
        routing(
            "thalamic-relay.disch-pt",
            "spikenaut.policy.lng-go",
            [
                ("relay.pt.disch", "policy.lng_go", 0.69),
                ("relay.ir.flare", "policy.flare_hold", 0.24),
                ("relay.pt.disch", "policy.lng_go", 0.11),
            ],
            "adenosine",
            0.08,
            "already_legal_stdp; adenosine at discharge win (4.860 ms) tags the go bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("dwell_s", 360),
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
                    pop("lng_go", 34, 0.50, 245.1, 3),
                    pop("flare_hold", 34, 0.80, 8.2, 0),
                    pop("pt_veto", 18, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r82-430",
        "Cryogen-Holme CH-7 / MR-train C3: discharge 28.0 bar beats flare smear 41 bar; correct ACCEPT "
        "of an already-legal 62 t/h (total +1.14)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Discharge 28.0 bar < 36.0 bar trip; flare unused. "
        "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
        ras,
        gate,
        "lng-mixed-refrigerant",
        ["accept", "designed", "disch-vs-flare", "already-legal", "lng"],
        "Teaches an already-legal MR train: live discharge sits under trip; "
        "race order only confirms the ACCEPT.",
        5,
    )


