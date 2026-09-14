def lif_436_excerpt():
    n = 78
    dt_us = 100
    tau_m_ms = 17.0
    v_th = 1.0
    v_reset = 0.0
    refractory_us = 1000
    i_bias = 0.89
    i_stim_peak = 2.56
    stim = (21200, 24800)
    seed = 84386
    window_us = 44000
    i_clamp_extra = 0.68
    clamp_n = 16
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
    burst = [(t, nid) for t, nid in spikes if 21200 <= t < 24800]
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
    take(burst, 9, label_times=(22200, 23200, 24200))
    clamp = [(t, nid) for t, nid in picked if t < 21200][:7]
    pack = [(t, nid) for t, nid in picked if t >= 21200][:9]
    picked = sorted(clamp + pack, key=lambda item: (item[0], item[1]))
    if len(picked) < 8:
        raise ValueError(
            f"LIF excerpt too short {len(picked)} (early={len(early)} burst={len(burst)})"
        )
    channels = ["lif.clamp" if t < 21200 else "lif.gasket" for t, _ in picked]
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
            ("stim_t_us", [21200, 24800]),
            ("i_clamp_extra", 0.68),
            ("clamp_n", 16),
            ("seed", 84386),
            (
                "note",
                "Population sim scoped to this sidecar. Plant remains designed. "
                "Neurons 0-15 carry +0.68 salt-clamp bias; stim 21.2-24.8 ms is the gasket blow.",
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


def record_436():
    excerpt, extra = lif_436_excerpt()
    ticks = [
        tick(2340, 0.04, -0.02, -0.02, 0.01, 0.00),
        tick(6120, 0.07, -0.04, -0.03, 0.01, -0.01),
        tick(6304, 0.05, -0.03, -0.02, 0.00, 0.00),
        tick(6880, 0.08, -0.06, -0.03, 0.02, -0.01),
        tick(22200, 0.04, -0.38, -0.04, -0.01, -0.02),
        tick(900000000, 0.02, -0.05, -0.02, 0.01, -0.01),
    ]
    state = OrderedDict(
        [
            (
                "description",
                "AH-salt autoclave AH-6 at Spinelle-Wath SW-4 is already feeding 16.0 t/h nylon-66 "
                "salt into a 278 C wall against a 265 C metal-temperature cap. A wall-first latch "
                "clamps the salt; a feed-first story would keep the 16.0 t/h cruise. Stored gasket "
                "strain is not yet an observable of either race channel.",
            ),
            ("domain", "nylon-66-salt-autoclave"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Finish the SW-4 AH-salt pass, keep autoclave wall <= 265 C, and leave the lid "
                "gasket unmarked.",
            ),
            ("t0_us", 1756850400000436),
            ("gate_latency_us", 760),
            ("race_window_us", 380),
            ("race_window_rel_ms", [6.08, 6.46]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "rtd.wall.C 278 C pulse",
                                "ft.salt.tph 16.0 t/h cruise",
                            ],
                        ),
                        (
                            "semantics",
                            "Wall-first latches salt 16.0 -> 8.4 t/h; feed-first keeps "
                            "cruise on a still-cooling gasket model.",
                        ),
                        (
                            "window_derivation",
                            "380 us = one 2 kHz wall-RTD sample minus salt-orifice group "
                            "delay on this autoclave bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 184 us vs combined jitter ~62 us (wall 28 + salt 34): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 184 us inside the 380 us window "
                            "would have kept 16.0 t/h cruise; predicted next-sample 271 C > 265 cap.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "wall multiplex RTD, 2 kHz, 28 us timestamp jitter",
                    "AH-salt feed FT, 1 kHz, 34 us jitter",
                    "lid-gasket AE puck (context until the blow)",
                    "condensate analyzer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("wall_cap_C", 265.0),
                        ("observed_wall_C", 278.0),
                        ("proposed_salt_tph", 16.0),
                        ("steam_tph", 4.8),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. AH-6 indexed on Spinelle-Wath SW-4; AH-salt armed at 16.0 t/h.",
                    "2. Cruise 16.0 t/h; wall 278 C against 265 C metal-temperature cap.",
                    "3. Salt precursor at 1.180 ms; wall warm-start 278 C.",
                    "4. Race window [6.080, 6.460] ms opens on the autoclave bus.",
                    "5. rtd.wall.C 278 C at 6.120 ms (winner).",
                    "6. ft.salt.tph 16.0 t/h at 6.304 ms (loser by 184 us).",
                    "7. Gate at 6.880 ms (winner + 760 us): MODIFY clamp 16.0 -> 8.4 t/h.",
                    "8. Clamp executes; next-sample wall 252 C < 265 cap.",
                    "9. At 22.200 ms stored strain still blows 14 mm of lid gasket; AE burst.",
                    "10. Autoclave isolate 15 min (abort_s=900); named un-netted loss, not folded into process heads.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "cruise_salt_16"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("salt_tph", 16.0),
                        ("steam_tph", 4.8),
                        ("agitator_rpm", 42.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("wall_C", 278.0),
                        ("wall_cap_C", 265.0),
                        ("predicted_unclamped_next_C", 271.0),
                        ("salt_tph", 16.0),
                        ("race_margin_us", 184),
                        ("combined_jitter_us", 62),
                        ("abort_s", 900),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 16.0 t/h cruise: 278 C looks like a condensate-analyzer spike, not "
                "lid contact, and AH-6 volume is treated as still open.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "MODIFY"),
            ("correctness", "correct"),
            (
                "rationale",
                "Wall 278 C won by 184 us, so the lid is loading heat, not still cooling. "
                "Holding 16.0 t/h predicts next-sample 271 C > 265 cap. MODIFY: salt 16.0 -> "
                "8.4 t/h. Observed after clamp 252 C < 265. A full REJECT is not indicated: a "
                "sound AH-salt pass accepts 8.4 t/h.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "wall_C",
                            OrderedDict(
                                [
                                    ("cap", 265.0),
                                    ("observed", 278.0),
                                    ("predicted_unclamped_next", 271.0),
                                    ("clamped_salt_tph", 8.4),
                                    ("observed_after_clamp", 252.0),
                                ]
                            ),
                        ),
                        (
                            "salt_tph",
                            OrderedDict([("proposed", 16.0), ("clamped", 8.4)]),
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
            ("name", "clamped_salt_8p4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("salt_tph", 8.4),
                        ("steam_tph", 4.8),
                        ("agitator_rpm", 42.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "MODIFY: salt 16.0 -> 8.4 t/h. Process-correct vs the 265 C wall "
                "cap. Gasket blow still occurs at 22.200 ms.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Process-correct MODIFY held wall at 252 C. At 22.200 ms stored strain "
                "in the lid gasket still blew a 14 mm face. Clamp reduced dump energy; "
                "it did not prevent the split. Partnered negative: process heads stay honest; "
                "world loss is named, not netted.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("salt", "clamp executed; peak 252 C < 265"),
                        ("gasket", "14 mm blow at 22.200 ms"),
                        ("repair", "15 min autoclave isolate (abort_s=900)"),
                        ("mission", "SW-4 AH-salt pass incomplete this circuit"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Neither wall RTD nor salt FT predicted the gasket charge; ae.gasket.blow is a new channel at 22.200 ms, 15.320 ms after the gate, still inside the 44 ms raster.",
                    "Delayed (abort_s=900): 15 min autoclave isolate. Named un-netted loss, not folded into task_progress.",
                ],
            ),
            (
                "un_netted_loss",
                "15 min autoclave isolate after a 14 mm lid-gasket blow. Safety head -0.58 "
                "prices the split; task_progress stays +0.30 because the salt clamp completed "
                "under the 265 C cap. World loss is named here, not subtracted from process heads.",
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "rtd.wall.C (6.120 ms, 278 C)"),
                        ("loser", "ft.salt.tph (6.304 ms, 16.0 t/h)"),
                        ("margin_us", 184),
                        (
                            "counterfactual_if_reversed",
                            "Feed-first by < 184 us inside the 380 us window would have kept "
                            "16.0 t/h cruise; predicted next-sample 271 C would have exceeded "
                            "the 265 cap even without the gasket charge. The MODIFY is still the "
                            "correct process. The blow is a later world charge either way, "
                            "cheaper with the clamp than without.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 22200),
            (
                "reward_inflection_note",
                "Safety collapses at the 22.200 ms gasket blow (tick t_us=22200), inside "
                "the 44 ms raster. The correct MODIFY at 6.880 ms is in the same excerpt. Do "
                "not put inflection on the abort_s=900 isolate tick.",
            ),
            ("delayed_surprise_s", 900.0),
            ("abort_s", 900),
        ]
    )
    spikes = [
        spike("enc.salt.ctx", 1.180, 0.42),
        spike("rtd.wall.C", 2.340, 0.61),
        spike("ft.salt.tph", 3.620, 0.50),
        spike("rtd.wall.C", 6.120, 1.32),
        spike("ft.salt.tph", 6.304, 1.14),
        spike("ctrl.gate", 6.880, 0.98),
        spike("rtd.wall.C", 8.540, 0.80),
        spike("ft.salt.tph", 11.200, 0.62),
        spike("ctrl.gate", 15.600, 0.84),
        spike("ae.gasket.blow", 22.200, 1.46),
        spike("ae.gasket.blow", 24.100, 0.91),
        spike("enc.salt.ctx", 31.800, 0.41),
        spike("rtd.wall.C", 40.400, 0.53),
    ]
    ras = raster_core(
        44,
        78,
        26,
        89,
        routing(
            "thalamic-relay.wall-gasket",
            "spikenaut.policy.salt-clamp",
            [
                ("relay.rtd.wall", "policy.salt_clamp", 0.66),
                ("relay.ft.salt", "policy.salt_hold", 0.30),
                ("relay.ae.gasket", "policy.salt_clamp", -0.45),
            ],
            "noradrenaline",
            0.05,
            "surprise-gated pre_post_stdp; NA at wall win (6.120 ms) opens a 50 ms "
            "eligibility trace that still covers the 22.200 ms gasket blow",
        ),
        excerpt,
        extra=extra,
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.38),
            ("decision", "MODIFY"),
            (
                "populations",
                [
                    pop("salt_clamp", 42, 0.50, 250.0, 4),
                    pop("salt_hold", 42, 0.50, 62.5, 1),
                    pop("wall_veto", 22, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r84-436",
        "Spinelle-Wath SW-4 / AH-6: wall 278 C beats AH-salt feed by 184 us; correct "
        "MODIFY still eats an in-window lid-gasket blow (partnered negative total -0.45)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Partnered negative. Process-correct MODIFY; world still charges inside the "
        "44 ms raster. total -0.45 = 0.30 + -0.58 + -0.16 + 0.04 + -0.05. Named autoclave "
        "isolate (abort_s=900) is not netted into task_progress.",
        ras,
        gate,
        "nylon-66-salt-autoclave",
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
        "15 min autoclave isolate.",
        1,
    )


def record_437():
    ticks = [
        tick(1960, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(4620, -0.04, -0.02, -0.04, -0.02, 0.01),
        tick(4788, -0.03, -0.01, -0.03, -0.02, 0.01),
        tick(5280, -0.07, -0.05, -0.08, -0.05, 0.02),
        tick(7460, -0.02, -0.01, -0.02, -0.01, 0.01),
        tick(1260000000, -0.02, -0.01, -0.04, -0.01, 0.00),
    ]
    spikes = [
        spike("ft.meoh.ctx", 0.940, 0.40),
        spike("live.pt.eu", 1.960, 0.58),
        spike("span.stale.eu", 2.720, 0.51),
        spike("live.pt.eu", 4.620, 1.32),
        spike("span.stale.eu", 4.788, 1.15),
        spike("ctrl.gate", 5.280, 1.00),
        spike("live.pt.eu", 7.460, 0.74),
        spike("span.stale.eu", 8.620, 0.61),
        spike("ctrl.gate", 12.800, 0.82),
        spike("ft.meoh.ctx", 17.200, 0.42),
        spike("live.pt.eu", 22.400, 0.53),
        spike("span.stale.eu", 26.800, 0.47),
    ]
    excerpt = independent_excerpt(84387, 96, 30000, 14, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "SAPO-34 riser MTO-R2 on Gorse-Keld GK-3 is holding methanol at 18.0 t/h with live "
                "riser 1.68 bar against a 3.20 bar trip on a published 0-8.00 bar 4-20 mA span. A "
                "leftover 0-40.00 bar range card plus stale 8.50 bar setpoint from last campaign "
                "still sit on the faceplate. Live-span-first should ACCEPT the feed; a weak supervisor "
                "that binds the stale span will REJECT a legal riser.",
            ),
            ("domain", "methanol-to-olefins-riser"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Keep 18.0 t/h methanol on MTO-R2 while live riser stays <= 3.20 bar; "
                "do not spend a leftover 0-40 bar span card or an 8.50 bar stale setpoint on the hold.",
            ),
            ("t0_us", 1756850400000437),
            ("gate_latency_us", 660),
            ("race_window_us", 300),
            ("race_window_rel_ms", [4.56, 4.86]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "live.pt.eu 1.68 bar on 0-8.00 bar span",
                                "span.stale.eu 8.40 bar on leftover 0-40.00 bar card",
                            ],
                        ),
                        (
                            "semantics",
                            "Live-span-first should ACCEPT 18.0 t/h (1.68 bar < 3.20 bar trip). "
                            "Stale-span-first tempts a weak supervisor to treat 8.40 bar as live.",
                        ),
                        (
                            "window_derivation",
                            "300 us = one MTO-R2 PT sample minus leftover-span transmitter group delay "
                            "on this SAPO bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 168 us vs combined jitter ~58 us (live 26 + stale 32): 2.9x over "
                            "a 2.0x trust floor. Order is correctly live-span-first. The error is binding "
                            "the leftover range card, not the race.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "MTO-R2 riser PT, 4 kHz, 26 us jitter, span=0-8.00 bar LIVE",
                    "leftover range card, 4 kHz, 32 us jitter, span=0-40.00 bar STALE",
                    "methanol FT (context)",
                    "SAPO-34 bed dP (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("trip_bar", 3.20),
                        ("live_bar", 1.68),
                        ("live_span_bar", 8.00),
                        ("bound_span_bar", 40.00),
                        ("scaled_wrong_bar", 8.40),
                        ("stale_setpoint_bar", 8.50),
                        ("pv_ma", 7.36),
                        ("proposed_feed_tph", 18.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. MTO-R2 latched on Gorse-Keld GK-3; methanol 18.0 t/h armed.",
                    "2. Live 7.36 mA on 0-8.00 bar span = 1.68 bar; leftover 0-40.00 bar card scales 8.40 bar.",
                    "3. Methanol-FT precursor at 0.940 ms.",
                    "4. Race window [4.560, 4.860] ms.",
                    "5. live.pt.eu 1.68 bar at 4.620 ms (winner).",
                    "6. span.stale.eu 8.40 bar at 4.788 ms (loser by 168 us).",
                    "7. Gate at 5.280 ms: REJECT hold 0.0 t/h (incorrect).",
                    "8. Legal methanol cancelled; live 1.68 bar still < 3.20 bar trip.",
                    "9. Swapped-range bind remains; stale setpoint 8.50 bar unused as a live trip.",
                    "10. Delayed missed_window_s=1260 (21 min olefin-quality window) while R2 waits.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "feed_18"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 18.0),
                        ("hold", False),
                        ("bound_span_bar", 8.00),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("live_bar", 1.68),
                        ("trip_bar", 3.20),
                        ("live_span_bar", 8.00),
                        ("bound_span_bar", 8.00),
                        ("scaled_wrong_bar", 8.40),
                        ("stale_setpoint_bar", 8.50),
                        ("pv_ma", 7.36),
                        ("swapped_range", False),
                        ("stale_setpoint", False),
                        ("pv_live", True),
                        ("proposed_feed_tph", 18.0),
                        ("race_margin_us", 168),
                        ("combined_jitter_us", 58),
                        ("missed_window_s", 1260),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 18.0 t/h feed because live 7.36 mA on the published 0-8.00 bar "
                "span is 1.68 bar under the 3.20 bar trip; 8.40 bar is a leftover 0-40.00 bar card, "
                "not the live EU.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "incorrect"),
            (
                "rationale",
                "Leftover 0-40.00 bar span card scales 7.36 mA to 8.40 bar, over the 3.20 bar trip "
                "once the supervisor treats that card as live and corroborates against the stale "
                "8.50 bar setpoint. REJECT: hold methanol 0.0 t/h until the tag recovers under 3.20 "
                "so the riser does not see an over-pressure event.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "mto_bar",
                            OrderedDict(
                                [
                                    ("published_live_trip", 3.20),
                                    ("observed_live", 1.68),
                                    ("misbound_span_bar", 40.00),
                                    ("scaled_wrong_bar", 8.40),
                                    ("stale_setpoint_bar", 8.50),
                                    ("pv_ma", 7.36),
                                    ("swapped_range", True),
                                    ("stale_setpoint", True),
                                    ("executed_feed_tph", 0.0),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 168),
                                    ("combined_jitter_us", 58),
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
            ("name", "feed_hold_stale_span"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_tph", 0.0),
                        ("hold", True),
                        ("bound_span_bar", 40.00),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (incorrect): feed 18.0 -> 0.0 t/h. Routing relay.span.stale -> "
                "policy.hold_reject; no positive weight to policy.go_accept. Live 1.68 bar never "
                "violated the 3.20 bar trip.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Wrong-REJECT froze MTO-R2 at 0.0 t/h while live riser stayed 1.68 bar under the "
                "3.20 bar trip. 21 min olefin-quality window missed. Correct gate was ACCEPT of "
                "the already-legal 18.0 t/h feed.",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("feed", "held at 0.0 t/h; 18.0 t/h abandoned"),
                        ("live_bar", "still 1.68 bar, under 3.20 bar published trip"),
                        ("loop", "21 min olefin-quality window missed"),
                        ("span", "8.40 bar leftover 0-40 bar card false positive, not a live over-trip"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "The 8.40 bar reading is a leftover 0-40.00 bar range card scaling 7.36 mA, not a published live over-trip; the 8.50 bar figure is a stale setpoint from that campaign.",
                    "Delayed (missed_window_s=1260): sister MTO-R3 ran the same 18.0 t/h quality window after QA rebound the span map; R2's slot was already gone.",
                ],
            ),
            (
                "recovery",
                OrderedDict(
                    [
                        (
                            "correct_gate",
                            "ACCEPT: live 1.68 bar < published 3.20 bar trip; leave 18.0 t/h; bind 0-8.00 bar span.",
                        ),
                        ("correct_trip_bar", 3.20),
                        ("wrong_scaled_bar", 8.40),
                        ("bound_span_should_be_bar", 8.00),
                        (
                            "wrong_edit_applied",
                            OrderedDict(
                                [("feed_tph", 0.0), ("hold", True), ("bound_span_bar", 40.00)]
                            ),
                        ),
                        (
                            "cost",
                            "21 min missed olefin-quality window (task/efficiency); live riser never over trip (safety false-positive).",
                        ),
                    ]
                ),
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "live.pt.eu (4.620 ms, 1.68 bar on 0-8.00 bar span)"),
                        ("loser", "span.stale.eu (4.788 ms, 8.40 bar leftover 0-40.00 bar card)"),
                        ("margin_us", 168),
                        (
                            "counterfactual_if_reversed",
                            "Stale-span-first by < 168 us would still show live 1.68 bar < 3.20 bar. A "
                            "correct gate ACCEPTs either way. The wrong REJECT spent the live-span "
                            "win on a leftover range card plus a stale 8.50 bar setpoint.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5280),
            (
                "reward_inflection_note",
                "Task and efficiency drop at the wrong REJECT (5.280 ms, tick 4). The 21 min "
                "missed window is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 1260.0),
            ("missed_window_s", 1260),
        ]
    )
    ras = raster_core(
        30,
        96,
        30,
        86,
        routing(
            "relay.span.stale",
            "policy.hold_reject",
            [
                ("relay.span.stale", "policy.hold_reject", 0.74),
                ("relay.live.pt", "policy.hold_reject", 0.20),
            ],
            "acetylcholine",
            0.06,
            "swapped_range_stdp; ACh tags the (wrong) hold_reject bind at the leftover-span shadow",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("missed_window_s", 1260),
                ("delayed_surprise_s", 1260),
                ("swapped_range", True),
                ("stale_setpoint", True),
                ("live_bar", 1.68),
                ("bound_span_bar", 40.00),
                ("scaled_wrong_bar", 8.40),
            ]
        ),
    )
    gate = OrderedDict(
        [
            ("decision_window_ms", 0.30),
            ("decision", "REJECT"),
            (
                "populations",
                [
                    pop("hold_reject", 50, 0.50, 266.7, 4),
                    pop("go_accept", 50, 0.80, 6.7, 0),
                    pop("span_ctx", 30, 0.55, 111.1, 1),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r84-437",
        "WRONG-REJECT at Gorse-Keld GK-3 / MTO-R2: live 1.68 bar < 3.20 bar trip; "
        "supervisor bound leftover 0-40 bar span (8.40 bar) plus stale 8.50 bar setpoint",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Wrong-reject. Sidecar arithmetic 1.68 < 3.20 on live span is true; clamp bound "
        "to a 8.40 bar leftover 0-40 bar card. total -0.60 = -0.20 + -0.11 + -0.23 + -0.12 + 0.06.",
        ras,
        gate,
        "methanol-to-olefins-riser",
        [
            "reject",
            "wrong-gate",
            "swapped-range",
            "stale-setpoint",
            "sidecar-convictable",
            "designed",
        ],
        "Teaches a probe that a correct live<trip read can still be a wrong gate when "
        "routing.table[0].to is policy.hold_reject and executed feed is zeroed on a leftover span.",
        2,
        supervisor_error_type="wrong-reject",
    )


def record_438():
    ticks = [
        tick(2180, 0.01, 0.06, 0.01, 0.01, 0.01),
        tick(5320, 0.02, 0.08, 0.02, 0.02, 0.01),
        tick(5496, 0.02, 0.07, 0.02, 0.02, 0.01),
        tick(6180, 0.03, 0.12, 0.04, 0.03, 0.02),
        tick(8040, 0.01, 0.06, 0.02, 0.01, 0.01),
        tick(540000000, 0.01, 0.03, 0.01, 0.01, 0.00),
    ]
    spikes = [
        spike("ir.bed.ctx", 1.080, 0.43),
        spike("ae.tube.pps", 2.180, 0.62),
        spike("ir.bed.C", 3.640, 0.49),
        spike("ae.tube.pps", 5.320, 1.35),
        spike("ir.bed.C", 5.496, 1.12),
        spike("ctrl.gate", 6.180, 1.03),
        spike("ae.tube.pps", 8.040, 0.77),
        spike("ir.bed.ctx", 12.200, 0.44),
        spike("ir.bed.C", 16.400, 0.58),
        spike("ctrl.gate", 21.200, 0.81),
        spike("ae.tube.pps", 27.600, 0.50),
        spike("ir.bed.C", 33.000, 0.46),
        spike("ae.tube.ctx", 37.200, 0.40),
    ]
    excerpt = independent_excerpt(84388, 108, 38000, 15, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Oxidation-O3 on Propenoate-Dell PD-HIL is armed for an 8.4 kNm3/h propylene "
                "oxidation pass while tube-sheet AE sits at 48 pps against a 14 pps leak floor. A "
                "bed pyrometer, lit by the pad lamp spectrum, still reports 312 C under a 380 C "
                "hot-spot cap. AE-first holds air/C3; IR-first would commit 8.4 kNm3/h into a leaking pack.",
            ),
            ("domain", "acrylic-acid-oxidation"),
            ("sim_or_real", "hil"),
            (
                "goal",
                "Run O3 only if tube AE stays <= 14 pps; otherwise hold so a leaking Mo-V pack is "
                "not loaded at 8.4 kNm3/h.",
            ),
            ("t0_us", 1756850400000438),
            ("gate_latency_us", 860),
            ("race_window_us", 440),
            ("race_window_rel_ms", [5.28, 5.72]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "ae.tube.pps 48 pps tube leak",
                                "ir.bed.C 312 C pad-lamp glint",
                            ],
                        ),
                        (
                            "semantics",
                            "AE-first latches converter hold 8.4 -> 0 kNm3/h; IR-first would commit "
                            "8.4 kNm3/h on a still-legal 312 C hot-spot-cap story.",
                        ),
                        (
                            "window_derivation",
                            "440 us = one tube-AE slot versus bed-IR decode on this HIL oxidation bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 176 us vs combined jitter ~64 us (AE 30 + IR 34): 2.8x over "
                            "a 2.0x trust floor. Reversing order by < 176 us inside the 440 us "
                            "window would have committed 8.4 kNm3/h into a 48 pps tube leak.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "Mo-V tube-sheet AE puck, 5 kHz, 30 us jitter",
                    "bed IR camera, 200 Hz, 34 us jitter",
                    "air/C3 encoder (context)",
                    "steam drum PT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("ae_leak_floor_pps", 14.0),
                        ("observed_ae_pps", 48.0),
                        ("bed_cap_C", 380.0),
                        ("observed_bed_C", 312.0),
                        ("proposed_air_kNm3h", 8.4),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Oxidation-O3 indexed on Propenoate-Dell PD-HIL; air 8.4 kNm3/h armed.",
                    "2. Bed IR 312 C under 380 C cap; AE already 48 pps.",
                    "3. IR-context precursor at 1.080 ms.",
                    "4. Race window [5.280, 5.720] ms.",
                    "5. ae.tube.pps 48 pps at 5.320 ms (winner).",
                    "6. ir.bed.C 312 C at 5.496 ms (loser by 176 us).",
                    "7. Gate at 6.180 ms: REJECT hold converter 0 kNm3/h.",
                    "8. Pass cancelled; tube leak not loaded.",
                    "9. HIL pad lamp spectrum remains the bed glint source.",
                    "10. Delayed (abort_s=540): 9 min tube re-seat before the next pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "acrylic_8p4"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_kNm3h", 8.4),
                        ("hold", False),
                        ("train", "O3"),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("ae_pps", 48.0),
                        ("ae_leak_floor_pps", 14.0),
                        ("bed_C", 312.0),
                        ("bed_cap_C", 380.0),
                        ("race_margin_us", 176),
                        ("combined_jitter_us", 64),
                        ("abort_s", 540),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 8.4 kNm3/h because bed 312 C is under the 380 C "
                "cap and treats the AE puck as steam-drum noise.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "REJECT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Tube AE 48 pps won by 176 us, so the pack is leaking, not still quiet. "
                "48 pps > 14 pps floor. REJECT: hold air 8.4 -> 0 kNm3/h. Bed 312 C < 380 C "
                "does not license the pass once AE is over floor.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "tube_ae_pps",
                            OrderedDict(
                                [
                                    ("floor", 14.0),
                                    ("observed", 48.0),
                                    ("executed_air_kNm3h", 0.0),
                                ]
                            ),
                        ),
                        (
                            "bed_C",
                            OrderedDict(
                                [
                                    ("cap", 380.0),
                                    ("observed", 312.0),
                                    ("does_not_license_pass", True),
                                ]
                            ),
                        ),
                        (
                            "order_evidence",
                            OrderedDict(
                                [
                                    ("margin_us", 176),
                                    ("combined_jitter_us", 64),
                                    ("ratio", 2.75),
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
            ("name", "tube_hold"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("air_kNm3h", 0.0),
                        ("hold", True),
                        ("train", "O3"),
                    ]
                ),
            ),
            (
                "gate_effect",
                "REJECT (correct): air 8.4 -> 0 kNm3/h. Routing relay.ae.tube -> "
                "policy.tube_hold. Tube leak is not loaded.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct REJECT held O3 at 0 kNm3/h. AE 48 pps beat bed 312 C; pack "
                "was already over the 14 pps leak floor. 9 min re-seat follows (abort_s=540).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("converter", "held at 0 kNm3/h; 8.4 kNm3/h abandoned"),
                        ("pack", "48 pps leak not loaded"),
                        ("bed", "312 C still under 380 C cap"),
                        ("reseat", "9 min tube re-seat queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Bed IR 312 C was a HIL pad-lamp glint, not a hot-spot-cap exceedance.",
                    "Delayed (abort_s=540): 9 min tube re-seat before the next pass on PD-HIL.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "ae.tube.pps (5.320 ms, 48 pps)"),
                        ("loser", "ir.bed.C (5.496 ms, 312 C)"),
                        ("margin_us", 176),
                        (
                            "counterfactual_if_reversed",
                            "IR-first by < 176 us would have committed 8.4 kNm3/h into a pack "
                            "already at 48 pps. The REJECT is still the correct process; AE is the "
                            "licensing channel, not bed IR.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 6180),
            (
                "reward_inflection_note",
                "Safety and task credit the correct REJECT at 6.180 ms (tick 4). The 9 min "
                "re-seat is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 540.0),
            ("abort_s", 540),
        ]
    )
    ras = raster_core(
        38,
        108,
        24,
        98,
        routing(
            "thalamic-relay.tube-ae",
            "spikenaut.policy.tube-hold",
            [
                ("relay.ae.tube", "policy.tube_hold", 0.68),
                ("relay.ir.bed", "policy.tube_commit", 0.28),
                ("relay.ae.tube", "policy.tube_hold", 0.12),
            ],
            "dopamine",
            0.07,
            "ae_floor_stdp; DA at tube win (5.320 ms) opens a 70 ms eligibility trace",
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
                    pop("tube_hold", 54, 0.50, 210.0, 5),
                    pop("tube_commit", 54, 0.50, 42.1, 1),
                    pop("ae_veto", 30, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r84-438",
        "Propenoate-Dell PD-HIL / Oxidation-O3: tube AE 48 pps beats bed 312 C; correct "
        "REJECT holds the acrylic-acid oxidation pass",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct REJECT. AE 48 pps > 14 pps floor beats a legal bed IR. "
        "total +0.80 = 0.10 + 0.42 + 0.12 + 0.10 + 0.06.",
        ras,
        gate,
        "acrylic-acid-oxidation",
        ["reject", "hil", "tube-ae", "acrylic", "correct-gate"],
        "Teaches a tube-AE vs pad-lamp-glint race on a HIL acrylic oxidizer: the leak floor, "
        "not the bed cap, licenses the pass.",
        3,
    )


def record_439():
    ticks = [
        tick(1680, 0.06, 0.04, 0.02, 0.01, 0.01),
        tick(4140, 0.08, 0.06, 0.04, 0.03, 0.02),
        tick(4284, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(4720, 0.12, 0.09, 0.05, 0.03, 0.02),
        tick(6580, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(300000000, 0.03, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("enc.c5.ctx", 0.820, 0.41),
        spike("pt.h2.bar", 1.680, 0.58),
        spike("ir.heater.C", 2.840, 0.47),
        spike("pt.h2.bar", 4.140, 1.28),
        spike("ir.heater.C", 4.284, 1.10),
        spike("ctrl.gate", 4.720, 0.97),
        spike("pt.h2.bar", 6.580, 0.72),
        spike("enc.c5.ctx", 10.400, 0.44),
        spike("ir.heater.C", 14.600, 0.55),
        spike("ctrl.gate", 18.800, 0.80),
        spike("pt.h2.bar", 22.200, 0.49),
        spike("enc.c5.ctx", 23.600, 0.38),
    ]
    excerpt = independent_excerpt(84389, 60, 24000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Penex-P1 of Isomer-Spurn IS-7 is already at 2.12 bar recycle hydrogen while a "
                "heater-tube IR smear still reports as 3.88 bar against a 3.60 bar trip the live PT "
                "has not crossed. Hydrogen-first should ACCEPT 14.0 t/h C5; glint-first would "
                "invent a hold on an already-legal isomerization pass.",
            ),
            ("domain", "pentane-isomerization-penex"),
            ("sim_or_real", "simulated"),
            (
                "goal",
                "Run P1 at 14.0 t/h while recycle H2 stays <= 3.60 bar; do not spend a heater-tube "
                "IR smear on the Penex hold.",
            ),
            ("t0_us", 1756850400000439),
            ("gate_latency_us", 580),
            ("race_window_us", 320),
            ("race_window_rel_ms", [4.10, 4.42]),
            (
                "race",
                OrderedDict(
                    [
                        (
                            "contenders",
                            [
                                "pt.h2.bar 2.12 bar live",
                                "ir.heater.C smear as 3.88 bar",
                            ],
                        ),
                        (
                            "semantics",
                            "Hydrogen-first should ACCEPT 14.0 t/h (2.12 bar < 3.60 bar trip). "
                            "Glint-first would hold on a simulated heater smear.",
                        ),
                        (
                            "window_derivation",
                            "320 us = one recycle-H2 PT sample versus heater-IR decode on this "
                            "Penex bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 144 us vs combined jitter ~50 us (PT 22 + IR 28): 2.9x over "
                            "a 2.0x trust floor. Reversing order by < 144 us inside the 320 us "
                            "window would have invented a hold on an already-legal 2.12 bar recycle.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "recycle H2 PT, 4 kHz, 22 us jitter",
                    "heater IR camera, 200 Hz, 28 us jitter",
                    "C5 FT (context)",
                    "chloride analyzer (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("h2_trip_bar", 3.60),
                        ("observed_h2_bar", 2.12),
                        ("heater_shadow_bar", 3.88),
                        ("proposed_c5_tph", 14.0),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Penex-P1 indexed on Isomer-Spurn IS-7; C5 14.0 t/h armed.",
                    "2. Recycle H2 2.12 bar; heater-IR smear as 3.88 bar over 3.60 bar trip.",
                    "3. C5-encoder precursor at 0.820 ms.",
                    "4. Race window [4.100, 4.420] ms.",
                    "5. pt.h2.bar 2.12 bar at 4.140 ms (winner).",
                    "6. ir.heater.C smear at 4.284 ms (loser by 144 us).",
                    "7. Gate at 4.720 ms: ACCEPT leave 14.0 t/h.",
                    "8. H2 remains 2.12 bar < 3.60 bar; glint unused as a hold.",
                    "9. Simulated heater scale remains the IR source.",
                    "10. Delayed (survey_hold_s=300): 5 min RON survey after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "c5_14"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("c5_tph", 14.0),
                        ("hold", False),
                        ("heater_C", 148.0),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("h2_bar", 2.12),
                        ("h2_trip_bar", 3.60),
                        ("heater_shadow_bar", 3.88),
                        ("proposed_c5_tph", 14.0),
                        ("race_margin_us", 144),
                        ("combined_jitter_us", 50),
                        ("survey_hold_s", 300),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 14.0 t/h because recycle H2 2.12 bar is under the 3.60 bar trip; "
                "3.88 bar is a heater-tube IR smear, not a recycle pressure.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Recycle H2 2.12 bar won by 144 us and sits under the 3.60 bar trip. Heater smear "
                "3.88 bar is a simulated tube scale, not a recycle reading. ACCEPT: leave 14.0 t/h. "
                "A hold would idle a legal Penex pass.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "h2_bar",
                            OrderedDict(
                                [
                                    ("trip", 3.60),
                                    ("observed", 2.12),
                                    ("executed_c5_tph", 14.0),
                                ]
                            ),
                        ),
                        (
                            "heater_shadow_bar",
                            OrderedDict(
                                [
                                    ("observed", 3.88),
                                    ("not_a_recycle_reading", True),
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
            ("name", "c5_14"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("c5_tph", 14.0),
                        ("hold", False),
                        ("heater_C", 148.0),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 14.0 t/h. Routing relay.pt.h2 -> policy.penex_go. "
                "Heater-IR unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left P1 at 14.0 t/h. Recycle H2 2.12 bar beat heater smear 3.88 bar; "
                "the 3.60 bar trip was never crossed. 5 min RON survey follows "
                "(survey_hold_s=300).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("c5", "14.0 t/h held as proposed"),
                        ("h2", "2.12 bar < 3.60 bar trip"),
                        ("glint", "3.88 bar smear unused"),
                        ("survey", "5 min RON survey queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "IR 3.88 bar was a simulated heater-tube smear, not a recycle over-trip.",
                    "Delayed (survey_hold_s=300): 5 min RON survey after the pass on IS-7.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "pt.h2.bar (4.140 ms, 2.12 bar)"),
                        ("loser", "ir.heater.C (4.284 ms, smear 3.88 bar)"),
                        ("margin_us", 144),
                        (
                            "counterfactual_if_reversed",
                            "Glint-first by < 144 us would still be a heater smear over the "
                            "3.60 bar trip; a correct gate ACCEPTs either way. Reversing would only "
                            "have delayed confirmation of the same legal recycle.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 4720),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 4.720 ms (tick 4). The 5 min "
                "survey is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 300.0),
            ("survey_hold_s", 300),
        ]
    )
    ras = raster_core(
        24,
        60,
        38,
        55,
        routing(
            "thalamic-relay.h2-pt",
            "spikenaut.policy.penex-go",
            [
                ("relay.pt.h2", "policy.penex_go", 0.70),
                ("relay.ir.heater", "policy.glint_hold", 0.22),
                ("relay.pt.h2", "policy.penex_go", 0.10),
            ],
            "serotonin",
            0.04,
            "already_legal_stdp; 5-HT at hydrogen win (4.140 ms) tags the go bind",
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
                    pop("penex_go", 38, 0.50, 246.7, 3),
                    pop("glint_hold", 38, 0.80, 8.2, 0),
                    pop("pt_veto", 22, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r84-439",
        "Isomer-Spurn IS-7 / Penex-P1: recycle H2 2.12 bar beats heater smear; correct ACCEPT "
        "of an already-legal 14.0 t/h (total +1.10)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Recycle H2 2.12 bar < 3.60 bar trip; heater smear unused. "
        "total +1.10 = 0.42 + 0.30 + 0.18 + 0.12 + 0.08.",
        ras,
        gate,
        "pentane-isomerization-penex",
        ["accept", "simulated-smear", "h2-vs-glint", "penex", "simulated"],
        "Teaches that a heater-tube IR smear can lose to a legal recycle-H2 PT inside a "
        "320 us window; reversing 144 us would have invented a hold on an already-legal Penex.",
        4,
    )


def record_440():
    ticks = [
        tick(1760, 0.06, 0.04, 0.03, 0.01, 0.01),
        tick(4860, 0.09, 0.06, 0.04, 0.03, 0.02),
        tick(5028, 0.07, 0.05, 0.03, 0.02, 0.01),
        tick(5520, 0.12, 0.09, 0.06, 0.03, 0.02),
        tick(7740, 0.06, 0.04, 0.03, 0.02, 0.01),
        tick(480000000, 0.04, 0.02, 0.01, 0.01, 0.01),
    ]
    spikes = [
        spike("ft.kf.ctx", 0.960, 0.42),
        spike("cell.v", 1.760, 0.59),
        spike("hf.offgas.ppm", 3.140, 0.48),
        spike("cell.v", 4.860, 1.30),
        spike("hf.offgas.ppm", 5.028, 1.11),
        spike("ctrl.gate", 5.520, 0.99),
        spike("cell.v", 7.740, 0.74),
        spike("hf.offgas.ppm", 11.400, 0.56),
        spike("ctrl.gate", 15.200, 0.82),
        spike("ft.kf.ctx", 17.800, 0.43),
        spike("cell.v", 20.600, 0.51),
    ]
    excerpt = independent_excerpt(84390, 48, 22000, 12, spike_avoid_us(spikes))
    state = OrderedDict(
        [
            (
                "description",
                "Cell-C8 at Cryolite-Force CF-2 is fluorinating at 6.2 t/d with cell 8.6 V "
                "against a 10.4 V anode-effect cap. Offgas HF smear sits at 28 ppm under a 70 ppm "
                "stack floor. Voltage-first should ACCEPT the 6.2 t/d already-legal set; HF-first "
                "would only delay confirmation of the same legal KF-2HF melt.",
            ),
            ("domain", "fluorine-kf2hf-cell"),
            ("sim_or_real", "designed"),
            (
                "goal",
                "Hold 6.2 t/d on C8 while cell stays <= 10.4 V and stack HF stays <= 70 ppm.",
            ),
            ("t0_us", 1756850400000440),
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
                                "cell.v 8.6 V melt",
                                "hf.offgas.ppm 28 ppm smear",
                            ],
                        ),
                        (
                            "semantics",
                            "Voltage-first should ACCEPT 6.2 t/d (8.6 V < 10.4 V cap). "
                            "HF-first would only delay confirmation of the same legal melt.",
                        ),
                        (
                            "window_derivation",
                            "360 us = one cell-voltage slot versus HF-analyzer group delay on this "
                            "KF-2HF bus.",
                        ),
                        (
                            "order_evidence_note",
                            "Margin 168 us vs combined jitter ~56 us (cell 24 + HF 32): 3.0x over "
                            "a 2.0x trust floor. Reversing order by < 168 us inside the 360 us "
                            "window would still show both channels under cap; ACCEPT either way.",
                        ),
                    ]
                ),
            ),
            (
                "sensors",
                [
                    "cell voltmeter, 2 kHz, 24 us jitter",
                    "stack HF analyzer, 1 kHz, 32 us jitter",
                    "cell PT (context)",
                    "KF-feed FT (context)",
                ],
            ),
            (
                "constraints",
                OrderedDict(
                    [
                        ("cell_cap_V", 10.4),
                        ("observed_cell_V", 8.6),
                        ("hf_floor_ppm", 70.0),
                        ("observed_hf_ppm", 28.0),
                        ("proposed_td", 6.2),
                    ]
                ),
            ),
            (
                "episode_steps",
                [
                    "1. Cell-C8 indexed on Cryolite-Force CF-2; KF-2HF 6.2 t/d armed.",
                    "2. Cell 8.6 V; stack HF 28 ppm under 70 ppm floor.",
                    "3. KF-FT precursor at 0.960 ms.",
                    "4. Race window [4.820, 5.180] ms.",
                    "5. cell.v 8.6 V at 4.860 ms (winner).",
                    "6. hf.offgas.ppm 28 ppm at 5.028 ms (loser by 168 us).",
                    "7. Gate at 5.520 ms: ACCEPT leave 6.2 t/d.",
                    "8. Cell remains 8.6 V < 10.4 V; HF unused as a hold.",
                    "9. Fluorine sendout continues.",
                    "10. Delayed (dwell_s=480): 8 min anode-effect survey dwell after the pass.",
                ],
            ),
        ]
    )
    proposed = OrderedDict(
        [
            ("name", "fluor_6p2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_td", 6.2),
                        ("hold", False),
                        ("current_kA", 12.4),
                    ]
                ),
            ),
            (
                "evidence",
                OrderedDict(
                    [
                        ("cell_V", 8.6),
                        ("cell_cap_V", 10.4),
                        ("hf_ppm", 28.0),
                        ("hf_floor_ppm", 70.0),
                        ("proposed_td", 6.2),
                        ("race_margin_us", 168),
                        ("combined_jitter_us", 56),
                        ("dwell_s", 480),
                    ]
                ),
            ),
            (
                "basis",
                "Planner proposes 6.2 t/d because cell 8.6 V is under the 10.4 V cap "
                "and stack HF 28 ppm is under the 70 ppm floor.",
            ),
        ]
    )
    safety = OrderedDict(
        [
            ("decision", "ACCEPT"),
            ("correctness", "correct"),
            (
                "rationale",
                "Cell 8.6 V won by 168 us and sits under the 10.4 V cap. Stack HF 28 ppm "
                "is under 70 ppm. ACCEPT: leave 6.2 t/d. A hold would idle a legal KF-2HF cell.",
            ),
            (
                "constraint_checked",
                OrderedDict(
                    [
                        (
                            "cell_V",
                            OrderedDict(
                                [
                                    ("cap", 10.4),
                                    ("observed", 8.6),
                                    ("executed_td", 6.2),
                                ]
                            ),
                        ),
                        (
                            "hf_ppm",
                            OrderedDict(
                                [
                                    ("floor", 70.0),
                                    ("observed", 28.0),
                                    ("under_floor", True),
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
            ("name", "fluor_6p2"),
            (
                "parameters",
                OrderedDict(
                    [
                        ("feed_td", 6.2),
                        ("hold", False),
                        ("current_kA", 12.4),
                    ]
                ),
            ),
            (
                "gate_effect",
                "ACCEPT: leave 6.2 t/d. Routing relay.cell.v -> policy.cell_go. "
                "HF unused as a hold.",
            ),
        ]
    )
    future = OrderedDict(
        [
            (
                "summary",
                "Correct ACCEPT left C8 at 6.2 t/d. Cell 8.6 V beat HF 28 ppm; both "
                "caps held. 8 min anode-effect survey dwell follows (dwell_s=480).",
            ),
            (
                "state_delta",
                OrderedDict(
                    [
                        ("melt", "6.2 t/d held as proposed"),
                        ("cell", "8.6 V < 10.4 V cap"),
                        ("hf", "28 ppm < 70 ppm floor"),
                        ("survey", "8 min anode-effect survey dwell queued"),
                    ]
                ),
            ),
            (
                "surprises",
                [
                    "Stack HF 28 ppm was never a trip; it only lost the race to a legal cell voltmeter.",
                    "Delayed (dwell_s=480): 8 min anode-effect survey dwell after the pass on CF-2.",
                ],
            ),
            (
                "race_result",
                OrderedDict(
                    [
                        ("winner", "cell.v (4.860 ms, 8.6 V)"),
                        ("loser", "hf.offgas.ppm (5.028 ms, 28 ppm)"),
                        ("margin_us", 168),
                        (
                            "counterfactual_if_reversed",
                            "HF-first by < 168 us would still be under 70 ppm; a correct gate "
                            "ACCEPTs either way. Reversing would only have delayed confirmation of "
                            "the same legal melt.",
                        ),
                    ]
                ),
            ),
            ("reward_inflection_t_us", 5520),
            (
                "reward_inflection_note",
                "Task and safety credit the correct ACCEPT at 5.520 ms (tick 4). The 8 min "
                "dwell is delayed surprise, not the inflection.",
            ),
            ("delayed_surprise_s", 480.0),
            ("dwell_s", 480),
        ]
    )
    ras = raster_core(
        22,
        48,
        40,
        42,
        routing(
            "thalamic-relay.cell-v",
            "spikenaut.policy.cell-go",
            [
                ("relay.cell.v", "policy.cell_go", 0.69),
                ("relay.hf.offgas", "policy.hf_hold", 0.24),
                ("relay.cell.v", "policy.cell_go", 0.11),
            ],
            "adenosine",
            0.08,
            "already_legal_stdp; adenosine at cell win (4.860 ms) tags the go bind",
        ),
        excerpt,
        extra=OrderedDict(
            [
                ("excerpt_source", "kernelized_events"),
                ("sim_scope", "none"),
                ("dwell_s", 480),
                ("delayed_surprise_s", 480),
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
                    pop("cell_go", 34, 0.50, 245.1, 3),
                    pop("hf_hold", 34, 0.80, 8.2, 0),
                    pop("cell_veto", 18, 0.75),
                ],
            ),
        ]
    )
    return wrap_record(
        "ttf-r84-440",
        "Cryolite-Force CF-2 / Cell-C8: 8.6 V beats stack HF 28 ppm; correct ACCEPT "
        "of an already-legal 6.2 t/d (total +1.14)",
        state,
        spikes,
        proposed,
        safety,
        executed,
        future,
        ticks,
        "Correct ACCEPT. Cell 8.6 V < 10.4 V cap; HF unused. "
        "total +1.14 = 0.44 + 0.30 + 0.20 + 0.12 + 0.08.",
        ras,
        gate,
        "fluorine-kf2hf-cell",
        ["accept", "designed", "cell-vs-hf", "already-legal", "kf2hf"],
        "Teaches an already-legal KF-2HF cell: both voltage and stack HF sit under cap; "
        "race order only confirms the ACCEPT.",
        5,
    )

